import pandas as pd
import os

DATA_PATH = "data/bendahara/log_kas.csv"
EXCEL_EXPORT_PATH = "data/bendahara/laporan_kas.xlsx"

def get_log_kas():
    """
    Mengambil seluruh log kas dari file CSV.
    """
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(DATA_PATH):
        df = pd.DataFrame(columns=["Tanggal", "Jenis", "Jumlah", "Keterangan"])
        df.to_csv(DATA_PATH, index=False)
    return pd.read_csv(DATA_PATH)

def input_kas(jenis, jumlah, keterangan, tanggal):
    """
    Menambahkan satu entri log kas baru.
    """
    df = get_log_kas()
    tanggal_str = pd.to_datetime(tanggal).strftime("%Y-%m-%d")
    df.loc[len(df)] = [tanggal_str, jenis, float(jumlah), keterangan.strip()]
    df.to_csv(DATA_PATH, index=False)

def export_laporan(df):
    """
    Mengekspor DataFrame kas ke file Excel.
    """
    os.makedirs("data", exist_ok=True)
    df.to_excel(EXCEL_EXPORT_PATH, index=False)
