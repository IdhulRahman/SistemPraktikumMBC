import os
import glob
from utils.firebase_sync import delete_from_cloud_storage

# Folder dasar penyimpanan dokumen
UPLOAD_FOLDER = "data/dokumen"

def save_file(uploaded_file, subfolder="", new_filename=None):
    """
    Menyimpan file upload ke subfolder tertentu.
    - Jika `new_filename` diberikan, file akan disimpan dengan nama tersebut.
    - Mengembalikan path file jika berhasil, None jika gagal.
    """
    if not uploaded_file:
        return None

    try:
        folder_path = os.path.join(UPLOAD_FOLDER, subfolder)
        os.makedirs(folder_path, exist_ok=True)

        # Pastikan hanya nama file (hindari path traversal)
        filename = os.path.basename(new_filename) if new_filename else os.path.basename(uploaded_file.name)
        file_path = os.path.join(folder_path, filename)

        with open(file_path, "wb") as f:
            f.write(uploaded_file.read())

        return file_path
    except Exception as e:
        print(f"[ERROR] Gagal menyimpan file: {e}")
        return None

def get_file_bytes(filename, subfolder=""):
    """
    Membaca file dalam bentuk byte untuk download.
    - Mengembalikan bytes atau None jika gagal.
    """
    try:
        safe_filename = os.path.basename(filename)
        file_path = os.path.join(UPLOAD_FOLDER, subfolder, safe_filename)

        with open(file_path, "rb") as f:
            return f.read()
    except Exception as e:
        print(f"[ERROR] Gagal membaca file: {e}")
        return None

def list_files(subfolder=""):
    """
    Mengembalikan daftar nama file dalam subfolder.
    - Kosong jika folder tidak ada atau tidak ada file.
    """
    try:
        folder_path = os.path.join(UPLOAD_FOLDER, subfolder)
        if not os.path.exists(folder_path):
            return []
        return sorted([
            f for f in os.listdir(folder_path)
            if os.path.isfile(os.path.join(folder_path, f))
        ])
    except Exception as e:
        print(f"[ERROR] Gagal mengambil daftar file: {e}")
        return []

def delete_file(filename, subfolder=""):
    """
    Menghapus file dari folder lokal dan Firebase Storage.
    - `filename`: nama file yang akan dihapus
    - `subfolder`: subfolder dalam data/dokumen/
    - Return True jika berhasil dihapus secara lokal (dan mencoba hapus dari cloud)
    """
    try:
        # Amankan nama file
        safe_filename = os.path.basename(filename)
        file_path = os.path.join(UPLOAD_FOLDER, subfolder, safe_filename)

        # Hapus file lokal
        if os.path.exists(file_path):
            os.remove(file_path)

            # Hapus file dari Firebase Storage
            cloud_path = os.path.join("dokumen", subfolder, safe_filename).replace("\\", "/")
            delete_from_cloud_storage(cloud_path)

            return True
    except Exception as e:
        print(f"[ERROR] Gagal menghapus file lokal/cloud: {e}")
    return False
