import json
import os
from datetime import datetime

TASK_PATH = "data/koor/tasks.json"

os.makedirs("data/koor", exist_ok=True)

def get_tasks():
    """
    Mengambil seluruh data tugas divisi dari file JSON.
    """
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(TASK_PATH):
        return {}
    with open(TASK_PATH, "r") as f:
        return json.load(f)

def save_tasks(data):
    """
    Menyimpan data tugas ke file JSON.
    """
    with open(TASK_PATH, "w") as f:
        json.dump(data, f, indent=2)

def add_task(divisi, tugas, dibuat_oleh, tanggal, deadline):
    """
    Menambahkan tugas ke divisi tertentu.
    """
    data = get_tasks()
    if divisi not in data:
        data[divisi] = []

    task = {
        "tugas": tugas.strip(),
        "status": False,                 # dikerjakan oleh divisi
        "validasi": False,              # diverifikasi koordinator
        "dibuat_oleh": dibuat_oleh,
        "tanggal": str(tanggal),
        "deadline": str(deadline),
        "waktu": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    data[divisi].append(task)
    save_tasks(data)

def update_task_status(divisi, index, mode, **kwargs):
    """
    Memperbarui status tugas tertentu berdasarkan mode:
    - selesai: tugas dicentang oleh divisi
    - validasi: divalidasi oleh koordinator
    - edit: ubah isi tugas & deadline
    - hapus: hapus tugas dari daftar
    """
    tasks = get_tasks()
    if divisi in tasks and 0 <= index < len(tasks[divisi]):
        task = tasks[divisi][index]

        if mode == "selesai":
            task["status"] = True

        elif mode == "validasi":
            if task["status"]:  # hanya bisa divalidasi jika sudah dikerjakan
                task["validasi"] = True

        elif mode == "edit":
            task["tugas"] = kwargs.get("new_task", task["tugas"])
            task["deadline"] = str(kwargs.get("new_deadline", task["deadline"]))

        elif mode == "hapus":
            tasks[divisi].pop(index)

        save_tasks(tasks)
