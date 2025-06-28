import os
import json
import firebase_admin
import streamlit as st
from firebase_admin import credentials, firestore, storage
from google.api_core.exceptions import GoogleAPIError

# === Inisialisasi Firebase menggunakan st.secrets ===
def initialize_firebase():
    try:
        if not firebase_admin._apps:
            cred_dict = {
                "type": st.secrets["type"],
                "project_id": st.secrets["project_id"],
                "private_key_id": st.secrets["private_key_id"],
                "private_key": st.secrets["private_key"],
                "client_email": st.secrets["client_email"],
                "client_id": st.secrets["client_id"],
                "auth_uri": st.secrets["auth_uri"],
                "token_uri": st.secrets["token_uri"],
                "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
                "client_x509_cert_url": st.secrets["client_x509_cert_url"],
                "universe_domain": st.secrets["universe_domain"]
            }

            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred, {
                "storageBucket": f"{st.secrets['project_id']}.firebasestorage.app"
            })

        print("✅ Firebase berhasil diinisialisasi.")
        return True
    except Exception as e:
        print(f"❌ Gagal inisialisasi Firebase: {e}")
        return False

# === Tes koneksi Firestore ===
def test_firestore_connection():
    try:
        db = firestore.client()
        list(db.collections())  # Trigger koneksi
        print("✅ Firestore terhubung.")
        return db
    except GoogleAPIError as e:
        print(f"❌ Gagal koneksi Firestore: {e}")
        return None

# === Tes koneksi Storage ===
def test_storage_connection():
    try:
        bucket = storage.bucket()
        list(bucket.list_blobs(page_size=1))  # Trigger koneksi
        print("✅ Storage terhubung.")
        return bucket
    except GoogleAPIError as e:
        print(f"❌ Gagal koneksi Storage: {e}")
        return None

# === Fungsi global: cek koneksi untuk Streamlit UI ===
def test_firebase_connections():
    global db, bucket
    firestore_ok = storage_ok = False

    if initialize_firebase():
        db = test_firestore_connection()
        bucket = test_storage_connection()
        firestore_ok = db is not None
        storage_ok = bucket is not None
    else:
        db = bucket = None

    return firestore_ok, storage_ok

# === Upload file ke Firebase Storage ===
def upload_to_storage(local_path, cloud_path):
    try:
        if bucket:
            blob = bucket.blob(cloud_path)
            blob.upload_from_filename(local_path)
            print(f"✅ Upload: {cloud_path}")
    except Exception as e:
        print(f"❌ Gagal upload ke Storage: {e}")

# === Download file dari Firebase Storage ===
def download_from_storage(cloud_path, local_path):
    try:
        if bucket:
            blob = bucket.blob(cloud_path)
            if blob.exists():
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                blob.download_to_filename(local_path)
                print(f"✅ Download: {cloud_path} → {local_path}")
    except Exception as e:
        print(f"❌ Gagal download dari Storage: {e}")

# === Sinkronisasi data lokal → Firebase ===
def sync_data_to_cloud():
    if not db or not bucket:
        print("❌ Firebase belum terhubung. Sinkronisasi dibatalkan.")
        return

    for root, _, files in os.walk("data"):
        for file in files:
            local_path = os.path.join(root, file)
            relative_path = os.path.relpath(local_path, "data").replace("\\", "/")

            # Upload JSON ke Firestore (kecuali users.json)
            if file.endswith(".json") and file != "users.json":
                try:
                    with open(local_path) as f:
                        data = json.load(f)

                    path_parts = relative_path.split("/")
                    if len(path_parts) >= 2:
                        collection = path_parts[-2]
                        document = os.path.splitext(path_parts[-1])[0]
                        db.collection(collection).document(document).set(data)
                except Exception as e:
                    print(f"❌ Gagal upload ke Firestore: {relative_path} => {e}")
            else:
                upload_to_storage(local_path, relative_path)

# === Sinkronisasi Firebase → data lokal ===
def sync_data_from_cloud():
    if not db or not bucket:
        print("❌ Firebase belum terhubung. Sinkronisasi dibatalkan.")
        return

    # 1. Sinkronisasi Firestore
    try:
        collections = db.collections()
        for col in collections:
            col_name = col.id
            for doc in col.stream():
                doc_data = doc.to_dict()
                os.makedirs(f"data/{col_name}", exist_ok=True)
                with open(f"data/{col_name}/{doc.id}.json", "w") as f:
                    json.dump(doc_data, f, indent=2)
        print("✅ Sinkronisasi Firestore selesai.")
    except Exception as e:
        print(f"❌ Gagal sync dari Firestore: {e}")

    # 2. Sinkronisasi file dari Storage
    try:
        blobs = bucket.list_blobs()
        for blob in blobs:
            cloud_path = blob.name
            local_path = os.path.join("data", cloud_path)

            if cloud_path == "users.json" or not cloud_path.endswith(".json"):
                download_from_storage(cloud_path, local_path)
        print("✅ Sinkronisasi Storage selesai.")
    except Exception as e:
        print(f"❌ Gagal sync dari Storage: {e}")
