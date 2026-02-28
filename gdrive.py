import os
import json
import logging
import io
import asyncio
from google.oauth2.service_account import Credentials
from google.oauth2.credentials import Credentials as UserCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

class DriveAPI:
    def __init__(self):
        self.service = self._authenticate()

    def _authenticate(self):
        # 1. Try to use a User Token (OAuth2) first. This allows access to restricted folders
        # shared ONLY with the user's actual email address.
        user_token_json = os.environ.get('GDRIVE_USER_TOKEN')
        if user_token_json:
            try:
                creds_dict = json.loads(user_token_json)
                creds = UserCredentials.from_authorized_user_info(creds_dict, SCOPES)
                service = build('drive', 'v3', credentials=creds)
                logging.info("Authenticated using GDRIVE_USER_TOKEN (User OAuth2).")
                return service
            except Exception as e:
                logging.error(f"Failed to authenticate with User Token: {e}")

        # 2. Fallback to Service Account credentials (good for public/shared drives, but not restricted private folders)
        creds_json = os.environ.get('GDRIVE_CREDENTIALS')
        if not creds_json:
            logging.warning("GDRIVE_CREDENTIALS environment variable not found. Will try to use credentials.json file.")
            if os.path.exists('credentials.json'):
                with open('credentials.json', 'r') as f:
                    creds_json = f.read()
            else:
                logging.error("No Google Drive credentials found. Please set GDRIVE_USER_TOKEN or GDRIVE_CREDENTIALS env var.")
                return None

        try:
            creds_dict = json.loads(creds_json)
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
            service = build('drive', 'v3', credentials=creds)
            logging.info("Authenticated using GDRIVE_CREDENTIALS (Service Account).")
            return service
        except Exception as e:
            logging.error(f"Failed to authenticate with Service Account: {e}")
            return None

    def extract_folder_id(self, url):
        # Extract folder ID from typical Google Drive folder URLs
        import re
        match = re.search(r'folders/([a-zA-Z0-9_-]+)', url)
        if match:
            return match.group(1)
        match = re.search(r'id=([a-zA-Z0-9_-]+)', url)
        if match:
            return match.group(1)
        return url # fallback assuming it might just be the ID

    def list_files_in_folder(self, folder_id):
        if not self.service:
            return []

        results = []
        page_token = None
        while True:
            try:
                response = self.service.files().list(
                    q=f"'{folder_id}' in parents and trashed=false",
                    spaces='drive',
                    fields='nextPageToken, files(id, name, mimeType, size)',
                    pageToken=page_token,
                    includeItemsFromAllDrives=True,
                    supportsAllDrives=True
                ).execute()
                for file in response.get('files', []):
                    results.append(file)
                page_token = response.get('nextPageToken', None)
                if page_token is None:
                    break
            except Exception as e:
                logging.error(f"An error occurred: {e}")
                break
        return results

    def get_folder_name(self, folder_id):
        if not self.service:
            return "Unknown_Folder"
        try:
            folder = self.service.files().get(
                fileId=folder_id,
                fields="name",
                supportsAllDrives=True
            ).execute()
            return folder.get('name', 'Unknown_Folder')
        except Exception as e:
            logging.error(f"An error occurred getting folder name: {e}")
            return "Unknown_Folder"

    async def traverse_folder_recursive(self, folder_id, current_path=""):
        if not self.service:
            return []

        folder_name = self.get_folder_name(folder_id)
        if current_path:
            current_path = f"{current_path}/{folder_name}"
        else:
            current_path = folder_name

        all_files = []
        items = self.list_files_in_folder(folder_id)

        for item in items:
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                # Recursive call
                sub_files = await self.traverse_folder_recursive(item['id'], current_path)
                all_files.extend(sub_files)
            else:
                item['path'] = current_path
                all_files.append(item)

        return all_files

    async def download_file(self, file_id, file_name, destination_folder, progress_callback=None):
        if not self.service:
            return None

        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)

        file_path = os.path.join(destination_folder, file_name)

        try:
            request = self.service.files().get_media(
                fileId=file_id,
                supportsAllDrives=True
            )
            loop = asyncio.get_running_loop()

            def _download_sync():
                with io.FileIO(file_path, 'wb') as fh:
                    downloader = MediaIoBaseDownload(fh, request, chunksize=1024*1024*5) # 5MB chunks
                    done = False
                    while done is False:
                        status, done = downloader.next_chunk()
                        if progress_callback and status:
                            # Run the callback in the event loop without blocking this thread
                            asyncio.run_coroutine_threadsafe(
                                progress_callback(status.progress() * 100),
                                loop
                            )

            await asyncio.to_thread(_download_sync)
            return file_path
        except Exception as e:
            logging.error(f"Error downloading file {file_name}: {e}")
            if os.path.exists(file_path):
                os.remove(file_path)
            return None
