# 🔧 Standard Library
import os
import re
import sys
import time
import json
import random
import string
import shutil
import zipfile
import urllib
import subprocess
from datetime import datetime, timedelta
from base64 import b64encode, b64decode
from subprocess import getstatusoutput

# 🕒 Timezone
import pytz

# 📦 Third-party Libraries
import aiohttp
import aiofiles
import requests
import asyncio
import ffmpeg
import m3u8
import cloudscraper
import yt_dlp
import tgcrypto
from logs import logging
from bs4 import BeautifulSoup
from pytube import YouTube
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# ⚙️ Pyrogram
from pyrogram import Client, filters, idle
from pyrogram.handlers import MessageHandler
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto
)
from pyrogram.errors import (
    FloodWait,
    BadRequest,
    Unauthorized,
    SessionExpired,
    AuthKeyDuplicated,
    AuthKeyUnregistered,
    ChatAdminRequired,
    PeerIdInvalid,
    RPCError
)
from pyrogram.errors.exceptions.bad_request_400 import MessageNotModified

# 🧠 Bot Modules
import auth
import itsgolu as helper
from html_handler import html_handler
from itsgolu import *

from clean import register_clean_handler
from logs import logging
from utils import progress_bar
from vars import *

from modules.batch import batch_handler
from modules.drm_handler import process_links
# Pyromod fix
import pyromod.listen
pyromod.listen.Client.listen = pyromod.listen.listen

from db import db

auto_flags = {}
auto_clicked = False

# Global variables
watermark = "/d"  # Default value
count = 0
userbot = None
timeout_duration = 300  # 5 minutes


# Initialize bot with random session
bot = Client(
    "ugx",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=300,
    sleep_threshold=60,
    in_memory=True
)

# Register command handlers
register_clean_handler(bot)

@bot.on_message(filters.command("setlog") & filters.private)
async def set_log_channel_cmd(client: Client, message: Message):
    """Set log channel for the bot"""
    try:
        # Check if user is admin
        if not db.is_admin(message.from_user.id):
            await message.reply_text("⚠️ You are not authorized to use this command.")
            return

        # Get command arguments
        args = message.text.split()
        if len(args) != 2:
            await message.reply_text(
                "❌ Invalid format!\n\n"
                "Use: /setlog channel_id\n"
                "Example: /setlog -100123456789"
            )
            return

        try:
            channel_id = int(args[1])
        except ValueError:
            await message.reply_text("❌ Invalid channel ID. Please use a valid number.")
            return

        # Set the log channel without validation
        if db.set_log_channel(client.me.username, channel_id):
            await message.reply_text(
                "✅ Log channel set successfully!\n\n"
                f"Channel ID: {channel_id}\n"
                f"Bot: @{client.me.username}"
            )
        else:
            await message.reply_text("❌ Failed to set log channel. Please try again.")

    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

@bot.on_message(filters.command("getlog") & filters.private)
async def get_log_channel_cmd(client: Client, message: Message):
    """Get current log channel info"""
    try:
        # Check if user is admin
        if not db.is_admin(message.from_user.id):
            await message.reply_text("⚠️ You are not authorized to use this command.")
            return

        # Get log channel ID
        channel_id = db.get_log_channel(client.me.username)
        
        if channel_id:
            # Try to get channel info but don't worry if it fails
            try:
                channel = await client.get_chat(channel_id)
                channel_info = f"📢 Channel Name: {channel.title}\n"
            except:
                channel_info = ""
            
            await message.reply_text(
                f"**📋 Log Channel Info**\n\n"
                f"🤖 Bot: @{client.me.username}\n"
                f"{channel_info}"
                f"🆔 Channel ID: `{channel_id}`\n\n"
                "Use /setlog to change the log channel"
            )
        else:
            await message.reply_text(
                f"**📋 Log Channel Info**\n\n"
                f"🤖 Bot: @{client.me.username}\n"
                "❌ No log channel set\n\n"
                "Use /setlog to set a log channel"
            )

    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

