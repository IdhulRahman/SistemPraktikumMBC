import os
import zipfile
import io
from datetime import datetime

DATA_FOLDER = "data"

def list_subfolders(folder=DATA_FOLDER):
    return [
        name for name in os.listdir(folder)
        if os.path.isdir(os.path.join(folder, name))
    ]

def zip_selected_folders(selected_folders, base_folder=DATA_FOLDER):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for folder in selected_folders:
            folder_path = os.path.join(base_folder, folder)
            for root, _, files in os.walk(folder_path):
                for file in files:
                    abs_path = os.path.join(root, file)
                    rel_path = os.path.relpath(abs_path, base_folder)
                    zipf.write(abs_path, rel_path)
    zip_buffer.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backup_data_{timestamp}.zip"
    return filename, zip_buffer
