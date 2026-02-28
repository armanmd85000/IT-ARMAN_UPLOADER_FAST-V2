# 🔧 Standard Library
import os
import time
import asyncio
import logging

# Fix event loop for newer Python versions (Heroku + Pyrogram)
try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

# ⚙️ Pyrogram
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

# 🧠 Bot Modules
import itsgolu as helper
from utils import progress_bar
from vars import *
from gdrive import DriveAPI

auto_flags = {}
stop_flag = False

# Custom Listener Logic
listening_futures = {}

async def listen(self, chat_id, filters=None, timeout=None):
    if timeout is None:
        timeout = 300

    loop = asyncio.get_running_loop()
    future = loop.create_future()

    if chat_id not in listening_futures:
        listening_futures[chat_id] = []
    listening_futures[chat_id].append((future, filters))

    try:
        return await asyncio.wait_for(future, timeout)
    except asyncio.TimeoutError:
        # Cleanup
        if chat_id in listening_futures:
            listening_futures[chat_id] = [x for x in listening_futures[chat_id] if x[0] != future]
        raise

Client.listen = listen

# Initialize bot
bot = Client(
    "drive_uploader",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=300,
    sleep_threshold=60,
    in_memory=True
)

async def listener_handler(client, message):
    chat_id = message.chat.id
    if chat_id in listening_futures:
        listeners = listening_futures[chat_id]
        matched_idx = -1

        for i, (future, flt) in enumerate(listeners):
            if future.done():
                continue

            if flt is not None:
                if not await flt(client, message):
                    continue

            matched_idx = i
            future.set_result(message)
            message.stop_propagation()
            break

        if matched_idx != -1:
            listeners.pop(matched_idx)
            if not listeners:
                del listening_futures[chat_id]

bot.add_handler(MessageHandler(listener_handler), group=-1)

# Authorization filter
def auth_check_filter(_, client, message):
    if not OWNER_ID:
        return True # If no owner ID is set, allow anyone (for testing). Otherwise return False.
    return message.from_user.id == OWNER_ID

auth_filter = filters.create(auth_check_filter)

@bot.on_message(~auth_filter & filters.private & filters.command(["start", "drive"]))
async def unauthorized_handler(client, message: Message):
    await message.reply("You are not authorized to use this bot. Contact owner.")

@bot.on_message(filters.command("start") & filters.private & auth_filter)
async def start(client: Client, message: Message):
    await message.reply(
        "**Hello! I am Google Drive Telegram Uploader Bot.**\n\n"
        "Send /drive `<google_drive_folder_url>` to start downloading and uploading files.\n"
        "Send /cookies with a `cookies.txt` file attached to authenticate restricted downloads."
    )

@bot.on_message(filters.command("stop") & filters.private & auth_filter)
async def stop_command(client: Client, message: Message):
    global stop_flag
    stop_flag = True
    await message.reply("🛑 Stop command received! The bot will halt after finishing the current task.")

@bot.on_message(filters.command("cookies") & filters.private & auth_filter)
async def save_cookies(client: Client, message: Message):
    target_message = message
    if not message.document:
        if message.reply_to_message and message.reply_to_message.document:
            target_message = message.reply_to_message
        else:
            await message.reply("Please send a `cookies.txt` file and put `/cookies` in the caption, or reply to a file with `/cookies`.")
            return

    if not target_message.document.file_name.endswith('.txt'):
        await message.reply("The file must be a `.txt` file containing your exported cookies.")
        return

    await target_message.download(file_name="drive_cookies.txt")
    await message.reply("✅ `drive_cookies.txt` has been saved successfully! You can now download restricted files.")

