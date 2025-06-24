import streamlit as st
import os
import json
import datetime
import pandas as pd
from utils.auth import is_logged_in
from utils.finance_tools import get_log_kas, input_kas
from utils.task_monitor import get_tasks, update_task_status
from utils.activity_logger import log_activity

# Konstanta folder
UPLOAD_GAJI_STATUS_FILE = "data/bendahara/gaji/upload_gaji_status.json"
GAJI_FOLDER = "data/dokumen/bendahara/gaji"



# Pastikan semua folder dan file penting tersedia
os.makedirs(EXCEL_FOLDER, exist_ok=True)
os.makedirs(GAJI_FOLDER, exist_ok=True)
if not os.path.exists(UPLOAD_GAJI_STATUS_FILE):
    with open(UPLOAD_GAJI_STATUS_FILE, "w") as f:
        json.dump({"aktif": False}, f)

# Konstanta folder
UPLOAD_GAJI_STATUS_FILE = "data/bendahara/gaji/upload_gaji_status.json"
GAJI_FOLDER = "data/dokumen/bendahara/gaji"
EXCEL_FOLDER = "data/bendahara/laporan_excel"
# Pastikan semua folder dan file penting tersedia
os.makedirs(EXCEL_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_GAJI_STATUS_FILE, exist_ok=True)
os.makedirs(GAJI_FOLDER, exist_ok=True)
if not os.path.exists(UPLOAD_GAJI_STATUS_FILE):
    with open(UPLOAD_GAJI_STATUS_FILE, "w") as f:
        json.dump({"aktif": False}, f)


