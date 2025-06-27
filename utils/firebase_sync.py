# utils/firebase_sync.py
import os
import json
import firebase_admin
from firebase_admin import credentials, firestore, storage

FIREBASE_CRED_PATH = "data/firebase_cred.json"
FIREBASE_BUCKET_NAME = "praktikummbc.firebasestorage.app"  # Ganti sesuai milikmu

firebase_initialized = False
db, bucket = None, None

def init_firebase():
    global firebase_initialized, db, bucket

    if firebase_initialized or not os.path.exists(FIREBASE_CRED_PATH):
        return

    try:
        cred = credentials.Certificate(FIREBASE_CRED_PATH)
        firebase_admin.initialize_app(cred, {
            "storageBucket": FIREBASE_BUCKET_NAME
        })
        db = firestore.client()
        bucket = storage.bucket()
        firebase_initialized = True
        print("✅ Firebase initialized.")
    except Exception as e:
        print(f"❌ Firebase init error: {e}")

def upload_file_to_storage(local_path, cloud_path):
    """Upload file ke Firebase Storage."""
    if not firebase_initialized:
        return
    blob = bucket.blob(cloud_path)
    blob.upload_from_filename(local_path)

def download_file_from_storage(cloud_path, local_path):
    """Download file dari Firebase Storage."""
    if not firebase_initialized:
        return
    blob = bucket.blob(cloud_path)
    if blob.exists():
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        blob.download_to_filename(local_path)

def sync_data_to_cloud():
    """Sinkronisasi folder data/ ke Firebase (Firestore & Storage)."""
    init_firebase()
    if not firebase_initialized:
        return

    # Upload semua file JSON ke Firestore (kecuali firebase_cred.json)
    for root, _, files in os.walk("data"):
        for file in files:
            if file.endswith(".json") and file != "firebase_cred.json":
                local_path = os.path.join(root, file)
                cloud_key = os.path.relpath(local_path, "data").replace("\\", "/").replace(".json", "")
                try:
                    with open(local_path) as f:
                        data = json.load(f)
                    db.document(cloud_key).set(data)
                except Exception as e:
                    print(f"❌ Gagal upload ke Firestore: {file} - {e}")

    # Upload file lainnya ke Firebase Storage
    for root, _, files in os.walk("data"):
        for file in files:
            if file == "firebase_cred.json":
                continue
            if not file.endswith(".json") or file.endswith(".pdf") or file.endswith((".png", ".jpg", ".jpeg", ".xlsx", ".csv")):
                local_path = os.path.join(root, file)
                cloud_path = os.path.relpath(local_path, "data").replace("\\", "/")
                try:
                    upload_file_to_storage(local_path, cloud_path)
                except Exception as e:
                    print(f"❌ Gagal upload ke Storage: {file} - {e}")

def sync_data_from_cloud():
    """Ambil data dari Firebase ke folder lokal."""
    init_firebase()
    if not firebase_initialized:
        return

    # Ambil semua dokumen Firestore
    try:
        docs = db.collections()
        for collection in docs:
            for doc in collection.stream():
                data = doc.to_dict()
                path = os.path.join("data", collection.id, f"{doc.id}.json")
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w") as f:
                    json.dump(data, f, indent=2)
    except Exception as e:
        print(f"❌ Gagal sinkron Firestore: {e}")

    # Ambil file dari Firebase Storage
    try:
        blobs = bucket.list_blobs(prefix="")
        for blob in blobs:
            if blob.name.endswith("/"):
                continue  # skip folder virtual
            local_path = os.path.join("data", blob.name)
            download_file_from_storage(blob.name, local_path)
    except Exception as e:
        print(f"❌ Gagal sinkron Storage: {e}")
