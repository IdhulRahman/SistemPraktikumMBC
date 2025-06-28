from dotenv import load_dotenv
from utils.firebase_sync import upload_to_storage, db
import json
import os

USER_FILE = "data/db/users.json"
TASK_FILE = "data/db/tasks.json"

os.makedirs("data/db", exist_ok=True)

load_dotenv()

koordinator_user = os.getenv("KOORDINATOR_USER")
koordinator_password = os.getenv("KOORDINATOR_PASSWORD")

DEFAULT_USERS = {
    koordinator_user: {
        "password": koordinator_password,
        "role": "koordinator"
    }
}

def load_users():
    """
    Mengambil daftar user dari file JSON. Jika belum ada, akan dibuat default.
    """
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(USER_FILE):
        save_users(DEFAULT_USERS)
    with open(USER_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    """
    Simpan users ke file lokal, upload ke storage, dan update ke Firestore.
    """
    users_lower = {
        uname.lower(): {
            "password": data["password"],
            "role": data["role"]
        }
        for uname, data in users.items()
    }

    # 1. Simpan ke file lokal
    with open(USER_FILE, "w") as f:
        json.dump(users_lower, f, indent=2)

    # 2. Upload ke Firebase Storage (optional)
    try:
        upload_to_storage(USER_FILE, "users.json")
    except Exception as e:
        print(f"⚠️ Gagal upload users.json ke Storage: {e}")

    # 3. Simpan juga ke Firestore (misal dalam koleksi "auth")
    try:
        for uname, data in users_lower.items():
            db.collection("auth").document(uname).set(data)
    except Exception as e:
        print(f"⚠️ Gagal upload users ke Firestore: {e}")

def load_tasks():
    """
    Mengambil data tugas per divisi.
    """
    if not os.path.exists(TASK_FILE):
        return {}
    with open(TASK_FILE, "r") as f:
        return json.load(f)

def save_tasks(tasks):
    """
    Menyimpan data tugas ke file.
    """
    os.makedirs("data", exist_ok=True)
    with open(TASK_FILE, "w") as f:
        json.dump(tasks, f, indent=2)
