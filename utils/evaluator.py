import pandas as pd
import os

DATA_EVAL = "data/hr/evaluasi_asisten.csv"

os.makedirs("data/hr", exist_ok=True)

def get_evaluasi():
    """
    Mengambil seluruh data evaluasi asisten dalam bentuk DataFrame.
    """
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(DATA_EVAL):
        df = pd.DataFrame(columns=["Nama", "Modul", "Komentar"])
        df.to_csv(DATA_EVAL, index=False)
    return pd.read_csv(DATA_EVAL)

def input_evaluasi(nama, modul, komentar = ""):
    """
    Menambahkan satu record evaluasi ke file CSV.
    """
    df = get_evaluasi()
    df.loc[len(df)] = [nama.strip(), modul.strip(), komentar.strip()]
    df.to_csv(DATA_EVAL, index=False)
