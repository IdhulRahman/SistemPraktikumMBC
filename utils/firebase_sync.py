import os
import json
import firebase_admin
from firebase_admin import credentials, firestore, storage

# Hanya inisialisasi jika belum ada app
if not firebase_admin._apps:
    cred = credentials.Certificate("utils/test.json")
    firebase_admin.initialize_app(cred, {
        "storageBucket": "praktikummbc.firebasestorage.app"
    })

db = firestore.client()
bucket = storage.bucket()


def upload_file_to_storage(local_path, cloud_path):
    blob = bucket.blob(cloud_path)
    blob.upload_from_filename(local_path)

def download_file_from_storage(cloud_path, local_path):
    blob = bucket.blob(cloud_path)
    if blob.exists():
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        blob.download_to_filename(local_path)

def sync_data_to_cloud():
    for root, _, files in os.walk("data"):
        for file in files:
            local_path = os.path.join(root, file)
            relative_path = os.path.relpath(local_path, "data")

            if file.endswith(".json"):
                try:
                    with open(local_path) as f:
                        data = json.load(f)

                    # Firestore Collection = folder path (tanpa .json)
                    # Firestore Document   = nama file (tanpa .json)
                    path_parts = relative_path.replace("\\", "/").split("/")
                    if len(path_parts) >= 2:
                        collection = path_parts[-2]
                        document = os.path.splitext(path_parts[-1])[0]
                        db.collection(collection).document(document).set(data)
                except Exception as e:
                    print(f"❌ Gagal upload ke Firestore: {relative_path} => {e}")
            else:
                upload_file_to_storage(local_path, relative_path)

def sync_data_from_cloud():
    # 1. Ambil data JSON dari Firestore dan simpan sebagai file
    collections = db.collections()
    for col in collections:
        col_name = col.id
        for doc in col.stream():
            doc_data = doc.to_dict()
            os.makedirs(f"data/{col_name}", exist_ok=True)
            with open(f"data/{col_name}/{doc.id}.json", "w") as f:
                json.dump(doc_data, f, indent=2)

    # 2. Download semua file dari Storage ke dalam folder data/
    blobs = bucket.list_blobs()
    for blob in blobs:
        if not blob.name.endswith(".json"):  # Hindari file JSON double
            local_path = os.path.join("data", blob.name)
            download_file_from_storage(blob.name, local_path)
