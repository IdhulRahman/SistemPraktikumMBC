from dotenv import load_dotenv
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
    Menyimpan daftar user ke file.
    """
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=2)

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
