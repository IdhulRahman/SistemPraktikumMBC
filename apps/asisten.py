import streamlit as st
from utils.auth import is_logged_in
from utils.file_handler import save_file, list_files, get_file_bytes
from utils.scheduler import get_oncall_schedule, get_maintenance_schedule
from utils.activity_logger import log_activity
from utils.finance_tools import get_log_kas
import pandas as pd
import datetime
import os
import mimetypes

LAPORAN_MAINTENANCE_FILE = "data/hardware/laporan_maintenance.csv"
EXCEL_FOLDER = "data/bendahara/laporan_excel"

def show():
    if not is_logged_in() or st.session_state.role not in ["asisten", "koordinator", "akademik", "hardware", "manajemen_praktikum", "hr", "bendahara", "sekretaris"]:
        st.warning("Anda harus login sebagai asisten atau koordinator.")
        return

    st.title("🧑‍🔧 Asisten Praktikum")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📤 Upload", "📅 Jadwal", "📥 Dokumen", "🧾 Laporan Maintenance", "📋 Log Pemasukan & Pengeluaran Kas"])

    # === TAB 1: UPLOAD ===
    with tab1:
        st.subheader("📤 Upload Scan Nilai & BAA")

        nama_asisten = st.text_input("Nama Asisten", placeholder="Contoh: Andi", key="nama_asisten")
        kelompok = st.text_input("Kelompok Praktikum", placeholder="Contoh: 5", key="kelompok_praktikum")
        modul_ke = st.text_input("Modul Ke", placeholder="Contoh: 3", key="modul_ke")

        nilai = st.file_uploader("Scan Nilai Praktikum", type=["pdf", "png", "jpg", "jpeg"], key="upload_nilai")
        baa = st.file_uploader("Scan BAA", type=["pdf", "png", "jpg", "jpeg"], key="upload_baa")

        def save_file_with_asisten(file, subfolder, prefix):
            ext = file.name.split(".")[-1]
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            new_filename = f"{prefix}_{nama_asisten.replace(' ', '_')}_{timestamp}.{ext}"
            save_file(file, subfolder=subfolder, new_filename=new_filename)

        if st.button("📤 Kirim File"):
            if not all([nama_asisten.strip(), kelompok.strip(), modul_ke.strip()]):
                st.error("⚠️ Lengkapi semua kolom terlebih dahulu.")
            else:
                if nilai:
                    save_file_with_asisten(nilai, "asisten/nilai", f"nilai_kelompok_{kelompok}_modul_{modul_ke}")
                    log_activity(st.session_state.username, f"Upload Nilai Kelompok {kelompok}", nilai.name)
                    st.success(f"✅ Nilai Kelompok {kelompok} berhasil diupload.")
                else:
                    st.warning("⚠️ File nilai belum diunggah.")

                if baa:
                    save_file_with_asisten(baa, "asisten/baa", f"baa_modul_{modul_ke}_kelompok_{kelompok}")
                    log_activity(st.session_state.username, f"Upload BAA Modul {modul_ke}", baa.name)
                    st.success(f"✅ BAA Modul {modul_ke} berhasil diupload.")
                else:
                    st.warning("⚠️ File BAA belum diunggah.")


    # === TAB 2: JADWAL ===
    with tab2:
        st.subheader("📌 Jadwal Oncall")
        df_oncall = get_oncall_schedule()
        st.dataframe(df_oncall, use_container_width=True) if not df_oncall.empty else st.info("Belum ada jadwal oncall.")

        st.subheader("🛠️ Jadwal Maintenance Alat")
        df_maint = get_maintenance_schedule()
        st.dataframe(df_maint, use_container_width=True) if not df_maint.empty else st.info("Belum ada jadwal maintenance.")

    # === TAB 3: DOKUMEN ===
    with tab3:
        st.subheader("📥 Download Dokumen Pendukung")

        dokumen = {
            "Modul Praktikum": "akademik/modul",
            "Soal TP/TA": "akademik/soal",
            "Jurnal Praktikum": "akademik/jurnal",
            "PPT Materi": "akademik/ppt",
            "Aturan Praktikan": "manajemen_praktikum/aturan",
            "Rundown Praktikum": "manajemen_praktikum/rundown",
            "Rubrik Penilaian": "manajemen_praktikum/rubrik",
        }

        for kategori, path in dokumen.items():
            files = list_files(path)
            if files:
                st.markdown(f"### 📘 {kategori}")
                for f in files:
                    file_bytes = get_file_bytes(f, subfolder=path)
                    mime, _ = mimetypes.guess_type(f)
                    mime = mime or "application/octet-stream"
                    st.download_button(f"⬇️ {f}", data=file_bytes, file_name=f, mime=mime, key=f"download_{kategori}_{f}")
            else:
                st.info(f"Tidak ada file untuk {kategori}.")

    # === TAB 4: LAPORAN MAINTENANCE ===
    with tab4:
        st.subheader("📊 Daftar Laporan Maintenance")
        if os.path.exists(LAPORAN_MAINTENANCE_FILE):
            try:
                df = pd.read_csv(LAPORAN_MAINTENANCE_FILE)
                if not df.empty:
                    df.index += 1
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("Belum ada laporan maintenance.")
            except Exception as e:
                st.error(f"Gagal membaca file laporan: {e}")
        else:
            st.info("File laporan maintenance tidak ditemukan.")

    # === TAB 5: LOG PEMASUKAN & PENGELUARAN KAS ===
    with tab5:
        st.subheader("📋 Lihat Log Pemasukan & Pengeluaran Kas")

        if not os.path.exists(EXCEL_FOLDER):
            os.makedirs(EXCEL_FOLDER)

        excel_files = [f for f in os.listdir(EXCEL_FOLDER) if f.endswith((".xlsx", ".xls"))]

        if not excel_files:
            st.info("Belum ada file Excel yang tersedia.")
        else:
            for file in excel_files:
                filepath = os.path.join(EXCEL_FOLDER, file)
                with st.expander(f"📄 {file}", expanded=False):
                    try:
                        df = pd.read_excel(filepath)
                        st.dataframe(df, use_container_width=True)
                    except Exception as e:
                        st.error(f"Gagal membuka file: {e}")