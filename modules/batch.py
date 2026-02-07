import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from modules.drm_handler import process_links
from vars import CREDIT, OWNER_ID

auto_flags = {}

async def batch_handler(client: Client, message: Message):
    chat_id = message.chat.id

    # 1. Collect Files
    files = []
    editable = await message.reply_text(
        "**Multi-File Batch Mode**\n\n"
        "Please send the `.txt` files you want to process.\n"
        "Send as many as you want.\n"
        "When finished, send `/done` to start processing.\n"
        "Send `/cancel` to abort."
    )

    while True:
        try:
            input_msg: Message = await client.listen(chat_id)

            if input_msg.text:
                if input_msg.text == "/done":
                    if not files:
                        await message.reply_text("❌ No files received. Send files first.")
                        continue
                    break
                if input_msg.text == "/cancel":
                    await message.reply_text("❌ Batch cancelled.")
                    return

            if input_msg.document and input_msg.document.file_name.endswith('.txt'):
                file_path = await input_msg.download()
                files.append(file_path)
                await message.reply_text(f"✅ Received: `{input_msg.document.file_name}`\nTotal: {len(files)} files.\nSend more or `/done`.")
            else:
                 if input_msg.text != "/done":
                    await message.reply_text("⚠️ Please send a .txt file or /done.")

        except asyncio.TimeoutError:
            await message.reply_text("❌ Timeout. Batch cancelled.")
            return

    # 2. Collect Settings (Once for all files)

    # Resolution
    timeout_duration = 60
    await editable.edit("**🎞️  Eɴᴛᴇʀ  Rᴇꜱᴏʟᴜᴛɪᴏɴ\n\n╭━━⪼  `360`\n┣━━⪼  `480`\n┣━━⪼  `720`\n╰━━⪼  `1080`**")
    try:
        input2: Message = await client.listen(chat_id, timeout=timeout_duration)
        raw_text2 = input2.text
        await input2.delete(True)
    except asyncio.TimeoutError:
        raw_text2 = '480' # Default

    # Watermark
    await editable.edit("**1. Send A Text For Watermark\n2. Send /d for no watermark & fast dwnld**")
    try:
        inputx: Message = await client.listen(chat_id, timeout=timeout_duration)
        watermark = inputx.text
        await inputx.delete(True)
    except asyncio.TimeoutError:
        watermark = '/d'

    # Credit
    await editable.edit(f"**1. Send Your Name For Caption Credit\n2. Send /d For default Credit **")
    try:
        input3: Message = await client.listen(chat_id, timeout=timeout_duration)
        raw_text3 = input3.text
        await input3.delete(True)
    except asyncio.TimeoutError:
        raw_text3 = '/d'

    # Token
    await editable.edit(f"**1. Send PW Token For MPD urls\n 2. Send /d For Others **")
    try:
        input4: Message = await client.listen(chat_id, timeout=timeout_duration)
        raw_text4 = input4.text
        await input4.delete(True)
    except asyncio.TimeoutError:
        raw_text4 = '/d'

    # Thumbnail
    await editable.edit("**1. Send A Image For Thumbnail\n2. Send /d For default Thumbnail\n3. Send /skip For Skipping**")
    thumb = "/d"
    try:
        input6 = await client.listen(chat_id=chat_id, timeout=timeout_duration)
        if input6.photo:
            if not os.path.exists("downloads"):
                os.makedirs("downloads")
            temp_file = f"downloads/thumb_{message.from_user.id}.jpg"
            await client.download_media(message=input6.photo, file_name=temp_file)
            thumb = temp_file
        elif input6.text:
            if input6.text == "/skip": thumb = "no"
            # else default /d
        await input6.delete(True)
    except asyncio.TimeoutError:
        pass

    # Channel
    await editable.edit("__**📢 Provide the Channel ID or send /d__\n\n<blockquote>🔹Send Your Channel ID where you want upload files.\n\nEx : -100XXXXXXXXX</blockquote>\n**")
    try:
        input7: Message = await client.listen(chat_id, timeout=timeout_duration)
        raw_text7 = input7.text
        await input7.delete(True)
    except asyncio.TimeoutError:
        raw_text7 = '/d'

    if "/d" in raw_text7:
        channel_id = message.chat.id
    else:
        try:
            channel_id = int(raw_text7)
        except:
             channel_id = message.chat.id

    await editable.delete()

    # 3. Process Files
    await message.reply_text(f"🚀 Starting Batch Process for {len(files)} files...")

    for idx, file_path in enumerate(files):
        try:
            # Parse File Name for Batch Name
            file_name_with_ext = os.path.basename(file_path)
            file_name = os.path.splitext(file_name_with_ext)[0]
            batch_name = file_name.replace('_', ' ')

            # Parse Links
            links = []
            try:
                with open(file_path, "r", encoding='utf-8') as f:
                    content = f.read().split("\n")
                for line in content:
                    if "://" in line:
                        parts = line.split("://", 1)
                        if len(parts) == 2:
                            links.append([parts[0], parts[1]])
            except Exception as e:
                await message.reply_text(f"❌ Failed to read file {file_name}: {e}")
                continue

            if not links:
                await message.reply_text(f"⚠️ No links found in {file_name}. Skipping.")
                continue

            await message.reply_text(f"📂 **Processing File {idx+1}/{len(files)}**: `{file_name}`\nLinks: {len(links)}")

            # Start Index logic
            start_index = 1
            if idx == 0:
                # Ask for start index ONLY for first file
                await message.reply_text(
                    f"**Total 🔗 links found are {len(links)}**\n"
                    f"Send Your Index File ID Between 1-{len(links)} ."
                )
                try:
                    input0: Message = await client.listen(chat_id, timeout=timeout_duration)
                    if input0.text.isdigit():
                        start_index = int(input0.text)
                    await input0.delete(True)
                except asyncio.TimeoutError:
                    start_index = 1

            # Call Processor
            await process_links(
                client=client,
                message=message,
                links=links,
                start_index=start_index,
                batch_name=batch_name,
                resolution=raw_text2,
                watermark=watermark,
                credit=raw_text3,
                token=raw_text4,
                thumbnail=thumb,
                channel_id=channel_id
            )

            await message.reply_text(f"✅ **Completed File {idx+1}/{len(files)}**: `{file_name}`")

        except Exception as e:
             await message.reply_text(f"❌ Error processing file {file_path}: {e}")

        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)

    await message.reply_text("🎉 **Batch Processing Complete!**")