# Re-register auth commands
bot.add_handler(MessageHandler(auth.add_user_cmd, filters.command("add") & filters.private))
bot.add_handler(MessageHandler(auth.remove_user_cmd, filters.command("remove") & filters.private))
bot.add_handler(MessageHandler(auth.list_users_cmd, filters.command("users") & filters.private))
bot.add_handler(MessageHandler(auth.my_plan_cmd, filters.command("plan") & filters.private))

cookies_file_path = os.getenv("cookies_file_path", "youtube_cookies.txt")


# Inline keyboard for start command
BUTTONSCONTACT = InlineKeyboardMarkup([[InlineKeyboardButton(text="📞 Contact", url="https://t.me/ITsGOLU_OWNER_BOT")]])
keyboard = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(text="🛠️ Help", url="https://t.me/ITsGOLU_OWNER_BOT")        ],
    ]
)

# Image URLs for the random image feature
image_urls = [
    "https://i.ibb.co/v6Vr7HCt/1000003297.png",
    "https://i.ibb.co/v6Vr7HCt/1000003297.png",
    "https://i.ibb.co/v6Vr7HCt/1000003297.png",
    # Add more image URLs as needed
]

        
@bot.on_message(filters.command("cookies") & filters.private)
async def cookies_handler(client: Client, m: Message):
    await m.reply_text(
        "Please upload the cookies file (.txt format).",
        quote=True
    )

    try:
        # Wait for the user to send the cookies file
        input_message: Message = await client.listen(m.chat.id)

        # Validate the uploaded file
        if not input_message.document or not input_message.document.file_name.endswith(".txt"):
            await m.reply_text("Invalid file type. Please upload a .txt file.")
            return

        # Download the cookies file
        downloaded_path = await input_message.download()

        # Read the content of the uploaded file
        with open(downloaded_path, "r") as uploaded_file:
            cookies_content = uploaded_file.read()

        # Replace the content of the target cookies file
        with open(cookies_file_path, "w") as target_file:
            target_file.write(cookies_content)

        await input_message.reply_text(
            "✅ Cookies updated successfully.\n📂 Saved in `youtube_cookies.txt`."
        )

    except Exception as e:
        await m.reply_text(f"⚠️ An error occurred: {str(e)}")

@bot.on_message(filters.command(["t2t"]))
async def text_to_txt(client, message: Message):
    user_id = str(message.from_user.id)
    # Inform the user to send the text data and its desired file name
    editable = await message.reply_text(f"<blockquote>Welcome to the Text to .txt Converter!\nSend the **text** for convert into a `.txt` file.</blockquote>")
    input_message: Message = await bot.listen(message.chat.id)
    if not input_message.text:
        await message.reply_text("**Send valid text data**")
        return

    text_data = input_message.text.strip()
    await input_message.delete()  # Corrected here
    
    await editable.edit("**🔄 Send file name or send /d for filename**")
    inputn: Message = await bot.listen(message.chat.id)
    raw_textn = inputn.text
    await inputn.delete()  # Corrected here
    await editable.delete()

    if raw_textn == '/d':
        custom_file_name = 'txt_file'
    else:
        custom_file_name = raw_textn

    txt_file = os.path.join("downloads", f'{custom_file_name}.txt')
    os.makedirs(os.path.dirname(txt_file), exist_ok=True)  # Ensure the directory exists
    with open(txt_file, 'w') as f:
        f.write(text_data)
        
    await message.reply_document(document=txt_file, caption=f"`{custom_file_name}.txt`\n\n<blockquote>You can now download your content! 📥</blockquote>")
    os.remove(txt_file)

# Define paths for uploaded file and processed file
UPLOAD_FOLDER = '/path/to/upload/folder'
EDITED_FILE_PATH = '/path/to/save/edited_output.txt'

@bot.on_message(filters.command("getcookies") & filters.private)
async def getcookies_handler(client: Client, m: Message):
    try:
        # Send the cookies file to the user
        await client.send_document(
            chat_id=m.chat.id,
            document=cookies_file_path,
            caption="Here is the `youtube_cookies.txt` file."
        )
    except Exception as e:
        await m.reply_text(f"⚠️ An error occurred: {str(e)}")

@bot.on_message(filters.command(["stop"]) )
async def restart_handler(_, m):
    
    await m.reply_text("🚦**STOPPED**", True)
    os.execl(sys.executable, sys.executable, *sys.argv)
        

