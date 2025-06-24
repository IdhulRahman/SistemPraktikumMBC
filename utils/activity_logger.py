import json
import os
from datetime import datetime
import pandas as pd

LOG_FILE = "data/log/aktivitas.json"

def log_activity(username, aksi, detail):
    """
    Mencatat aktivitas user ke file log JSON.
    """
    log = {
        "user": username,
        "aksi": aksi,
        "detail": detail,
        "waktu": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    logs = get_all_logs()
    logs.append(log)

    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)


def get_all_logs():
    """
    Mengambil semua log aktivitas sebagai list of dict.
    """
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def export_logs_csv():
    """
    Mengembalikan log aktivitas dalam format CSV bytes.
    Cocok digunakan dengan st.download_button.
    """
    logs = get_all_logs()
    if not logs:
        return b"Waktu,User,Aksi,Detail\n"
    df = pd.DataFrame(logs)
    df = df[["waktu", "user", "aksi", "detail"]]
    return df.to_csv(index=False).encode()


def get_logs_by_user(username):
    """
    Filter log berdasarkan username.
    """
    return [log for log in get_all_logs() if log["user"] == username]


def get_logs_by_action(aksi):
    """
    Filter log berdasarkan aksi tertentu.
    """
    return [log for log in get_all_logs() if log["aksi"] == aksi]
