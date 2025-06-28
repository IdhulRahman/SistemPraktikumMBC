import os
import streamlit as st
from utils.auth import is_logged_in
from utils.file_handler import save_file, list_files, delete_file
from utils.activity_logger import log_activity
from utils.task_monitor import get_tasks, update_task_status
from utils.firebase_sync import upload_file_to_storage, delete_from_storage


def tampilkan_file_dengan_opsi(file_list, subfolder, label_folder):
    if not file_list:
        st.info(f"Tidak ada file dalam {label_folder}.")
        return

    st.markdown(f"### 📂 Daftar {label_folder}")
    for file in file_list:
        with st.expander(f"📄 {file}"):
            col1, col2 = st.columns([0.7, 0.3])
            with col1:
                st.markdown(f"Nama File: `{file}`")
            with col2:
                if st.button("🗑️ Hapus", key=f"{label_folder}_{file}_praktikum"):
                    lokal_ok = delete_file(file, subfolder=subfolder)
                    cloud_ok = delete_from_storage(subfolder, file)

                    if lokal_ok or cloud_ok:
                        log_activity(st.session_state.username, f"Hapus {label_folder}", file)
                        st.success(f"{label_folder} '{file}' berhasil dihapus.")
                        st.rerun()
                    else:
                        st.error(f"Gagal menghapus {label_folder} '{file}'.")

def show():
    if not is_logged_in() or st.session_state.role not in ["manajemen_praktikum", "koordinator"]:
        st.warning("Anda tidak memiliki akses ke halaman ini.")
        return

    st.title("📚 Divisi Manajemen Praktikum")
    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 Rubrik Penilaian",
        "📆 Rundown Praktikum",
        "📜 Aturan Asisten",
        "📌 Tugas Dari Koordinator"
    ])

    # === Tab 1: Rubrik Penilaian ===
    with tab1:
        st.subheader("📤 Upload Dokumen Rubrik Penilaian")
        file_rubrik = st.file_uploader("Pilih file rubrik (PDF/DOCX)", type=["pdf", "docx"], key="rubrik_penilaian")
        if file_rubrik and st.button("📤 Kirim File Rubrik"):
            saved_path = save_file(file_rubrik, subfolder="manajemen_praktikum/rubrik")
            if saved_path:
                relative_path = os.path.relpath(saved_path, "data").replace("\\", "/")
                upload_file_to_storage(saved_path, relative_path)
                log_activity(st.session_state.username, "Upload Rubrik Penilaian", file_rubrik.name)
                st.success("✅ Dokumen rubrik berhasil diupload.")
                st.rerun()

        tampilkan_file_dengan_opsi(
            list_files("manajemen_praktikum/rubrik"),
            "manajemen_praktikum/rubrik",
            "Rubrik Penilaian"
        )

    # === Tab 2: Rundown Praktikum ===
    with tab2:
        st.subheader("📤 Upload Rundown Praktikum")
        file_rundown = st.file_uploader("Pilih file rundown (PDF/DOCX)", type=["pdf", "docx"], key="rundown_praktikum")
        if file_rundown and st.button("📤 Kirim File Rundown"):
            saved_path = save_file(file_rundown, subfolder="manajemen_praktikum/rundown")
            if saved_path:
                relative_path = os.path.relpath(saved_path, "data").replace("\\", "/")
                upload_file_to_storage(saved_path, relative_path)
                log_activity(st.session_state.username, "Upload Rundown Praktikum", file_rundown.name)
                st.success("✅ Rundown berhasil diupload.")
                st.rerun()

        tampilkan_file_dengan_opsi(
            list_files("manajemen_praktikum/rundown"),
            "manajemen_praktikum/rundown",
            "Rundown Praktikum"
        )

    # === Tab 3: Aturan Asisten ===
    with tab3:
        st.subheader("📤 Upload Dokumen Aturan Asisten")
        file_aturan = st.file_uploader("Pilih file aturan (PDF/DOCX)", type=["pdf", "docx"], key="aturan_asisten")
        if file_aturan and st.button("📤 Kirim File Aturan"):
            saved_path = save_file(file_aturan, subfolder="manajemen_praktikum/aturan")
            if saved_path:
                relative_path = os.path.relpath(saved_path, "data").replace("\\", "/")
                upload_file_to_storage(saved_path, relative_path)
                log_activity(st.session_state.username, "Upload Aturan Asisten", file_aturan.name)
                st.success("✅ Dokumen aturan berhasil diupload.")
                st.rerun()

        tampilkan_file_dengan_opsi(
            list_files("manajemen_praktikum/aturan"),
            "manajemen_praktikum/aturan",
            "Aturan Asisten"
        )

    # === Tab 4: Tugas dari Koordinator ===
    with tab4:
        st.subheader("📌 Daftar Tugas")
        tugas_manajemen_praktikum = get_tasks().get("manajemen_praktikum", [])

        if not tugas_manajemen_praktikum:
            st.info("Belum ada tugas yang tercatat untuk divisi manajemen praktikum.")
        else:
            for idx, t in enumerate(tugas_manajemen_praktikum):
                col1, col2 = st.columns([0.85, 0.15])
                with col1:
                    status_icon = "✅" if t["status"] else "🔲"
                    st.markdown(f"""
                        **{status_icon} {t['tugas']}**  
                        🧑‍💼 Oleh: `{t['dibuat_oleh']}`  
                        📅 Tanggal: `{t.get('tanggal', '-')}`  
                        ⏰ Deadline: `{t.get('deadline', '-')}`
                    """)
                    if t.get("status") and not t.get("validasi", False):
                        st.warning("📌 Sudah diceklis, menunggu validasi koordinator.")
                    elif t.get("validasi", False):
                        st.success("✔️ Telah divalidasi")
                with col2:
                    if not t["status"] and st.session_state.role != "koordinator":
                        if st.button("Ceklis", key=f"check_manajemen_praktikum_{idx}"):
                            update_task_status("manajemen_praktikum", idx, "selesai")
                            log_activity(
                                st.session_state.username,
                                "Ceklis Tugas",
                                f"manajemen praktikum: {t['tugas']}"
                            )
                            st.rerun()