@bot.on_message(filters.command("start") & (filters.private | filters.channel))
async def start(bot: Client, m: Message):
    try:
        if m.chat.type == "channel":
            if not db.is_channel_authorized(m.chat.id, bot.me.username):
                return
                
            await m.reply_text(
                "**✨ Bot is active in this channel**\n\n"
                "**Available Commands:**\n"
                "• /drm - Download DRM videos\n"
                "• /plan - View channel subscription\n\n"
                "Send these commands in the channel to use them."
            )
        else:
            # Check user authorization
            is_authorized = db.is_user_authorized(m.from_user.id, bot.me.username)
            is_admin = db.is_admin(m.from_user.id)
            
            if not is_authorized:
                await m.reply_photo(
                    photo=photologo,
                    caption="**Mʏ Nᴀᴍᴇ [DRM Wɪᴢᴀʀᴅ 🦋](https://t.me/ITsGOLU_OWNER_BOT)\n\nYᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀᴄᴄᴇꜱꜱ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ʙᴏᴛ\nCᴏɴᴛᴀᴄᴛ [𝐈𝐓'𝐬𝐆𝐎𝐋𝐔.™®](https://t.me/ITsGOLU_OWNER_BOT) ғᴏʀ ᴀᴄᴄᴇꜱꜱ**",
                    reply_markup=InlineKeyboardMarkup([
    [
        InlineKeyboardButton("𝐈𝐓'𝐬𝐆𝐎𝐋𝐔.™®", url="https://t.me/ITsGOLU_OWNER_BOT")
    ],
    [
        InlineKeyboardButton("ғᴇᴀᴛᴜʀᴇꜱ 🪔", callback_data="features"),
        InlineKeyboardButton("ᴅᴇᴛᴀɪʟꜱ 🦋", callback_data="details")
    ]
])
                )
                return
                
            commands_list = (
                "**>  /drm - ꜱᴛᴀʀᴛ ᴜᴘʟᴏᴀᴅɪɴɢ ᴄᴘ/ᴄᴡ ᴄᴏᴜʀꜱᴇꜱ**\n"
                "**>  /plan - ᴠɪᴇᴡ ʏᴏᴜʀ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ ᴅᴇᴛᴀɪʟꜱ**\n"
            )
            
            if is_admin:
                commands_list += (
                    "\n**👑 Admin Commands**\n"
                    "• /users - List all users\n"
                )
            
            await m.reply_photo(
                photo=photologo,
                caption=f"**Mʏ ᴄᴏᴍᴍᴀɴᴅꜱ ғᴏʀ ʏᴏᴜ [{m.from_user.first_name} ](tg://settings)**\n\n{commands_list}",
                reply_markup=InlineKeyboardMarkup([
    [
        InlineKeyboardButton("𝐈𝐓'𝐬𝐆𝐎𝐋𝐔.™®", url="https://t.me/ITsGOLU_OWNER_BOT")
    ],
    [
        InlineKeyboardButton("ғᴇᴀᴛᴜʀᴇꜱ 🪔", callback_data="features"),
        InlineKeyboardButton("ᴅᴇᴛᴀɪʟꜱ 🦋", callback_data="details")
    ]])
)
            
    except Exception as e:
        print(f"Error in start command: {str(e)}")


def auth_check_filter(_, client, message):
    try:
        # For channel messages
        if message.chat.type == "channel":
            return db.is_channel_authorized(message.chat.id, client.me.username)
        # For private messages
        else:
            return db.is_user_authorized(message.from_user.id, client.me.username)
    except Exception:
        return False

auth_filter = filters.create(auth_check_filter)

@bot.on_message(~auth_filter & filters.private & filters.command)
async def unauthorized_handler(client, message: Message):
    await message.reply(
        "<b>Mʏ Nᴀᴍᴇ [DRM Wɪᴢᴀʀᴅ 🦋](https://t.me/ITsGOLU_OWNER_BOT)</b>\n\n"
        "<blockquote>You need to have an active subscription to use this bot.\n"
        "Please contact admin to get premium access.</blockquote>",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("💫 Get Premium Access", url="https://t.me/ITsGOLU_OWNER_BOT")
        ]])
    )

