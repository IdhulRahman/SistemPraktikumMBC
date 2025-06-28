import streamlit as st
import os
import json
import pandas as pd
from utils.auth import is_logged_in
from utils.firebase_sync import upload_file_to_storage, sync_data_to_cloud, delete_from_storage
from utils.finance_tools import get_log_kas, input_kas
from utils.task_monitor import get_tasks, update_task_status
from utils.activity_logger import log_activity
from utils.file_handler import save_file, delete_file

# Konstanta folder
UPLOAD_GAJI_STATUS_FILE = "data/bendahara/gaji/upload_gaji_status.json"
UPLOAD_GAJI_STATUS_FILE_DIR = os.path.dirname(UPLOAD_GAJI_STATUS_FILE)
GAJI_FOLDER = "data/dokumen/bendahara/gaji"
EXCEL_FOLDER = "data/dokumen/bendahara/laporan_excel"

# Pastikan semua folder dan file penting tersedia
os.makedirs(EXCEL_FOLDER, exist_ok=True)
os.makedirs(GAJI_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_GAJI_STATUS_FILE_DIR, exist_ok=True)

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

    # ========================== TAB 1 ==========================
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
                    sync_data_to_cloud()
                    st.success("✅ Transaksi berhasil disimpan.")
                    st.rerun()
                else:
                    st.error("⚠️ Jumlah dan keterangan tidak boleh kosong.")
        else:
            st.warning("❌ Hanya bendahara dan koordinator yang dapat menginput transaksi.")

    # ========================== TAB 2 ==========================
    with tab2:
        st.subheader("📋 Riwayat Transaksi Keuangan")
        df = get_log_kas()
        if df.empty:
            st.info("ℹ️ Belum ada data transaksi kas.")
        else:
            st.dataframe(df, use_container_width=True)
            st.download_button("⬇️ Export (.csv)", df.to_csv(index=False), "log_keuangan.csv", "text/csv")

    # ========================== TAB 3 ==========================
    with tab3:
        st.subheader("📤 Upload File Excel Laporan Kas")

        if st.session_state.role in ["bendahara", "koordinator"]:
            file = st.file_uploader("Pilih file Excel (.xlsx / .xls)", type=["xlsx", "xls"])
            if file and st.button("📤 Kirim Laporan"):
                saved_path = save_file(file,subfolder="bendahara/laporan_excel")
                if saved_path:
                    log_activity(st.session_state.username, "Upload Laporan Kas", file.name)
                    sync_data_to_cloud()
                    st.success(f"✅ File '{file.name}' berhasil diupload.")
                    st.rerun()

            st.markdown("### 📂 Arsip Laporan Kas")
            laporan_folder = "data/dokumen/bendahara/laporan_excel"
            os.makedirs(laporan_folder, exist_ok=True)
            excel_files = [f for f in os.listdir(laporan_folder) if f.endswith((".xlsx", ".xls"))]

            if not excel_files:
                st.info("Belum ada file laporan kas yang diupload.")
            else:
                for file in sorted(excel_files, reverse=True):
                    file_path = os.path.join(laporan_folder, file)
                    with st.expander(f"📄 {file}"):
                        try:
                            df_excel = pd.read_excel(file_path, engine="openpyxl")
                            st.dataframe(df_excel, use_container_width=True)
                        except Exception as e:
                            st.error(f"Gagal membaca isi file: {e}")

                        if st.button("🗑️ Hapus", key=f"hapus_{file}_laporan"):

                            lokal_ok = delete_file(file, subfolder="bendahara/laporan_excel")
                            cloud_ok = delete_from_storage("bendahara/laporan_excel", file)

                            if lokal_ok or cloud_ok:
                                log_activity(st.session_state.username, "Hapus Laporan Kas", file)
                                sync_data_to_cloud()
                                st.success(f"✅ File '{file}' berhasil dihapus.")
                                st.rerun()
                            else:
                                st.error(f"Gagal menghapus file '{file}'.")

    # ========================== TAB 4 ==========================
    with tab4:
        st.subheader("🛠️ Pengaturan Upload Gaji")

        status = False
        if os.path.exists(UPLOAD_GAJI_STATUS_FILE):
            with open(UPLOAD_GAJI_STATUS_FILE) as f:
                status = json.load(f).get("aktif", False)

        opsi = st.radio("Status Upload Gaji", ["Nonaktif", "Aktif"], index=int(status), horizontal=True)

        if st.button("💾 Simpan Pengaturan"):
            new_status = {"aktif": opsi == "Aktif"}
            with open(UPLOAD_GAJI_STATUS_FILE, "w") as f:
                json.dump(new_status, f)

            rel_path = os.path.relpath(UPLOAD_GAJI_STATUS_FILE, "data").replace("\\", "/")
            upload_file_to_storage(UPLOAD_GAJI_STATUS_FILE, rel_path)

            log_activity(st.session_state.username, "Atur Upload Gaji", f"Status: {opsi}")
            sync_data_to_cloud()
            st.success(f"✅ Upload gaji diset ke **{opsi}**.")
            st.rerun()

        st.markdown("### 📄 Daftar Bukti Gaji")
        folder_gaji = "data/dokumen/bendahara/gaji"
        os.makedirs(folder_gaji, exist_ok=True)
        bukti_gaji = [f for f in os.listdir(folder_gaji) if f.endswith((".jpg", ".png", ".jpeg", ".pdf"))]

        if not bukti_gaji:
            st.info("Belum ada file bukti gaji yang diupload.")
        else:
            for file in sorted(bukti_gaji, reverse=True):
                file_path = os.path.join(folder_gaji, file)
                with st.expander(f"📄 {file}"):
                    if file.endswith((".jpg", ".jpeg", ".png")):
                        st.image(file_path, caption=file, use_container_width=True)
                    elif file.endswith(".pdf"):
                        with open(file_path, "rb") as f:
                            st.download_button(f"📥 Download {file}", f, file_name=file, mime="application/pdf")

                    if st.button("🗑️ Hapus", key=f"hapus_{file}_gaji"):
                        lokal_ok = delete_file(file, subfolder="bendahara/gaji")
                        cloud_ok = delete_from_storage("bendahara/gaji", file)

                        if lokal_ok or cloud_ok:
                            log_activity(st.session_state.username, "Hapus Bukti Gaji", file)
                            sync_data_to_cloud()
                            st.success(f"✅ File '{file}' berhasil dihapus.")
                            st.rerun()
                        else:
                            st.error(f"Gagal menghapus file '{file}'.")

        
    # ========================== TAB 5 ==========================
    with tab5:
        st.subheader("📌 Daftar Tugas")
        tugas = get_tasks().get("bendahara", [])

        if not tugas:
            st.info("Belum ada tugas untuk divisi bendahara.")
        else:
            for idx, t in enumerate(tugas):
                col1, col2 = st.columns([0.85, 0.15])
                with col1:
                    icon = "✅" if t["status"] else "🔲"
                    st.markdown(f"""
                        **{icon} {t['tugas']}**  
                        🧑‍💼 Oleh: `{t['dibuat_oleh']}`  
                        📆 Tanggal: `{t.get('tanggal', '-')}`  
                        ⏰ Deadline: `{t.get('deadline', '-')}`
                    """)
                    if t["status"] and not t.get("validasi"):
                        st.warning("✅ Menunggu validasi koordinator.")
                    elif t.get("validasi"):
                        st.success("✔️ Sudah divalidasi")
                with col2:
                    if not t["status"] and st.session_state.role != "koordinator":
                        if st.button("Ceklis", key=f"check_bendahara_{idx}"):
                            update_task_status("bendahara", idx, "selesai")
                            log_activity(st.session_state.username, "Ceklis Tugas", f"bendahara: {t['tugas']}")
                            sync_data_to_cloud()
                            st.rerun()