def show():
    if not is_logged_in():
        st.warning("Anda harus login untuk mengakses halaman ini.")
        return

    st.title("💰 Bendahara Praktikum")
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🧾 Input Transaksi", "📊 Log Keuangan",
        "📤 Upload Laporan Kas", "🛠️ Pengaturan Upload Gaji", "📌 Tugas Dari Koordinator"
    ])

    # ========================== 🧾 TAB 1: Input Transaksi ==========================
    with tab1:
        st.subheader("📥 Form Input Transaksi Kas")
        if st.session_state.role in ["bendahara", "koordinator"]:
            jenis = st.radio("Jenis Transaksi", ["Pemasukan", "Pengeluaran"], horizontal=True)
            col1, col2 = st.columns(2)
            jumlah = col1.number_input("Jumlah (Rp)", min_value=0)
            tanggal = col2.date_input("Tanggal Transaksi")
            keterangan = st.text_input("Keterangan Transaksi", placeholder="Contoh: Uang pendaftaran")

            if st.button("💾 Simpan Transaksi"):
                if jumlah > 0 and keterangan.strip():
                    input_kas(jenis, jumlah, keterangan, tanggal)
                    log_activity(st.session_state.username, f"Input {jenis}", f"{jumlah} - {keterangan}")
                    st.success("✅ Transaksi berhasil disimpan.")
                    st.rerun()
                else:
                    st.error("⚠️ Jumlah dan keterangan tidak boleh kosong.")
        else:
            st.warning("❌ Hanya bendahara dan koordinator yang dapat menginput transaksi.")

    # ========================== 📊 TAB 2: Log Keuangan ==========================
    with tab2:
        st.subheader("📋 Riwayat Transaksi Keuangan")
        df = get_log_kas()
        if df.empty:
            st.info("ℹ️ Belum ada data transaksi kas yang tercatat.")
        else:
            st.dataframe(df, use_container_width=True)
            st.download_button(
                "⬇️ Export Data Keuangan (.csv)",
                data=df.to_csv(index=False).encode(),
                file_name="log_keuangan.csv",
                mime="text/csv"
            )
        st.caption("📌 Log ini bersifat transparan dan dapat dilihat oleh seluruh asisten.")

    # ========================== 📤 TAB 3: Upload Laporan Kas ==========================
    with tab3:
        st.subheader("📤 Upload File Excel Laporan Kas")
        if st.session_state.role in ["bendahara", "koordinator"]:
            file = st.file_uploader("Pilih file laporan keuangan (.xlsx / .xls)", type=["xlsx", "xls"])
            if file and st.button("📤 Kirim Laporan"):
                file_path = os.path.join(EXCEL_FOLDER, file.name)
                with open(file_path, "wb") as f:
                    f.write(file.read())
                log_activity(st.session_state.username, "Upload File Excel", file.name)
                st.success(f"✅ File '{file.name}' berhasil diupload.")
                st.rerun()

        st.markdown("### 📑 Daftar File Excel:")
        excel_files = [f for f in os.listdir(EXCEL_FOLDER) if f.endswith((".xlsx", ".xls"))]
        if not excel_files:
            st.info("Belum ada file Excel yang diupload.")
        else:
            for fname in excel_files:
                file_path = os.path.join(EXCEL_FOLDER, fname)
                with st.expander(f"📄 {fname}"):
                    try:
                        df_excel = pd.read_excel(file_path, engine="openpyxl")
                        st.dataframe(df_excel, use_container_width=True)
                    except Exception as e:
                        st.error(f"Gagal membaca file: {e}")
                    if st.session_state.role in ["bendahara", "koordinator"]:
                        if st.button("🗑️ Hapus File", key=f"hapus_excel_{fname}"):
                            os.remove(file_path)
                            log_activity(st.session_state.username, "Hapus File Excel", fname)
                            st.success(f"✅ File '{fname}' berhasil dihapus.")
                            st.rerun()

    # ========================== 🛠️ TAB 4: Pengaturan Upload Gaji ==========================
    with tab4:
        st.subheader("🛠️ Pengaturan Upload Gaji")
    
        # === Status Upload Gaji ===
        status = False
        if os.path.exists(UPLOAD_GAJI_STATUS_FILE):
            with open(UPLOAD_GAJI_STATUS_FILE) as f:
                status = json.load(f).get("aktif", False)
    
        opsi = st.radio("Status Upload Gaji", ["Nonaktif", "Aktif"], index=1 if status else 0, horizontal=True)
    
        if st.button("💾 Simpan Pengaturan"):
            new_status = {"aktif": opsi == "Aktif"}
            with open(UPLOAD_GAJI_STATUS_FILE, "w") as f:
                json.dump(new_status, f)
            log_activity(st.session_state.username, "Atur Status Upload Gaji", f"Status: {opsi}")
            st.success(f"✅ Status upload gaji diubah menjadi **{opsi}**.")
            st.rerun()
    
        # === Daftar Upload Gaji ===
        st.markdown("### 📄 Daftar Bukti Gaji yang Telah Diupload")
    
        gaji_files = [f for f in os.listdir(GAJI_FOLDER) if f.endswith((".jpg", ".jpeg", ".png"))]
    
        if not gaji_files:
            st.info("Belum ada file bukti gaji yang diupload.")
        else:
            for f in sorted(gaji_files, reverse=True):
                with st.expander(f"🧾 {f}"):
                    file_path = os.path.join(GAJI_FOLDER, f)
                    st.image(file_path, caption=f, use_column_width=True)
    
                    col1, col2 = st.columns([0.7, 0.3])
                    with col1:
                        st.caption(f"📅 Upload Time: {datetime.datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%d %B %Y %H:%M:%S')}")
                    with col2:
                        if st.button("🗑️ Hapus", key=f"hapus_gaji_{f}"):
                            os.remove(file_path)
                            log_activity(st.session_state.username, "Hapus Bukti Gaji", f)
                            st.success(f"✅ File `{f}` berhasil dihapus.")
                            st.rerun()

    # ========================== 📌 TAB 5: Tugas Dari Koordinator ==========================
    with tab5:
        st.subheader("📌 Daftar Tugas")
        tugas_divisi = get_tasks().get("bendahara", [])

        if not tugas_divisi:
            st.info("Belum ada tugas yang tercatat untuk bendahara.")
        else:
            for idx, t in enumerate(tugas_divisi):
                col1, col2 = st.columns([0.85, 0.15])
                with col1:
                    status_icon = "✅" if t["status"] else "🔲"
                    st.markdown(f"""
                        **{status_icon} {t['tugas']}**  
                        🧑‍💼 Oleh: `{t['dibuat_oleh']}`  
                        📆 Tanggal dibuat: `{t.get('tanggal', '-')}`  
                        ⏰ Deadline: `{t.get('deadline', '-')}`
                    """)
                    if t.get("status") and not t.get("validasi", False):
                        st.warning("📌 Sudah diceklis, menunggu validasi koordinator.")
                    elif t.get("validasi", False):
                        st.success("✔️ Telah divalidasi")
                with col2:
                    if not t["status"] and st.session_state.role != "koordinator":
                        if st.button("Ceklis", key=f"check_bendahara_{idx}"):
                            update_task_status("bendahara", idx, "selesai")
                            log_activity(st.session_state.username, "Ceklis Tugas", f"bendahara: {t['tugas']}")
                            st.rerun()