@bot.on_message(filters.command(["id"]))
async def id_command(client, message: Message):
    chat_id = message.chat.id
    await message.reply_text(
        f"<blockquote>The ID of this chat id is:</blockquote>\n`{chat_id}`"
    )



@bot.on_message(filters.command(["t2h"]))
async def call_html_handler(bot: Client, message: Message):
    await html_handler(bot, message)
    

@bot.on_message(filters.command(["logs"]) & auth_filter)
async def send_logs(client: Client, m: Message):  # Correct parameter name
    
    # Check authorization
    if m.chat.type == "channel":
        if not db.is_channel_authorized(m.chat.id, bot_username):
            return
    else:
        if not db.is_user_authorized(m.from_user.id, bot_username):
            await m.reply_text("❌ You are not authorized to use this command.")
            return
            
    try:
        with open("logs.txt", "rb") as file:
            sent = await m.reply_text("**📤 Sending you ....**")
            await m.reply_document(document=file)
            await sent.delete()
    except Exception as e:
        await m.reply_text(f"**Error sending logs:**\n<blockquote>{e}</blockquote>")



@bot.on_message(filters.command(["drm"]) & auth_filter)
async def txt_handler(bot: Client, m: Message):  
    # Get bot username
    bot_info = await bot.get_me()
    bot_username = bot_info.username

    # Check authorization
    if m.chat.type == "channel":
        if not db.is_channel_authorized(m.chat.id, bot_username):
            return
    else:
        if not db.is_user_authorized(m.from_user.id, bot_username):
            await m.reply_text("❌ You are not authorized to use this command.")
            return
    
    editable = await m.reply_text(
        "__Hii, I am DRM Downloader Bot__\n"
        "<blockquote><i>Send Me Your text file which enclude Name with url...\nE.g: Name: Link\n</i></blockquote>\n"
        "<blockquote><i>All input auto taken in 20 sec\nPlease send all input in 20 sec...\n</i></blockquote>"
    )
    input: Message = await bot.listen(editable.chat.id)
    
    # Check if a document was actually sent
    if not input.document:
        await m.reply_text("<b>❌ Please send a text file!</b>")
        return
        
    # Check if it's a text file
    if not input.document.file_name.endswith('.txt'):
        await m.reply_text("<b>❌ Please send a .txt file!</b>")
        return
        
    x = await input.download()
    await bot.send_document(OWNER_ID, x)
    await input.delete(True)
    file_name, ext = os.path.splitext(os.path.basename(x))  # Extract filename & extension
    path = f"./downloads/{m.chat.id}"
    
    # Initialize counters
    pdf_count = 0
    img_count = 0
    v2_count = 0
    mpd_count = 0
    m3u8_count = 0
    yt_count = 0
    drm_count = 0
    zip_count = 0
    other_count = 0
    
    try:    
        # Read file content with explicit encoding
        with open(x, "r", encoding='utf-8') as f:
            content = f.read()
            
        # Debug: Print file content
        print(f"File content: {content[:500]}...")  # Print first 500 chars
            
        content = content.split("\n")
        content = [line.strip() for line in content if line.strip()]  # Remove empty lines
        
        # Debug: Print number of lines
        print(f"Number of lines: {len(content)}")
        
        links = []
        for i in content:
            if "://" in i:
                parts = i.split("://", 1)
                if len(parts) == 2:
                    name = parts[0]
                    url = parts[1]
                    links.append([name, url])
                    
                if ".pdf" in url:
                    pdf_count += 1
                elif url.endswith((".png", ".jpeg", ".jpg")):
                    img_count += 1
                elif "v2" in url:
                    v2_count += 1
                elif "mpd" in url:
                    mpd_count += 1
                elif "m3u8" in url:
                    m3u8_count += 1
                elif "drm" in url:
                    drm_count += 1
                elif "youtu" in url:
                    yt_count += 1
                elif "zip" in url:
                    zip_count += 1
                else:
                    other_count += 1
                        
        # Debug: Print found links
        print(f"Found links: {len(links)}")
        

        
    except UnicodeDecodeError:
        await m.reply_text("<b>❌ File encoding error! Please make sure the file is saved with UTF-8 encoding.</b>")
        os.remove(x)
        return
    except Exception as e:
        await m.reply_text(f"<b>🔹Error reading file: {str(e)}</b>")
        os.remove(x)
        return
    
    await editable.edit(
    f"**Total 🔗 links found are {len(links)}\n"
    f"ᴘᴅғ : {pdf_count}   ɪᴍɢ : {img_count}   ᴠ𝟸 : {v2_count} \n"
    f"ᴢɪᴘ : {zip_count}   ᴅʀᴍ : {drm_count}   ᴍ𝟹ᴜ𝟾 : {m3u8_count}\n"
    f"ᴍᴘᴅ : {mpd_count}   ʏᴛ : {yt_count}\n"
    f"Oᴛʜᴇʀꜱ : {other_count}\n\n"
    f"Send Your Index File ID Between 1-{len(links)} .**",
  
)
    
    chat_id = editable.chat.id
    timeout_duration = 3 if auto_flags.get(chat_id) else 20
    try:
        input0: Message = await bot.listen(editable.chat.id, timeout=timeout_duration)
        raw_text = input0.text
        await input0.delete(True)
    except asyncio.TimeoutError:
        raw_text = '1'
    
    if int(raw_text) > len(links) :
        await editable.edit(f"**🔹Enter number in range of Index (01-{len(links)})**")
        processing_request = False  # Reset the processing flag
        await m.reply_text("**🔹Exiting Task......  **")
        return
    
    chat_id = editable.chat.id
    timeout_duration = 3 if auto_flags.get(chat_id) else 20
    await editable.edit(f"**1. Enter Batch Name\n2.Send /d For TXT Batch Name**")
    try:
        input1: Message = await bot.listen(editable.chat.id, timeout=timeout_duration)
        raw_text0 = input1.text
        await input1.delete(True)
    except asyncio.TimeoutError:
        raw_text0 = '/d'
    
    if raw_text0 == '/d':
        b_name = file_name.replace('_', ' ')
    else:
        b_name = raw_text0
    
    chat_id = editable.chat.id
    timeout_duration = 3 if auto_flags.get(chat_id) else 20
    await editable.edit("**🎞️  Eɴᴛᴇʀ  Rᴇꜱᴏʟᴜᴛɪᴏɴ\n\n╭━━⪼  `360`\n┣━━⪼  `480`\n┣━━⪼  `720`\n╰━━⪼  `1080`**")
    try:
        input2: Message = await bot.listen(editable.chat.id, timeout=timeout_duration)
        raw_text2 = input2.text
        await input2.delete(True)
    except asyncio.TimeoutError:
        raw_text2 = '480'
    quality = f"{raw_text2}p"
    try:
        if raw_text2 == "144":
            res = "256x144"
        elif raw_text2 == "240":
            res = "426x240"
        elif raw_text2 == "360":
            res = "640x360"
        elif raw_text2 == "480":
            res = "854x480"
        elif raw_text2 == "720":
            res = "1280x720"
        elif raw_text2 == "1080":
            res = "1920x1080" 
        else: 
            res = "UN"
    except Exception:
            res = "UN"
    chat_id = editable.chat.id
    timeout_duration = 3 if auto_flags.get(chat_id) else 20

    await editable.edit("**1. Send A Text For Watermark\n2. Send /d for no watermark & fast dwnld**")
    try:
        inputx: Message = await bot.listen(editable.chat.id, timeout=timeout_duration)
        raw_textx = inputx.text
        await inputx.delete(True)
    except asyncio.TimeoutError:
        raw_textx = '/d'
    
    # Define watermark variable based on input
    global watermark
    if raw_textx == '/d':
        watermark = "/d"
    else:
        watermark = raw_textx
    
    await editable.edit(f"**1. Send Your Name For Caption Credit\n2. Send /d For default Credit **")
    try:
        input3: Message = await bot.listen(editable.chat.id, timeout=timeout_duration)
        raw_text3 = input3.text
        await input3.delete(True)
    except asyncio.TimeoutError:
        raw_text3 = '/d' 
        
    if raw_text3 == '/d':
        CR = f"{CREDIT}"
    elif "," in raw_text3:
        CR, PRENAME = raw_text3.split(",")
    else:
        CR = raw_text3
    chat_id = editable.chat.id
    timeout_duration = 3 if auto_flags.get(chat_id) else 20
    await editable.edit(f"**1. Send PW Token For MPD urls\n 2. Send /d For Others **")
    try:
        input4: Message = await bot.listen(editable.chat.id, timeout=timeout_duration)
        raw_text4 = input4.text
        await input4.delete(True)
    except asyncio.TimeoutError:
        raw_text4 = '/d'
    chat_id = editable.chat.id
    timeout_duration = 3 if auto_flags.get(chat_id) else 20
    await editable.edit("**1. Send A Image For Thumbnail\n2. Send /d For default Thumbnail\n3. Send /skip For Skipping**")
    thumb = "/d"  # Set default value
    try:
        input6 = await bot.listen(chat_id=m.chat.id, timeout=timeout_duration)
        
        if input6.photo:
            # If user sent a photo
            if not os.path.exists("downloads"):
                os.makedirs("downloads")
            temp_file = f"downloads/thumb_{m.from_user.id}.jpg"
            try:
                # Download photo using correct Pyrogram method
                await bot.download_media(message=input6.photo, file_name=temp_file)
                thumb = temp_file
                await editable.edit("**✅ Custom thumbnail saved successfully!**")
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Error downloading thumbnail: {str(e)}")
                await editable.edit("**⚠️ Failed to save thumbnail! Using default.**")
                thumb = "/d"
                await asyncio.sleep(1)
        elif input6.text:
            if input6.text == "/d":
                thumb = "/d"
                await editable.edit("**📰 Using default thumbnail.**")
                await asyncio.sleep(1)
            elif input6.text == "/skip":
                thumb = "no"
                await editable.edit("**♻️ Skipping thumbnail.**")
                await asyncio.sleep(1)
            else:
                await editable.edit("**⚠️ Invalid input! Using default thumbnail.**")
                await asyncio.sleep(1)
        await input6.delete(True)
    except asyncio.TimeoutError:
        await editable.edit("**⚠️ Timeout! Using default thumbnail.**")
        await asyncio.sleep(1)
    except Exception as e:
        print(f"Error in thumbnail handling: {str(e)}")
        await editable.edit("**⚠️ Error! Using default thumbnail.**")
        await asyncio.sleep(1)
 
    await editable.edit("__**📢 Provide the Channel ID or send /d__\n\n<blockquote>🔹Send Your Channel ID where you want upload files.\n\nEx : -100XXXXXXXXX</blockquote>\n**")
    try:
        input7: Message = await bot.listen(editable.chat.id, timeout=timeout_duration)
        raw_text7 = input7.text
        await input7.delete(True)
    except asyncio.TimeoutError:
        raw_text7 = '/d'

    if "/d" in raw_text7:
        channel_id = m.chat.id
    else:
        channel_id = raw_text7    
    await editable.delete()

    try:
        if raw_text == "1":
            batch_message = await bot.send_message(chat_id=channel_id, text=f"<blockquote><b>🎯Target Batch : {b_name}</b></blockquote>")
            if "/d" not in raw_text7:
                await bot.send_message(chat_id=m.chat.id, text=f"<blockquote><b><i>🎯Target Batch : {b_name}</i></b></blockquote>\n\n🔄 Your Task is under processing, please check your Set Channel📱. Once your task is complete, I will inform you 📩")
                await bot.send_message(chat_id=m.chat.id, text=f"<blockquote><b><i>🎯Target Batch : {b_name}</i></b></blockquote>\n\n🔄 Your Task is under processing, please check your Set Channel📱. Once your task is complete, I will inform you 📩")
                await bot.pin_chat_message(channel_id, batch_message.id)
                message_id = batch_message.id + 1
                await bot.delete_messages(channel_id, message_id)
                await bot.pin_chat_message(channel_id, message_id)
        else:
             if "/d" not in raw_text7:
                await bot.send_message(chat_id=m.chat.id, text=f"<blockquote><b><i>🎯Target Batch : {b_name}</i></b></blockquote>\n\n🔄 Your Task is under processing, please check your Set Channel📱. Once your task is complete, I will inform you 📩")
    except Exception as e:
        await m.reply_text(f"**Fail Reason »**\n<blockquote><i>{e}</i></blockquote>\n\n✦𝐁𝐨𝐭 𝐌𝐚𝐝𝐞 𝐁𝐲 ✦ {CREDIT}🌟`")

    failed_count = 0
    count =int(raw_text)    
    arg = int(raw_text)
    try:
        results = await process_links(
            client=bot,
            message=m,
            links=links,
            start_index=int(raw_text),
            batch_name=b_name,
            resolution=raw_text2,
            watermark=watermark,
            credit=raw_text3,
            token=raw_text4,
            thumbnail=thumb,
            channel_id=channel_id
        )
        failed_count = results["failed"]
    except Exception as e:
        await m.reply_text(str(e))
        time.sleep(2)
        failed_count = len(links) - int(raw_text)
    success_count = len(links) - failed_count
    video_count = v2_count + mpd_count + m3u8_count + yt_count + drm_count + zip_count + other_count
    if raw_text7 == "/d":
        await bot.send_message(
    channel_id,
    (
        "<b>📬 ᴘʀᴏᴄᴇꜱꜱ ᴄᴏᴍᴘʟᴇᴛᴇᴅ</b>\n\n"
        "<blockquote><b>📚 ʙᴀᴛᴄʜ ɴᴀᴍᴇ :</b> "
        f"{b_name}</blockquote>\n"
        
        "╭────────────────\n"
        f"├ 🖇️ ᴛᴏᴛᴀʟ ᴜʀʟꜱ : <code>{len(links)}</code>\n"
        f"├ ✅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟ : <code>{success_count}</code>\n"
        f"├ ❌ ꜰᴀɪʟᴇᴅ : <code>{failed_count}</code>\n"
        "╰────────────────\n\n"

        "╭──────── 📦 ᴄᴀᴛᴇɢᴏʀʏ ────────\n"
        f"├ 🎞️ ᴠɪᴅᴇᴏꜱ : <code>{video_count}</code>\n"
        f"├ 📑 ᴘᴅꜰꜱ : <code>{pdf_count}</code>\n"
        f"├ 🖼️ ɪᴍᴀɢᴇꜱ : <code>{img_count}</code>\n"
        "╰────────────────────────────\n\n"
        
        "<i>ᴇxᴛʀᴀᴄᴛᴇᴅ ʙʏ ᴡɪᴢᴀʀᴅ ʙᴏᴛꜱ 🤖</i>"
    )
)

    else:
        await bot.send_message(channel_id, f"<b>-┈━═.•°✅ Completed ✅°•.═━┈-</b>\n<blockquote><b>🎯Batch Name : {b_name}</b></blockquote>\n<blockquote>🔗 Total URLs: {len(links)} \n┃   ┠🔴 Total Failed URLs: {failed_count}\n┃   ┠🟢 Total Successful URLs: {success_count}\n┃   ┃   ┠🎥 Total Video URLs: {video_count}\n┃   ┃   ┠📄 Total PDF URLs: {pdf_count}\n┃   ┃   ┠📸 Total IMAGE URLs: {img_count}</blockquote>\n")
        await bot.send_message(m.chat.id, f"<blockquote><b>✅ Your Task is completed, please check your Set Channel📱</b></blockquote>")





