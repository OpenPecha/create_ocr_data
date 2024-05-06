import io
import os
import pickle

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Scopes define the level of access you are requesting over the user's data.
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# Path to your OAuth 2.0 credentials.
CREDENTIALS_FILE = "../../data/drive_cred.json"

# The ID of the Google Drive folder from which to download ZIP files.
FOLDER_ID = "15Y-PnZBT1JtrZX1ck-RT4Hd1oWU9VA7b"

# Local directory to save the downloaded ZIP files.
DOWNLOAD_PATH = "../../data/work_zip/"


def authenticate_google_drive():
    """Authenticate and return a Google Drive service instance."""
    creds = None
    if os.path.exists("../../data/token.pickle"):
        with open("../../data/token.pickle", "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        with open("../../data/token.pickle", "wb") as token:
            pickle.dump(creds, token)
    return build("drive", "v3", credentials=creds)


def list_zip_files(service, folder_id):
    """List all ZIP files in the specified Google Drive folder."""
    query = f"'{folder_id}' in parents and mimeType='application/zip'"
    results = (
        service.files()
        .list(q=query, spaces="drive", fields="nextPageToken, files(id, name)")
        .execute()
    )
    return results.get("files", [])


def download_file(service, file_id, file_name, download_path):
    """Download a file from Google Drive."""
    request = service.files().get_media(fileId=file_id)
    file_path = os.path.join(download_path, file_name)
    fh = io.FileIO(file_path, "wb")
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
        print(f"Downloaded {file_name} {int(status.progress() * 100)}%.")


def main():
    service = authenticate_google_drive()
    if not os.path.exists(DOWNLOAD_PATH):
        os.makedirs(DOWNLOAD_PATH)
    zip_files = list_zip_files(service, FOLDER_ID)
    for file in zip_files:
        print(f"Downloading {file['name']}...")
        download_file(service, file["id"], file["name"], DOWNLOAD_PATH)


if __name__ == "__main__":
    main()
