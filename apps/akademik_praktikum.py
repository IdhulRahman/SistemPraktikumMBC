import streamlit as st
from utils.auth import is_logged_in
from utils.file_handler import save_file, list_files, delete_file
from utils.activity_logger import log_activity
from utils.task_monitor import get_tasks, update_task_status
from utils.firebase_sync import sync_data_to_cloud

def tampilkan_file_dengan_opsi(file_list, subfolder, label_folder):
    if not file_list:
        st.info(f"Tidak ada file dalam {label_folder}.")
        return

    st.markdown(f"### 📂 Daftar {label_folder}")
    for i, file in enumerate(file_list):
        with st.expander(f"📄 {file}"):
            col1, col2 = st.columns([0.7, 0.3])
            with col1:
                st.markdown(f"Nama File: `{file}`")
            with col2:
                tombol_key = f"{label_folder}_hapus_{i}"
                if st.button("🗑️ Hapus", key=tombol_key):
                    if delete_file(file, subfolder=subfolder):
                        log_activity(st.session_state.username, f"Hapus {label_folder}", file)
                        st.success(f"{label_folder} '{file}' berhasil dihapus.")
                        sync_data_to_cloud()
                        st.rerun()
                    else:
                        st.error(f"Gagal menghapus {label_folder} '{file}'.")

def show():
    if not is_logged_in() or st.session_state.role not in ["akademik", "koordinator"]:
        st.warning("Anda tidak memiliki akses ke halaman ini.")
        return

    st.title("📖 Divisi Akademik Praktikum")
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📚 Modul Praktikum", 
        "📝 Soal TP & TA", 
        "📓 Jurnal Praktikum",
        "📊 Materi PPT", 
        "📌 Tugas Dari Koordinator"
    ])

    # === Tab 1: Modul Praktikum ===
    with tab1:
        st.subheader("📤 Upload Modul Praktikum")
        file_modul = st.file_uploader("Pilih file modul (PDF)", type=["pdf"], key="modul_praktikum")
        if file_modul:
            if st.button("📤 Kirim File Modul"):
                save_file(file_modul, subfolder="akademik/modul")
                log_activity(st.session_state.username, "Upload Modul", file_modul.name)
                st.success("✅ Modul berhasil diupload.")
                sync_data_to_cloud()
                st.rerun()

        tampilkan_file_dengan_opsi(list_files("akademik/modul"), "akademik/modul", "Modul Praktikum")

    # === Tab 2: Soal TP/TA ===
    with tab2:
        st.subheader("📤 Upload Soal Tes Pendahuluan & Akhir")
        file_soal = st.file_uploader("Pilih file soal (PDF/DOCX)", type=["pdf", "docx"], key="soal_tp_ta")
        if file_soal:
            if st.button("📤 Kirim File Soal"):
                save_file(file_soal, subfolder="akademik/soal")
                log_activity(st.session_state.username, "Upload Soal TP/TA", file_soal.name)
                st.success("✅ Soal berhasil diupload.")
                sync_data_to_cloud()
                st.rerun()

        tampilkan_file_dengan_opsi(list_files("akademik/soal"), "akademik/soal", "Soal TP/TA")

    # === Tab 3: Jurnal Praktikum ===
    with tab3:
        st.subheader("📤 Upload Template Jurnal Praktikum")
        file_jurnal = st.file_uploader("Pilih file jurnal (PDF)", type=["pdf"], key="jurnal_praktikum")
        if file_jurnal:
            if st.button("📤 Kirim File Jurnal"):
                save_file(file_jurnal, subfolder="akademik/jurnal")
                log_activity(st.session_state.username, "Upload Jurnal", file_jurnal.name)
                st.success("✅ Jurnal berhasil diupload.")
                sync_data_to_cloud()
                st.rerun()

        tampilkan_file_dengan_opsi(list_files("akademik/jurnal"), "akademik/jurnal", "Jurnal Praktikum")

    # === Tab 4: Materi PPT ===
    with tab4:
        st.subheader("📤 Upload Materi Praktikum (PPT)")
        file_ppt = st.file_uploader("Pilih file presentasi (PPTX/PDF)", type=["pptx", "pdf"], key="materi_ppt")
        if file_ppt:
            if st.button("📤 Kirim File PPT"):
                save_file(file_ppt, subfolder="akademik/ppt")
                log_activity(st.session_state.username, "Upload Materi PPT", file_ppt.name)
                st.success("✅ Materi berhasil diupload.")
                sync_data_to_cloud()
                st.rerun()

        tampilkan_file_dengan_opsi(list_files("akademik/ppt"), "akademik/ppt", "Materi PPT")

    # === Tab 5: Tugas dari Koordinator ===
    with tab5:
        st.subheader("📌 Daftar Tugas")
        tugas_akademik = get_tasks().get("akademik", [])

        if not tugas_akademik:
            st.info("Belum ada tugas yang tercatat untuk divisi akademik praktikum.")
        else:
            for idx, t in enumerate(tugas_akademik):
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
                        if st.button("Ceklis", key=f"check_akademik_{idx}"):
                            update_task_status("akademik", idx, "selesai")
                            log_activity(
                                st.session_state.username,
                                "Ceklis Tugas",
                                f"akademik praktikum: {t['tugas']}"
                            )
                            sync_data_to_cloud()
                            st.rerun()