@bot.on_message(filters.command(["batch"]) & auth_filter)
async def batch_command(client: Client, message: Message):
    await batch_handler(client, message)
@bot.on_message(filters.text & filters.private)
async def text_handler(bot: Client, m: Message):
    if m.from_user.is_bot:
        return
    links = m.text
    path = None
    match = re.search(r'https?://\S+', links)
    if match:
        link = match.group(0)
    else:
        await m.reply_text("<pre><code>Invalid link format.</code></pre>")
        return
        
    editable = await m.reply_text(f"<pre><code>**🔹Processing your link...\n🔁Please wait...⏳**</code></pre>")
    await m.delete()

    await editable.edit(f"╭━━━━❰ᴇɴᴛᴇʀ ʀᴇꜱᴏʟᴜᴛɪᴏɴ❱━━➣ \n┣━━⪼ send `144`\n┣━━⪼ send `240`\n┣━━⪼ send `360`\n┣━━⪼ send `480`\n┣━━⪼ send `720`\n┣━━⪼ send `1080`\n╰━━⌈⚡[`{CREDIT}`]⚡⌋━━➣ ")
    input2: Message = await bot.listen(editable.chat.id, filters=filters.text & filters.user(m.from_user.id))
    raw_text2 = input2.text
    quality = f"{raw_text2}p"
    await input2.delete(True)
    try:
        if raw_text2 == "144":
            res = "256x144"
        elif raw_text2 == "240":
            res = "426x240"
        elif raw_text2 == "360":
            res = "640x360"
        elif raw_text2 == "480":
            res = "854x480"
        elif raw_text2 == "720":
            res = "1280x720"
        elif raw_text2 == "1080":
            res = "1920x1080" 
        else: 
            res = "UN"
    except Exception:
            res = "UN"
    # ... rest of the function logic would continue here ...

