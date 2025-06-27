import pandas as pd
import os
import json

ONCALL_PATH = "data/hr/jadwal_oncall.csv"
MAINTENANCE_PATH = "data/hardware/jadwal_maintenance.csv"

# === ONCALL ===

def get_oncall_schedule():
    """
    Mengambil jadwal oncall dari file CSV.
    """
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(ONCALL_PATH):
        df = pd.DataFrame(columns=["Hari", "Nama Asisten", "Divisi"])
        df.to_csv(ONCALL_PATH, index=False)
    return pd.read_csv(ONCALL_PATH)

def input_oncall(hari, nama, divisi):
    """
    Menambahkan jadwal oncall baru.
    """
    df = get_oncall_schedule()
    df.loc[len(df)] = [hari.strip(), nama.strip(), divisi.strip()]
    df.to_csv(ONCALL_PATH, index=False)

def update_oncall(index, hari, nama, divisi):
    """
    Mengedit jadwal oncall di baris tertentu.
    """
    df = get_oncall_schedule()
    if 0 <= index < len(df):
        df.at[index, "Hari"] = hari.strip()
        df.at[index, "Nama Asisten"] = nama.strip()
        df.at[index, "Divisi"] = divisi.strip()
        df.to_csv(ONCALL_PATH, index=False)

def delete_oncall(index):
    """
    Menghapus jadwal oncall di baris tertentu.
    """
    df = get_oncall_schedule()
    if 0 <= index < len(df):
        df = df.drop(index).reset_index(drop=True)
        df.to_csv(ONCALL_PATH, index=False)

# === MAINTENANCE ===

def get_maintenance_schedule():
    """
    Mengambil jadwal maintenance dari file CSV.
    """
    path = "data/hardware/maintenance.csv"
    if os.path.exists(path):
        try:
            return pd.read_csv(path)
        except Exception as e:
            print(f"Gagal membaca file CSV: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

def input_maintenance(tanggal, alat, catatan):
    """
    Menambahkan jadwal maintenance ke file CSV.
    """
    df = get_maintenance_schedule()
    tanggal_str = pd.to_datetime(tanggal).strftime("%Y-%m-%d")
    df.loc[len(df)] = [tanggal_str, alat.strip(), catatan.strip()]
    df.to_csv(MAINTENANCE_PATH, index=False)
