from datetime import datetime, date

def check_deadline(tgl_deadline: date) -> str:
    """
    Mengecek status deadline berdasarkan tanggal hari ini.

    Parameter:
        tgl_deadline (date): Tanggal deadline (bukan datetime)

    Return:
        str: Status deadline dengan ikon
    """
    today = datetime.today().date()

    if not isinstance(tgl_deadline, date):
        return "❓ Format tanggal tidak valid"

    delta = (tgl_deadline - today).days

    if delta < 0:
        return f"❌ Lewat deadline ({abs(delta)} hari yang lalu)"
    elif delta == 0:
        return "⚠️ Deadline hari ini!"
    elif delta <= 3:
        return f"⚠️ Tinggal {delta} hari lagi"
    else:
        return f"✅ Masih {delta} hari lagi"
