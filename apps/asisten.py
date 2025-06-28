import streamlit as st
import os
import json
import datetime
import mimetypes
import pandas as pd
from utils.auth import is_logged_in
from utils.file_handler import save_file, list_files, get_file_bytes
from utils.scheduler import get_oncall_schedule, get_maintenance_schedule
from utils.activity_logger import log_activity
from utils.firebase_sync import sync_data_to_cloud

# Konstanta path
LAPORAN_MAINTENANCE_FILE = "data/hardware/laporan_maintenance.csv"
EXCEL_FOLDER = "data/dokumen/bendahara/laporan_excel"
UPLOAD_GAJI_STATUS_FILE = "data/bendahara/gaji/upload_gaji_status.json"
GAJI_FOLDER = "data/dokumen/bendahara/gaji"
os.makedirs(GAJI_FOLDER, exist_ok=True)

def show():
    if not is_logged_in() or st.session_state.role not in [
        "asisten", "koordinator", "akademik", "hardware", "manajemen_praktikum", "hr", "bendahara", "sekretaris"
    ]:
        st.warning("Anda harus login sebagai asisten atau koordinator.")
        return

    st.title("🧑‍🔧 Asisten Praktikum")
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📤 Upload", "📅 Jadwal", "📥 Dokumen",
        "🧾 Laporan Maintenance", "📋 Log Kas", "🤑 Bukti Gaji"
    ])

    # ======================== TAB 1: UPLOAD NILAI & BAA ========================
    with tab1:
        st.subheader("📤 Upload Scan Nilai & BAA")

        # === Form Input ===
        nama_asisten = st.text_input("👤 Nama Asisten", placeholder="Contoh: Andi", key="nama_asisten")
        kelompok = st.text_input("👥 Kelompok Praktikum", placeholder="Contoh: 5", key="kelompok_praktikum")
        modul_ke = st.selectbox("📘 Modul Ke", options=["1", "2", "3"], key="modul_ke")

        minggu_ke = st.selectbox("📆 Minggu Ke", options=["1", "2"], key="minggu_ke")
        hari = st.selectbox("🗓️ Hari", options=["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"], key="hari")
        shift_ke = st.selectbox("⏱️ Shift Ke", options=["1", "2", "3", "4"], key="shift_ke")

        nilai = st.file_uploader("📄 Scan Nilai Praktikum", type=["pdf", "png", "jpg", "jpeg"], key="upload_nilai")
        baa = st.file_uploader("📄 Scan BAA", type=["pdf", "png", "jpg", "jpeg"], key="upload_baa")

        # === Simpan File ===
        def save_file_with_asisten(file, subfolder, prefix):
            ext = file.name.split(".")[-1]
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            nama_bersih = nama_asisten.replace(" ", "_")
            nama_file = f"{prefix}_minggu{minggu_ke}_{hari}_shift{shift_ke}_{nama_bersih}_{timestamp}.{ext}"
            save_file(file, subfolder=subfolder, new_filename=nama_file)

        # === Submit Button ===
        if st.button("📤 Kirim File"):
            if not all([nama_asisten.strip(), kelompok.strip(), modul_ke.strip(), minggu_ke.strip(), hari.strip(), shift_ke.strip()]):
                st.error("⚠️ Lengkapi semua kolom terlebih dahulu.")
            else:
                if nilai:
                    prefix_nilai = f"nilai_kelompok_{kelompok}_modul_{modul_ke}"
                    save_file_with_asisten(nilai, "asisten/nilai", prefix_nilai)
                    log_activity(st.session_state.username, f"Upload Nilai Kelompok {kelompok}", nilai.name)
                    st.success(f"✅ Nilai Kelompok {kelompok} berhasil diupload.")
                    uploaded = True
                else:
                    st.warning("⚠️ File nilai belum diunggah.")

                if baa:
                    prefix_baa = f"baa_kelompok_{kelompok}_modul_{modul_ke}"
                    save_file_with_asisten(baa, "asisten/baa", prefix_baa)
                    log_activity(st.session_state.username, f"Upload BAA Modul {modul_ke}", baa.name)
                    st.success(f"✅ BAA Modul {modul_ke} berhasil diupload.")
                    uploaded = True
                else:
                    st.warning("⚠️ File BAA belum diunggah.")

                if uploaded:
                    sync_data_to_cloud()

    # ======================== TAB 2: JADWAL ONCALL & MAINTENANCE ========================
    with tab2:
        st.markdown("---")
        st.subheader("📘 Jadwal Mengajar Asisten")

        jadwal_path = "data/jadwal/jadwal_asisten.json"
        if os.path.exists(jadwal_path):
            with open(jadwal_path, "r") as f:
                data = json.load(f)

            if data:
                rows = []
                for asisten, items in data.items():
                    for entry in items:
                        rows.append({
                            "Asisten": asisten,
                            "Kelompok": entry.get("kelompok", "-"),
                            "Minggu": entry.get("minggu", "-"),
                            "Hari": entry.get("hari", "-"),
                            "Shift": entry.get("shift", "-"),
                            "Modul": entry.get("modul", "-")
                        })

                df_jadwal = pd.DataFrame(rows)

                if not df_jadwal.empty:
                    # === Filter berdasarkan Minggu ===
                    minggu_list = sorted(df_jadwal["Minggu"].unique())
                    filter_minggu = st.selectbox("🔎 Filter Minggu", ["Semua"] + minggu_list)

                    if filter_minggu != "Semua":
                        df_jadwal = df_jadwal[df_jadwal["Minggu"] == filter_minggu]

                    # === Tampilkan DataFrame ===
                    if not df_jadwal.empty:
                        df_jadwal = df_jadwal.sort_values(by=["Minggu", "Hari", "Shift"])
                        df_jadwal = df_jadwal[["Asisten", "Kelompok", "Minggu", "Hari", "Shift", "Modul"]]
                        st.dataframe(df_jadwal, use_container_width=True, hide_index=True)
                    else:
                        st.info("Tidak ada jadwal yang cocok dengan filter.")
                else:
                    st.info("Data jadwal kosong.")
            else:
                st.info("File jadwal ditemukan, tetapi belum berisi data.")
        else:
            st.info("Belum ada file jadwal yang tersedia.")


        st.subheader("📌 Jadwal Oncall")
        df_oncall = get_oncall_schedule()
        if not df_oncall.empty:
            st.dataframe(df_oncall, use_container_width=True)
        else:
            st.info("Belum ada jadwal oncall.")

        st.subheader("🛠️ Jadwal Maintenance Alat")
        df_maint = get_maintenance_schedule()
        if not df_maint.empty:
            st.dataframe(df_maint, use_container_width=True)
        else:
            st.info("Belum ada jadwal maintenance.")

    # ======================== TAB 3: DOWNLOAD DOKUMEN PENDUKUNG ========================
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
                    st.download_button(f"⬇️ {f}", data=file_bytes, file_name=f, mime=mime or "application/octet-stream", key=f"{kategori}_{f}")
            else:
                st.info(f"Tidak ada file untuk {kategori}.")

    # ======================== TAB 4: LAPORAN MAINTENANCE ========================
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

    # ======================== TAB 5: LOG KEUANGAN (LAPORAN KAS) ========================
    with tab5:
        st.subheader("📋 Laporan Pemasukan & Pengeluaran Kas")

        os.makedirs(EXCEL_FOLDER, exist_ok=True)
        excel_files = [f for f in os.listdir(EXCEL_FOLDER) if f.endswith((".xlsx", ".xls"))]

        if not excel_files:
            st.info("Belum ada file Excel yang tersedia.")
        else:
            for file in sorted(excel_files):
                filepath = os.path.join(EXCEL_FOLDER, file)
                with st.expander(f"📄 {file}", expanded=False):
                    try:
                        df = pd.read_excel(filepath)
                        st.dataframe(df, use_container_width=True)
                    except Exception as e:
                        st.error(f"Gagal membuka file: {e}")

    # ======================== TAB 6: UPLOAD BUKTI GAJI ========================

    with tab6:
        st.subheader("🤑 Upload Bukti Gaji (Screenshot)")
    
        status_upload = False
        if os.path.exists(UPLOAD_GAJI_STATUS_FILE):
            with open(UPLOAD_GAJI_STATUS_FILE) as f:
                status_upload = json.load(f).get("aktif", False)
    
        if status_upload:
            nama = st.text_input("Nama Lengkap", placeholder="Contoh: Andi Saputra")
            nim = st.text_input("NIM", placeholder="Contoh: 1201201234")
            bulan = st.text_input("Periode Gaji", placeholder="Contoh: Juni 2025")
    
            bukti_gaji = st.file_uploader("Unggah Bukti Gaji (jpg/png)", type=["jpg", "jpeg", "png"])
    
            if st.button("📤 Kirim Bukti Gaji"):
                if not all([nama.strip(), nim.strip(), bulan.strip(), bukti_gaji]):
                    st.error("⚠️ Lengkapi semua kolom dan file terlebih dahulu.")
                else:
                    ext = bukti_gaji.name.split(".")[-1]
                    
                    filename = f"{nama}_{nim}.{ext}"
                    save_file(bukti_gaji, subfolder="bendahara/gaji", new_filename=filename)
                    log_activity(st.session_state.username, "Upload Bukti Gaji", filename)
    
                    st.success(f"✅ Bukti gaji bulan {bulan} berhasil diupload sebagai `{filename}`.")
                    sync_data_to_cloud()

                    st.image(os.path.join(GAJI_FOLDER, filename), caption="📄 Preview Bukti Gaji", use_container_width=True)
        else:
            st.warning("📢 Upload bukti gaji belum dibuka oleh bendahara.")
