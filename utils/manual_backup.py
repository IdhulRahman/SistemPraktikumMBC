import os
import pickle
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# ==================== KONFIGURASI ====================
LOCAL_DATA_FOLDER = "data"
DRIVE_FOLDER_ID = "18csNjLIthZHoX66gahnoZ6D3a8KxbDb4"  # Folder tujuan di Drive
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
CLIENT_SECRET_FILE = "client_secret_1066251439820-va52ro5dl11euasch7pljcok414dclfb.apps.googleusercontent.com.json"

# ==================== AUTENTIKASI ====================
def authenticate_drive():
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    return build("drive", "v3", credentials=creds)

# ==================== CEK & UPLOAD ====================
def upload_file(service, filepath, relative_path, parent_id):
    filename = os.path.basename(filepath)

    # Cek apakah file sudah ada di folder Drive
    query = f"name='{filename}' and '{parent_id}' in parents and trashed=false"
    result = service.files().list(q=query, spaces='drive', fields='files(id)').execute()
    file_list = result.get("files", [])

    media = MediaFileUpload(filepath, resumable=True)
    if file_list:
        # Update file
        file_id = file_list[0]["id"]
        service.files().update(fileId=file_id, media_body=media).execute()
        print(f"[🔁] Diperbarui: {relative_path}")
    else:
        # Upload file baru
        file_metadata = {"name": filename, "parents": [parent_id]}
        service.files().create(body=file_metadata, media_body=media, fields="id").execute()
        print(f"[✅] Diunggah: {relative_path}")

# ==================== BACKUP FOLDER ====================
def backup_data_to_drive():
    service = authenticate_drive()
    total = 0
    for root, _, files in os.walk(LOCAL_DATA_FOLDER):
        for f in files:
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, LOCAL_DATA_FOLDER)
            try:
                upload_file(service, full_path, rel_path, DRIVE_FOLDER_ID)
                total += 1
            except Exception as e:
                print(f"[⚠️] Gagal upload {rel_path}: {e}")
    print(f"\n📦 Total file diproses: {total}")