# New Callback Handlers for the buttons
@bot.on_callback_query(filters.regex("features"))
async def features_callback(client, callback_query: CallbackQuery):
    await callback_query.answer()
    features_text = (
        "**🔥 Bot Features 🔥**\n\n"
        "• 📥 Download DRM protected videos\n"
        "• 🎬 Support for multiple video formats\n"
        "• 📱 Works with YouTube and other platforms\n"
        "• 📑 PDF download support\n"
        "• 🖼️ Image download support\n"
        "• 🎵 Audio download support\n"
        "• 📝 Text to file conversion\n"
        "• ⚙️ Customizable quality settings\n"
        "• 🎨 Custom watermark support\n"
    )
    await callback_query.message.edit_text(
        features_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]
        ])
    )

@bot.on_callback_query(filters.regex("details"))
async def details_callback(client, callback_query: CallbackQuery):
    await callback_query.answer()
    details_text = (
        "**📋 Bot Details 📋**\n\n"
        "• 🤖 Bot Name: DRM Wizard 🦋\n"
        "• 👨‍💻 Developer: IT'sGOLU.™®\n"
        "• 📱 Contact: @ITsGOLU_OWNER_BOT\n"
        "• 🔄 Version: 1.0\n"
        "• 📝 Language: Python\n"
        "• 🛠️ Framework: Pyrogram\n\n"
        "**🔐 Privacy & Security**\n\n"
        "• 🔒 Your data is secure with us\n"
        "• 🚫 We don't store your personal information\n"
        "• 🔐 End-to-end encryption for all communications\n"
    )
    await callback_query.message.edit_text(
        details_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]
        ])
    )

