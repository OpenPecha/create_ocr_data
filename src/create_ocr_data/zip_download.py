import io
import os
import pickle

from google.auth.transport.requests import Request  # Add this import
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from create_ocr_data.checkpoints import load_checkpoints, save_checkpoint

# The ID of the Google Drive folder from which to download ZIP files.
FOLDER_ID = "15Y-PnZBT1JtrZX1ck-RT4Hd1oWU9VA7b"

# Local directory to save the downloaded ZIP files.
DOWNLOAD_PATH = "../../data/work_zip/"


def authenticate_google_drive():
    """Authenticate and return a Google Drive service instance."""
    creds = None
    token_pickle = "../../data/token.pickle"
    credentials_file = "../../data/drive_cred.json"
    scopes = ["https://www.googleapis.com/auth/drive.readonly"]

    if os.path.exists(token_pickle):
        with open(token_pickle, "rb") as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, scopes)
            creds = flow.run_console()

        # Save the credentials for the next run
        with open(token_pickle, "wb") as token:
            pickle.dump(creds, token)

    service = build("drive", "v3", credentials=creds)
    return service


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
    checkpoints = load_checkpoints()
    service = authenticate_google_drive()
    if not os.path.exists(DOWNLOAD_PATH):
        os.makedirs(DOWNLOAD_PATH)
    zip_files = list_zip_files(service, FOLDER_ID)
    for file in zip_files:
        if file["name"] in checkpoints:
            continue
        print(f"Downloading {file['name']}...")
        download_file(service, file["id"], file["name"], DOWNLOAD_PATH)
        save_checkpoint(file["name"])


if __name__ == "__main__":
    main()