@bot.on_message(filters.command(["drive"]) & auth_filter)
async def drive_handler(client: Client, m: Message):
    global stop_flag
    stop_flag = False
    args = m.text.split(maxsplit=1)
    if len(args) < 2:
        await m.reply_text("Please provide a Google Drive folder link. Example: `/drive https://drive.google.com/drive/folders/...`")
        return

    url = args[1].strip()
    
    drive_api = DriveAPI()
    if not drive_api.service:
        await m.reply_text("Failed to connect to Google Drive API. Please check your credentials.")
        return

    folder_id = drive_api.extract_folder_id(url)
    if not folder_id:
        await m.reply_text("Could not extract folder ID from the provided URL.")
        return

    # Ask for target channel
    editable = await m.reply_text("**Provide the Channel ID or send `/d` to use the current chat:**\n\nEx: -100XXXXXXXXX")
    try:
        input_msg: Message = await client.listen(m.chat.id, timeout=30)
        channel_id_text = input_msg.text.strip()
        await input_msg.delete(True)
    except asyncio.TimeoutError:
        channel_id_text = '/d'
    
    if channel_id_text == '/d':
        channel_id = m.chat.id
    else:
        try:
            channel_id = int(channel_id_text)
        except ValueError:
            await editable.edit("❌ Invalid Channel ID format. Please use a number. Exiting.")
            return

    # Ask for custom thumbnail
    await editable.edit("**1. Send an Image for Thumbnail\n2. Send `/d` for default Thumbnail\n3. Send `/skip` to skip Thumbnail**")
    thumb = "/d"
    try:
        input_thumb: Message = await client.listen(m.chat.id, timeout=30)
        if input_thumb.photo:
            os.makedirs("downloads", exist_ok=True)
            temp_file = f"downloads/thumb_{m.from_user.id}.jpg"
            await input_thumb.download(file_name=temp_file)
            thumb = temp_file
            await editable.edit("✅ Custom thumbnail saved!")
        elif input_thumb.text:
            if input_thumb.text == "/d":
                thumb = "/d"
                await editable.edit("📰 Using default thumbnail.")
            elif input_thumb.text == "/skip":
                thumb = "no"
                await editable.edit("♻️ Skipping thumbnail.")
        await input_thumb.delete(True)
        await asyncio.sleep(1)
    except asyncio.TimeoutError:
        await editable.edit("⚠️ Timeout! Using default thumbnail.")
        await asyncio.sleep(1)

    # Ask for watermark
    await editable.edit("**1. Send a Text for Watermark\n2. Send `/d` for no watermark**")
    try:
        input_wm: Message = await client.listen(m.chat.id, timeout=30)
        watermark = input_wm.text.strip()
        await input_wm.delete(True)
    except asyncio.TimeoutError:
        watermark = '/d'

    await editable.edit(f"⏳ **Fetching folder contents...**")

    # Traverse folder
    files = await drive_api.traverse_folder_recursive(folder_id)
    if not files:
        await editable.edit("❌ No files found in the folder or failed to access the folder.")
        return

    await editable.edit(f"✅ Found **{len(files)}** files. Starting download...")

    success_count = 0
    failed_count = 0

    os.makedirs("downloads", exist_ok=True)

    last_folder_path = None

    for index, file in enumerate(files, 1):
        if stop_flag:
            await client.send_message(m.chat.id, "🛑 **Process stopped by user.**")
            break

        file_name = file['name']
        file_id = file['id']
        mime_type = file.get('mimeType', '')
        folder_path = file.get('path', 'Unknown_Folder')

        # Send folder text to channel if entering a new folder
        if folder_path != last_folder_path:
            last_folder_path = folder_path

            # Extract main folder and subfolder logic
            parts = folder_path.split("/")
            main_folder = parts[0]
            sub_folder = " -> ".join(parts[1:]) if len(parts) > 1 else "None"

            await client.send_message(
                chat_id=channel_id,
                text=f"📂 **Main Folder:** `{main_folder}`\n"
                     f"📁 **Subfolder:** `{sub_folder}`"
            )

        status_msg = await client.send_message(m.chat.id, f"📥 Downloading `{file_name}`\n📂 Folder: `{folder_path}`")
        
        # Download
        last_reported_percent = -10
        async def update_progress(percentage):
             nonlocal last_reported_percent
             current_percent = int(percentage)
             # Update every 10%
             if current_percent >= last_reported_percent + 10:
                 try:
                     await status_msg.edit_text(f"📥 Downloading `{file_name}`\n📂 Folder: `{folder_path}`\nProgress: {current_percent}%")
                     last_reported_percent = current_percent
                 except:
                     pass

        downloaded_path = await drive_api.download_file(file_id, file_name, "downloads", progress_callback=update_progress)
        
        if not downloaded_path:
            await status_msg.edit_text(f"❌ Failed to download `{file_name}`")
            failed_count += 1
            await asyncio.sleep(2)
            await status_msg.delete()
            continue
        
        await status_msg.edit_text(f"📤 Uploading `{file_name}`...")

        # Construct Caption
        caption = (
            f"**📁 Folder:** `{folder_path}`\n"
            f"**📄 File:** `{file_name}`\n\n"
            f"**🎓 Uploaded By:** {CREDIT}"
        )

        try:
            if 'video' in mime_type or file_name.lower().endswith(('.mp4', '.mkv', '.webm', '.avi')):
                await helper.send_vid(client, m, caption, downloaded_path, thumb, file_name, status_msg, channel_id, watermark=watermark)
            else:
                await client.send_document(
                    chat_id=channel_id,
                    document=downloaded_path,
                    caption=caption
                )
                if os.path.exists(downloaded_path):
                    os.remove(downloaded_path)
                await status_msg.delete()
            success_count += 1
        except Exception as e:
            logging.error(f"Failed to upload {file_name}: {e}")
            await client.send_message(m.chat.id, f"❌ Failed to upload `{file_name}`: {e}")
            if os.path.exists(downloaded_path):
                os.remove(downloaded_path)
            failed_count += 1
            await status_msg.delete()

    await client.send_message(
        m.chat.id,
        (
            f"<b>✅ Process Completed!</b>\n\n"
            f"🔗 Total Files: `{len(files)}`\n"
            f"🟢 Successfully Uploaded: `{success_count}`\n"
            f"🔴 Failed: `{failed_count}`\n"
        )
    )

print("Bot Started...")
bot.run()
