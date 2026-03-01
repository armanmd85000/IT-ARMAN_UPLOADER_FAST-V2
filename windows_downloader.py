import os
import re
import sys
import json
import time
import subprocess
from urllib.parse import urlparse, parse_qs
import requests
from playwright.sync_api import sync_playwright

# ---------------------------------------------------------
# SETUP INSTRUCTIONS FOR WINDOWS:
# 1. pip install playwright requests
# 2. playwright install chromium
# 3. Close all completely open Google Chrome windows before running this!
# 4. Change CHROME_PROFILE_DIR below to match your actual Chrome profile path.
# ---------------------------------------------------------

# Replace with your actual username and profile path
CHROME_PROFILE_DIR = r"C:\Users\YOUR_USERNAME\AppData\Local\Google\Chrome\User Data"

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name)

def download_file(url, filename, headers):
    print(f"\n[+] Starting download: {filename}")
    try:
        # Use a session to persist headers
        session = requests.Session()
        session.headers.update(headers)

        # We stream the download so we don't consume all RAM
        response = session.get(url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024 * 1024 # 1 MB
        downloaded = 0

        with open(filename, 'wb') as f:
            for data in response.iter_content(block_size):
                f.write(data)
                downloaded += len(data)

                # Simple progress bar
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    sys.stdout.write(f"\rDownloading: {percent:.2f}% ({downloaded/(1024*1024):.2f}MB / {total_size/(1024*1024):.2f}MB)")
                    sys.stdout.flush()

        print(f"\n[+] Successfully downloaded {filename}")
        return True
    except Exception as e:
        print(f"\n[-] Failed to download: {e}")
        return False

def extract_drive_folder(url):
    print(f"[*] Launching Chrome using your local profile...")

    with sync_playwright() as p:
        try:
            # Launch persistent context to bypass login (uses your actual logged-in Chrome)
            context = p.chromium.launch_persistent_context(
                user_data_dir=CHROME_PROFILE_DIR,
                headless=False, # Must be visible for Google not to block it easily
                args=["--disable-blink-features=AutomationControlled"]
            )

            page = context.new_page()

            print(f"[*] Navigating to Google Drive folder...")
            page.goto(url)

            # Wait for the file list to load
            print("[*] Waiting for files to load...")
            page.wait_for_selector('div[role="row"]', timeout=30000)
            time.sleep(3) # Let the page settle

            # Get all file elements
            files = page.locator('div[role="row"]').all()

            if not files:
                print("[-] No files found or could not parse the folder structure.")
                return

            print(f"[+] Found {len(files)} items in folder.")

            os.makedirs("drive_downloads", exist_ok=True)

            for item in files:
                try:
                    # Get the file name from the aria-label
                    aria_label = item.get_attribute("aria-label", timeout=2000)
                    if not aria_label:
                        continue

                    # Extract the actual name before the "owned by" or other metadata
                    name_match = re.search(r'^(.*?)(?:\s+owned by|\s+last modified|\s+Shared)', aria_label)
                    file_name = name_match.group(1).strip() if name_match else aria_label.strip()
                    file_name = sanitize_filename(file_name)

                    if not file_name.endswith(('.mp4', '.mkv', '.avi', '.webm')):
                        print(f"[-] Skipping non-video file: {file_name}")
                        continue

                    print(f"\n[*] Processing video: {file_name}")

                    # Intercept network requests to catch the 'videoplayback' URL
                    media_url = []
                    request_headers = []

                    def handle_request(route, request):
                        if 'videoplayback' in request.url:
                            if not media_url: # Only grab the first one
                                media_url.append(request.url)
                                request_headers.append(request.headers)
                        route.continue_()

                    # Set up the interceptor
                    page.route("**/*", handle_request)

                    # Double click the file to open the video player
                    item.dblclick()

                    print("[*] Waiting for video player to initialize and stream to start...")
                    # Wait up to 15 seconds for the videoplayback URL to be caught
                    for _ in range(15):
                        if media_url:
                            break
                        time.sleep(1)

                    # Remove the interceptor so it doesn't catch requests from the next video
                    page.unroute("**/*", handle_request)

                    if media_url:
                        print(f"[+] Intercepted restricted media stream URL!")
                        # Download the file using the captured URL and the exact headers Chrome used
                        filepath = os.path.join("drive_downloads", file_name)

                        # Fix extension if missing
                        if '.' not in file_name[-5:]:
                            filepath += ".mp4"

                        download_file(media_url[0], filepath, request_headers[0])
                    else:
                        print(f"[-] Failed to intercept stream for {file_name}. Is it playable?")

                    # Press ESC to close the video player and go back to the folder view
                    page.keyboard.press("Escape")
                    time.sleep(2) # Wait for animation to finish

                except Exception as inner_e:
                    print(f"[-] Error processing file {aria_label}: {inner_e}")
                    # Try to recover by pressing Escape
                    page.keyboard.press("Escape")
                    time.sleep(2)

        except Exception as e:
            print(f"[-] Fatal Error: {e}")
            print("\nDid you remember to fully close all standard Google Chrome windows before running this script?")
        finally:
            if 'context' in locals():
                context.close()

if __name__ == "__main__":
    folder_link = input("Enter the restricted Google Drive folder URL: ").strip()
    if "drive.google.com" in folder_link:
        extract_drive_folder(folder_link)
    else:
        print("Invalid Google Drive URL.")
