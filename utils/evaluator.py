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

def cek_dokumen_baa_bap(nama, minggu, modul, folder="asisten"):
    # Format nama file
    filename = f"{nama}_Minggu{minggu}_Modul{modul}.pdf"
    baa_path = os.path.join(folder, "baa", filename)
    bap_path = os.path.join(folder, "bap", filename)

    baa_ada = os.path.exists(baa_path)
    bap_ada = os.path.exists(bap_path)
    return baa_ada, bap_ada