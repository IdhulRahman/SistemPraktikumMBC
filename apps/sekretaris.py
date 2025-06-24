import streamlit as st
from utils.auth import is_logged_in
from utils.file_handler import save_file, list_files, delete_file
from utils.notifier import check_deadline
from utils.activity_logger import log_activity
from utils.task_monitor import get_tasks, update_task_status  # ⬅️ tambahan

def show():
    if not is_logged_in() or st.session_state.role not in ["sekretaris", "koordinator"]:
        st.warning("Anda tidak memiliki akses ke halaman ini.")
        return

    st.title("📁 Sekretaris Praktikum")
    tab1, tab2, tab3= st.tabs([
        "📄 Dokumen Resmi",
        "📤 Presentasi",
        "📌 Tugas Dari Koordinator"
    ])

    # === TAB 1: DOKUMEN RESMI ===
    with tab1:
        st.subheader("Upload Dokumen Resmi (LRJ, Surat, Berita Acara, TOT)")

        dokumen = st.file_uploader("Pilih file dokumen resmi", type=["pdf", "docx"], key="dokumen_resmi")
        if dokumen:
            if st.button("📤 Kirim Dokumen Resmi"):
                path = save_file(dokumen, subfolder="sekretaris/resmi")
                log_activity(st.session_state.username, "Upload Dokumen Resmi", dokumen.name)
                st.success(f"📄 Dokumen '{dokumen.name}' berhasil diunggah.")
                st.rerun()

        st.subheader("📂 Arsip Dokumen Resmi")
        resmi_files = list_files("sekretaris/resmi")
        for file in resmi_files:
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                st.write(f"📄 {file}")
            with col2:
                if st.button("🗑️ Hapus", key=f"hapus_{file}_resmi"):
                    if delete_file(file, "sekretaris/resmi"):
                        log_activity(st.session_state.username, "Hapus Dokumen Resmi", file)
                        st.success(f"File '{file}' berhasil dihapus.")
                        st.rerun()

    # === TAB 2: PRESENTASI ===
    with tab2:
        st.subheader("Upload Presentasi (Rakor / Techroadmap)")

        tujuan = st.selectbox("Tujuan Presentasi", ["Rakor", "Techroadmap", "Lainnya"], key="tujuan_ppt")
        ppt = st.file_uploader("Pilih file presentasi", type=["pptx", "pdf"], key="ppt_presentasi")

        if ppt:
            if st.button("📤 Kirim File Presentasi"):
                path = save_file(ppt, subfolder="sekretaris/presentasi")
                log_activity(st.session_state.username, f"Upload Presentasi ({tujuan})", ppt.name)
                st.success(f"📊 Presentasi '{ppt.name}' untuk tujuan **{tujuan}** berhasil diunggah.")
                st.rerun()

        st.subheader("📂 Arsip Presentasi")
        ppt_files = list_files("sekretaris/presentasi")
        for file in ppt_files:
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                st.write(f"📊 {file}")
            with col2:
                if st.button("🗑️ Hapus", key=f"hapus_{file}_ppt"):
                    if delete_file(file, "sekretaris/presentasi"):
                        log_activity(st.session_state.username, "Hapus Presentasi", file)
                        st.success(f"File '{file}' berhasil dihapus.")
                        st.rerun()

    # TAB 3 - Tugas dari Koordinator
    with tab3:
        st.subheader("📌 Daftar Tugas")
        tugas_sekretaris = get_tasks().get("sekretaris", [])

        if not tugas_sekretaris:
            st.info("Belum ada tugas yang tercatat untuk sekretaris praktikum.")
        else:
            for idx, t in enumerate(tugas_sekretaris):
                col1, col2 = st.columns([0.85, 0.15])
                with col1:
                    status_icon = "✅" if t["status"] else "🔲"
                    st.markdown(f"""
                        **{status_icon} {t['tugas']}**  
                        🧑‍💼 Oleh: `{t['dibuat_oleh']}`  
                        📆 Tanggal dibuat: `{t.get('tanggal', '-')}`  
                        ⏰ Deadline: `{t.get('deadline', '-')}`
                    """)

                    # Notifikasi validasi
                    if t.get("status") and not t.get("validasi", False):
                        st.warning("📌 Sudah diceklis, menunggu validasi koordinator.")
                    elif t.get("validasi", False):
                        st.success("✔️ Telah divalidasi")

                with col2:
                    # Hanya non-koordinator yang bisa mencentang
                    if not t["status"] and st.session_state.role != "koordinator":
                        if st.button("Ceklis", key=f"check_sekretaris_{idx}"):
                            update_task_status("sekretaris", idx, "selesai")
                            log_activity(st.session_state.username, "Ceklis Tugas", f"sekretaris: {t['tugas']}")
                            st.rerun()
