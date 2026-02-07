import os
import re
import time
import requests
import aiofiles
import aiohttp
import asyncio
import cloudscraper
from pyrogram import Client
from pyrogram.types import Message
from pyrogram.errors import FloodWait
import itsgolu as helper
from vars import CREDIT, OWNER_ID, api_url, api_token, cwtoken, cptoken

async def process_links(
    client: Client,
    message: Message,
    links: list,
    start_index: int,
    batch_name: str,
    resolution: str, # raw_text2 (e.g. "480")
    watermark: str,
    credit: str, # raw_text3 or calculated CR
    token: str, # raw_text4 (PW Token)
    thumbnail: str,
    channel_id: int
):
    failed_count = 0
    success_count = 0

    count = start_index
    path = f"./downloads/{message.chat.id}"
    os.makedirs(path, exist_ok=True)

    # Resolution mapping
    quality = f"{resolution}p"

    # Pre-calculate CR if passed raw (handled by caller better, but for safety):
    if "," in credit:
        CR, PRENAME = credit.split(",")
    else:
        CR = credit
        PRENAME = ""

    for i in range(start_index - 1, len(links)):
        # Extract name and url
        raw_name = links[i][0]
        raw_url = links[i][1]

        # Cleanup URL
        Vxy = raw_url.replace("file/d/","uc?export=download&id=").replace("www.youtube-nocookie.com/embed", "youtu.be").replace("?modestbranding=1", "").replace("/view?usp=sharing","")
        url = "https://" + Vxy
        link0 = "https://" + Vxy

        # Cleanup Name
        name1 = raw_name.replace("(", "[").replace(")", "]").replace("_", "").replace("\t", "").replace(":", "").replace("/", "").replace("+", "").replace("#", "").replace("|", "").replace("@", "").replace("*", "").replace(".", "").replace("https", "").replace("http", "").strip()
        if PRENAME:
             name = f'{PRENAME} {name1[:60]}'
        else:
             name = f'{name1[:60]}'

        # Define Captions
        cc = (
            f"<b>🏷️ Iɴᴅᴇx ID  :</b> {str(count).zfill(3)}\n\n"
            f"<b>🎞️  Tɪᴛʟᴇ :</b> {name1} \n\n"
            f"<blockquote>📚  𝗕ᴀᴛᴄʜ : {batch_name}</blockquote>"
            f"\n\n<b>🎓  Uᴘʟᴏᴀᴅ Bʏ : {CR}</b>"
        )
        cc1 = (
            f"<b>🏷️ Iɴᴅᴇx ID :</b> {str(count).zfill(3)}\n\n"
            f"<b>📑  Tɪᴛʟᴇ :</b> {name1} \n\n"
            f"<blockquote>📚  𝗕ᴀᴛᴄʜ : {batch_name}</blockquote>"
            f"\n\n<b>🎓  Uᴘʟᴏᴀᴅ Bʏ : {CR}</b>"
        )
        cczip = f'[📁]Zip Id : {str(count).zfill(3)}\n**Zip Title :** `{name1} .zip`\n<blockquote><b>Batch Name :</b> {batch_name}</blockquote>\n\n**Extracted by➤**{CR}\n'
        ccimg = (
            f"<b>🏷️ Iɴᴅᴇx ID <b>: {str(count).zfill(3)} \n\n"
            f"<b>🖼️  Tɪᴛʟᴇ</b> : {name1} \n\n"
            f"<blockquote>📚  𝗕ᴀᴛᴄʜ : {batch_name}</blockquote>"
            f"\n\n<b>🎓  Uᴘʟᴏᴀᴅ Bʏ : {CR}</b>"
        )
        cchtml = f'[🌐]Html Id : {str(count).zfill(3)}\n**Html Title :** `{name1} .html`\n<blockquote><b>Batch Name :</b> {batch_name}</blockquote>\n\n**Extracted by➤**{CR}\n'

        # Google Docs Handling (Try Export)
        if "docs.google.com/document/d/" in url:
             try:
                 doc_id = url.split("document/d/")[1].split("/")[0]
                 export_url = f"https://docs.google.com/document/d/{doc_id}/export?format=pdf"
                 async with aiohttp.ClientSession() as session:
                    async with session.get(export_url) as resp:
                        if resp.status == 200:
                            f = await aiofiles.open(f"{name}.pdf", mode='wb')
                            await f.write(await resp.read())
                            await f.close()
                            await client.send_document(chat_id=channel_id, document=f"{name}.pdf", caption=cc1)
                            os.remove(f"{name}.pdf")
                            count += 1
                            success_count += 1
                            continue
             except Exception:
                 pass # Fallback to manual note

        # Google Drive / Docs Handling (Manual Note Fallback)
        if "drive.google.com" in url or "docs.google.com" in url:
            try:
                # Guess file type from context or just generic
                type_guess = "file"
                if "Assignment" in name1: type_guess = "Assignment"
                elif "Notes" in name1: type_guess = "Notes"
                elif "pdf" in name1.lower(): type_guess = "PDF"

                msg_text = (
                    f"<b>{name1}</b>\n"
                    f"🔗 Link: {url}\n\n"
                    f"<i>Note: Click the link to download {type_guess}</i>"
                )
                await client.send_message(channel_id, msg_text)
                count += 1
                success_count += 1
                continue
            except Exception as e:
                # Fallback to error reporting if even sending message fails
                pass

        try:
            # === URL Processing Logic ===
            user_id = message.from_user.id
            cmd = ""
            mpd = None
            keys_string = ""

            if "visionias" in url:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers={'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9', 'Accept-Language': 'en-US,en;q=0.9', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'Pragma': 'no-cache', 'Referer': 'http://www.visionias.in/', 'Sec-Fetch-Dest': 'iframe', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'cross-site', 'Upgrade-Insecure-Requests': '1', 'User-Agent': 'Mozilla/5.0 (Linux; Android 12; RMX2121) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36', 'sec-ch-ua': '"Chromium";v="107", "Not=A?Brand";v="24"', 'sec-ch-ua-mobile': '?1', 'sec-ch-ua-platform': '"Android"',}) as resp:
                        text = await resp.text()
                        url = re.search(r"(https://.*?playlist.m3u8.*?)\"", text).group(1)

            if "acecwply" in url:
                cmd = f'yt-dlp -o "{name}.%(ext)s" -f "bestvideo[height<={resolution}]+bestaudio" --hls-prefer-ffmpeg --no-keep-video --remux-video mkv --no-warning "{url}"'

            elif "https://static-trans-v1.classx.co.in" in url or "https://static-trans-v2.classx.co.in" in url:
                base_with_params, signature = url.split("*")
                base_clean = base_with_params.split(".mkv")[0] + ".mkv"
                if "static-trans-v1.classx.co.in" in url:
                    base_clean = base_clean.replace("https://static-trans-v1.classx.co.in", "https://appx-transcoded-videos-mcdn.akamai.net.in")
                elif "static-trans-v2.classx.co.in" in url:
                    base_clean = base_clean.replace("https://static-trans-v2.classx.co.in", "https://transcoded-videos-v2.classx.co.in")
                url = f"{base_clean}*{signature}"

            elif "https://static-rec.classx.co.in/drm/" in url:
                base_with_params, signature = url.split("*")
                base_clean = base_with_params.split("?")[0]
                base_clean = base_clean.replace("https://static-rec.classx.co.in", "https://appx-recordings-mcdn.akamai.net.in")
                url = f"{base_clean}*{signature}"

            elif "https://static-wsb.classx.co.in/" in url:
                clean_url = url.split("?")[0]
                clean_url = clean_url.replace("https://static-wsb.classx.co.in", "https://appx-wsb-gcp-mcdn.akamai.net.in")
                url = clean_url

            elif "https://static-db.classx.co.in/" in url:
                if "*" in url:
                    base_url, key = url.split("*", 1)
                    base_url = base_url.split("?")[0]
                    base_url = base_url.replace("https://static-db.classx.co.in", "https://appxcontent.kaxa.in")
                    url = f"{base_url}*{key}"
                else:
                    base_url = url.split("?")[0]
                    url = base_url.replace("https://static-db.classx.co.in", "https://appxcontent.kaxa.in")

            elif "https://static-db-v2.classx.co.in/" in url:
                if "*" in url:
                    base_url, key = url.split("*", 1)
                    base_url = base_url.split("?")[0]
                    base_url = base_url.replace("https://static-db-v2.classx.co.in", "https://appx-content-v2.classx.co.in")
                    url = f"{base_url}*{key}"
                else:
                    base_url = url.split("?")[0]
                    url = base_url.replace("https://static-db-v2.classx.co.in", "https://appx-content-v2.classx.co.in")

            elif any(x in url for x in ["https://cpvod.testbook.com/", "classplusapp.com/drm/", "media-cdn.classplusapp.com", "media-cdn-alisg.classplusapp.com", "media-cdn-a.classplusapp.com", "tencdn.classplusapp", "videos.classplusapp", "webvideos.classplusapp.com"]):
                url_norm = url.replace("https://cpvod.testbook.com/", "https://media-cdn.classplusapp.com/drm/")
                api_url_call = f"https://itsgolu-cp-api.vercel.app/itsgolu?url={url_norm}@ITSGOLU_OFFICIAL&user_id={user_id}"
                keys_string = ""
                mpd = None
                try:
                    resp = requests.get(api_url_call, timeout=30)
                    try:
                        data = resp.json()
                    except Exception:
                        data = None

                    if isinstance(data, dict) and "KEYS" in data and "MPD" in data:
                        mpd = data.get("MPD")
                        keys = data.get("KEYS", [])
                        url = mpd
                        keys_string = " ".join([f"--key {k}" for k in keys])
                    elif isinstance(data, dict) and "url" in data:
                        url = data.get("url")
                        keys_string = ""
                    else:
                        try:
                            res = helper.get_mps_and_keys2(url_norm)
                            if res:
                                mpd, keys = res
                                url = mpd
                                keys_string = " ".join([f"--key {k}" for k in keys])
                            else:
                                keys_string = ""
                        except Exception:
                            keys_string = ""
                except Exception:
                    try:
                        res = helper.get_mps_and_keys2(url_norm)
                        if res:
                            mpd, keys = res
                            url = mpd
                            keys_string = " ".join([f"--key {k}" for k in keys])
                        else:
                            keys_string = ""
                    except Exception:
                        keys_string = ""

            elif "tencdn.classplusapp" in url:
                headers = {'host': 'api.classplusapp.com', 'x-access-token': f'{token}', 'accept-language': 'EN', 'api-version': '18', 'app-version': '1.4.73.2', 'build-number': '35', 'connection': 'Keep-Alive', 'content-type': 'application/json', 'device-details': 'Xiaomi_Redmi 7_SDK-32', 'device-id': 'c28d3cb16bbdac01', 'region': 'IN', 'user-agent': 'Mobile-Android', 'webengage-luid': '00000187-6fe4-5d41-a530-26186858be4c', 'accept-encoding': 'gzip'}
                params = {"url": f"{url}"}
                response = requests.get('https://api.classplusapp.com/cams/uploader/video/jw-signed-url', headers=headers, params=params)
                url = response.json()['url']

            elif 'videos.classplusapp' in url:
                url = requests.get(f'https://api.classplusapp.com/cams/uploader/video/jw-signed-url?url={url}', headers={'x-access-token': f'{cptoken}'}).json()['url']

            elif 'media-cdn.classplusapp.com' in url or 'media-cdn-alisg.classplusapp.com' in url or 'media-cdn-a.classplusapp.com' in url:
                headers = {'host': 'api.classplusapp.com', 'x-access-token': f'{cptoken}', 'accept-language': 'EN', 'api-version': '18', 'app-version': '1.4.73.2', 'build-number': '35', 'connection': 'Keep-Alive', 'content-type': 'application/json', 'device-details': 'Xiaomi_Redmi 7_SDK-32', 'device-id': 'c28d3cb16bbdac01', 'region': 'IN', 'user-agent': 'Mobile-Android', 'webengage-luid': '00000187-6fe4-5d41-a530-26186858be4c', 'accept-encoding': 'gzip'}
                params = {"url": f"{url}"}
                response = requests.get('https://api.classplusapp.com/cams/uploader/video/jw-signed-url', headers=headers, params=params)
                url   = response.json()['url']

            elif "childId" in url and "parentId" in url:
                url = f"https://anonymouspwplayer-0e5a3f512dec.herokuapp.com/pw?url={url}&token={token}"

            if "edge.api.brightcove.com" in url:
                bcov = f'bcov_auth={cwtoken}'
                url = url.split("bcov_auth")[0]+bcov

            elif "d1d34p8vz63oiq" in url or "sec1.pw.live" in url:
                url = f"https://anonymouspwplayer-b99f57957198.herokuapp.com/pw?url={url}?token={token}"

            if ".pdf*" in url:
                url = f"https://dragoapi.vercel.app/pdf/{url}"

            elif 'encrypted.m' in url:
                appxkey = url.split('*')[1]
                url = url.split('*')[0]

            # Determine ytf based on resolution
            if "youtu" in url:
                ytf = f"bv*[height<={resolution}][ext=mp4]+ba[ext=m4a]/b[height<=?{resolution}]"
            elif "embed" in url:
                ytf = f"bestvideo[height<={resolution}]+bestaudio/best[height<={resolution}]"
            else:
                ytf = f"b[height<={resolution}]/bv[height<={resolution}]+ba/b/bv+ba"

            if "jw-prod" in url:
                url = url.replace("https://apps-s3-jw-prod.utkarshapp.com/admin_v1/file_library/videos","https://d1q5ugnejk3zoi.cloudfront.net/ut-production-jw/admin_v1/file_library/videos")
                cmd = f'yt-dlp -o "{name}.mp4" "{url}"'
            elif "webvideos.classplusapp." in url:
               cmd = f'yt-dlp --add-header "referer:https://web.classplusapp.com/" --add-header "x-cdn-tag:empty" -f "{ytf}" "{url}" -o "{name}.mp4"'
            elif "youtube.com" in url or "youtu.be" in url:
                cmd = f'yt-dlp --cookies youtube_cookies.txt -f "{ytf}" "{url}" -o "{name}.mp4'
            else:
                cmd = f'yt-dlp -f "{ytf}" "{url}" -o "{name}.mp4"'

            # === File Downloading & Sending Logic ===
            if "drive" in url and "google" not in url: # Catch generic drive links but not google drive (handled above)
                ka = await helper.download(url, name)
                copy = await client.send_document(chat_id=channel_id,document=ka, caption=cc1)
                count+=1
                os.remove(ka)

            elif ".pdf" in url:
                if "cwmediabkt99" in url:
                    max_retries = 3
                    retry_delay = 4
                    success = False
                    failure_msgs = []

                    for attempt in range(max_retries):
                        try:
                            await asyncio.sleep(retry_delay)
                            url_pdf = url.replace(" ", "%20")
                            scraper = cloudscraper.create_scraper()
                            response = scraper.get(url_pdf)

                            if response.status_code == 200:
                                with open(f'{name}.pdf', 'wb') as file:
                                    file.write(response.content)
                                await asyncio.sleep(retry_delay)
                                copy = await client.send_document(chat_id=channel_id, document=f'{name}.pdf', caption=cc1)
                                count += 1
                                os.remove(f'{name}.pdf')
                                success = True
                                break
                            else:
                                failure_msg = await client.send_message(message.chat.id, f"Attempt {attempt + 1}/{max_retries} failed: {response.status_code} {response.reason}")
                                failure_msgs.append(failure_msg)
                        except Exception as e:
                            failure_msg = await client.send_message(message.chat.id, f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                            failure_msgs.append(failure_msg)
                            await asyncio.sleep(retry_delay)
                            continue

                    if not success:
                        raise Exception("Failed to download PDF after retries")

                    for msg in failure_msgs:
                        await msg.delete()

                else:
                    cmd_pdf = f'yt-dlp -o "{name}.pdf" "{url}"'
                    download_cmd = f"{cmd_pdf} -R 25 --fragment-retries 25"
                    os.system(download_cmd)
                    if os.path.exists(f'{name}.pdf'):
                        copy = await client.send_document(chat_id=channel_id, document=f'{name}.pdf', caption=cc1)
                        count += 1
                        os.remove(f'{name}.pdf')
                    else:
                         raise Exception("PDF Download failed (file not found)")

            elif ".ws" in url and  url.endswith(".ws"):
                await helper.pdf_download(f"{api_url}utkash-ws?url={url}&authorization={api_token}",f"{name}.html")
                time.sleep(1)
                await client.send_document(chat_id=channel_id, document=f"{name}.html", caption=cchtml)
                os.remove(f'{name}.html')
                count += 1

            elif any(ext in url for ext in [".jpg", ".jpeg", ".png"]):
                ext = url.split('.')[-1]
                cmd_img = f'yt-dlp -o "{name}.{ext}" "{url}"'
                download_cmd = f"{cmd_img} -R 25 --fragment-retries 25"
                os.system(download_cmd)
                if os.path.exists(f'{name}.{ext}'):
                    copy = await client.send_photo(chat_id=channel_id, photo=f'{name}.{ext}', caption=ccimg)
                    count += 1
                    os.remove(f'{name}.{ext}')
                else:
                     raise Exception("Image Download failed")

            elif any(ext in url for ext in [".mp3", ".wav", ".m4a"]):
                ext = url.split('.')[-1]
                cmd_audio = f'yt-dlp -x --audio-format {ext} -o "{name}.{ext}" "{url}"'
                download_cmd = f"{cmd_audio} -R 25 --fragment-retries 25"
                os.system(download_cmd)
                if os.path.exists(f'{name}.{ext}'):
                    await client.send_document(chat_id=channel_id, document=f'{name}.{ext}', caption=cc1)
                    os.remove(f'{name}.{ext}')
                else:
                    raise Exception("Audio Download failed")

            elif 'encrypted.m' in url:
                Show = f"<i><b>Video APPX Encrypted Downloading</b></i>\n<blockquote><b>{str(count).zfill(3)}) {name1}</b></blockquote>"
                prog = await client.send_message(channel_id, Show, disable_web_page_preview=True)

                res_file = await helper.download_and_decrypt_video(url, cmd, name, appxkey)
                filename = res_file
                await prog.delete(True)
                if filename and os.path.exists(filename):
                    await helper.send_vid(client, message, cc, filename, thumbnail, name, prog, channel_id, watermark=watermark)
                    count += 1
                else:
                    raise Exception("Encrypted video download failed")

            elif 'drmcdni' in url or 'drm/wv' in url or 'drm/common' in url:
                Show = f"<i><b>📥 Fast Video Downloading</b></i>\n<blockquote><b>{str(count).zfill(3)}) {name1}</b></blockquote>"
                prog = await client.send_message(channel_id, Show, disable_web_page_preview=True)
                res_file = await helper.decrypt_and_merge_video(mpd, keys_string, path, name, resolution)
                filename = res_file
                await prog.delete(True)
                if filename and os.path.exists(filename):
                    await helper.send_vid(client, message, cc, filename, thumbnail, name, prog, channel_id, watermark=watermark)
                    count += 1
                else:
                     raise Exception("DRM video download failed")
                await asyncio.sleep(1)

            else:
                Show = f"<i><b>📥 Fast Video Downloading</b></i>\n<blockquote><b>{str(count).zfill(3)}) {name1}</b></blockquote>"
                prog = await client.send_message(channel_id, Show, disable_web_page_preview=True)
                res_file = await helper.download_video(url, cmd, name)
                filename = res_file
                await prog.delete(True)
                if filename and os.path.exists(filename):
                    await helper.send_vid(client, message, cc, filename, thumbnail, name, prog, channel_id, watermark=watermark)
                    count += 1
                    time.sleep(1)
                else:
                    raise Exception("Video download failed")

            success_count += 1

        except Exception as e:
            failed_count += 1
            count += 1
            # Error Reporting
            error_msg = f"❌ Failed to download:\nName: {name1}\nLink: {link0}\nError: {str(e)}"

            # Send to chat
            await client.send_message(message.chat.id, error_msg)

            # Send to channel if different
            if channel_id and channel_id != message.chat.id:
                 try:
                     await client.send_message(channel_id, error_msg)
                 except:
                     pass

        # Small delay between files
        await asyncio.sleep(1)

    return {
        "success": success_count,
        "failed": failed_count,
        "total": len(links)
    }