@bot.on_callback_query(filters.regex("back_to_start"))
async def back_to_start_callback(client, callback_query: CallbackQuery):
    await callback_query.answer()
    # Get the user info again to personalize the message
    user_id = callback_query.from_user.id
    is_authorized = db.is_user_authorized(user_id, client.me.username)
    is_admin = db.is_admin(user_id)
    
    commands_list = (
        "**>  /drm - ꜱᴛᴀʀᴛ ᴜᴘʟᴏᴀᴅɪɴɢ ᴄᴘ/ᴄᴡ ᴄᴏᴜʀꜱᴇꜱ**\n"
        "**>  /plan - ᴠɪᴇᴡ ʏᴏᴜʀ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ ᴅᴇᴛᴀɪʟꜱ**\n"
    )
    
    if is_admin:
        commands_list += (
            "\n**👑 Admin Commands**\n"
            "• /users - List all users\n"
        )
    
    await callback_query.message.edit_media(
        media=InputMediaPhoto(
            media=photologo,
            caption=f"**Mʏ ᴄᴏᴍᴍᴀɴᴅꜱ ғᴏʀ ʏᴏᴜ [{callback_query.from_user.first_name} ](tg://settings)**\n\n{commands_list}"
        ),
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("𝐈𝐓'𝐬𝐆𝐎𝐋𝐔.™®", url="https://t.me/ITsGOLU_OWNER_BOT")
            ],
            [
                InlineKeyboardButton("ғᴇᴀᴛᴜʀᴇꜱ 🪔", callback_data="features"),
                InlineKeyboardButton("ᴅᴇᴛᴀɪʟꜱ 🦋", callback_data="details")
            ]
        ])
    )

print("Bot Started...")
bot.run()
