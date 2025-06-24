import streamlit as st
from utils.auth import is_logged_in
from utils.scheduler import get_oncall_schedule, input_oncall, update_oncall, delete_oncall
from utils.file_handler import list_files
from utils.evaluator import get_evaluasi, input_evaluasi
from utils.activity_logger import log_activity
from utils.task_monitor import get_tasks, update_task_status
import os

UPLOAD_FOLDER = "asisten"  # Path folder upload

def show():
    if not is_logged_in() or st.session_state.role not in ["hr", "koordinator"]:
        st.warning("Anda tidak memiliki akses ke halaman ini.")
        return

    st.title("👥 Human Resource (HR)")
    tab1, tab2, tab3, tab4 = st.tabs([
        "📅 Jadwal Oncall",
        "📋 Evaluasi Asisten",
        "📄 Berita Acara & Nilai Asisten",
        "📌 Tugas Dari Koordinator"
    ])

    # 📅 Jadwal Oncall
    with tab1:
        st.subheader("Input Jadwal Oncall Asisten")

        nama = st.text_input("Nama Asisten", key="nama_oncall")
        hari = st.text_input("Hari Oncall", key="hari_oncall")
        divisi = st.selectbox(
            "Divisi",
            ["koordinator praktikum", "sekretaris praktikum", "bendahara praktikum",
            "human resources", "akademik praktikum", "hardware & software", "manajemen praktikum"],
            key="divisi_oncall"
        )

        if st.button("Tambah Jadwal"):
            input_oncall(hari, nama, divisi)
            log_activity(st.session_state.username, "Input Oncall", f"{nama} - {hari}")
            st.success("Jadwal oncall berhasil ditambahkan.")
            st.rerun()

        st.subheader("📋 Daftar Jadwal Oncall")
        df_oncall = get_oncall_schedule()

        if not df_oncall.empty:
            st.dataframe(df_oncall, use_container_width=True)

            st.markdown("### ✏️ Edit / ❌ Hapus Jadwal")
            selected_index = st.number_input(
                "Pilih baris (mulai dari 0)", min_value=0,
                max_value=len(df_oncall) - 1, step=1, key="edit_index"
            )

            if selected_index < len(df_oncall):
                selected_row = df_oncall.loc[selected_index]

                edit_nama = st.text_input("Edit Nama", value=selected_row["Nama Asisten"], key="edit_nama")
                edit_hari = st.text_input("Edit Hari", value=selected_row["Hari"], key="edit_hari")
                edit_divisi = st.selectbox(
                    "Edit Divisi", 
                    ["koordinator praktikum", "sekretaris praktikum", "bendahara praktikum",
                    "human resources", "akademik praktikum", "hardware & software", "manajemen praktikum"],
                    index=["koordinator praktikum", "sekretaris praktikum", "bendahara praktikum",
                        "human resources", "akademik praktikum", "hardware & software", "manajemen praktikum"].index(selected_row["Divisi"]),
                    key="edit_divisi"
                )

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 Simpan Perubahan"):
                        update_oncall(selected_index, edit_hari, edit_nama, edit_divisi)
                        log_activity(st.session_state.username, "Edit Oncall", f"{edit_nama} - {edit_hari}")
                        st.success("Jadwal berhasil diperbarui.")
                        st.rerun()

                with col2:
                    if st.button("🗑️ Hapus Jadwal"):
                        delete_oncall(selected_index)
                        log_activity(st.session_state.username, "Hapus Oncall", f"{selected_row['Nama Asisten']} - {selected_row['Hari']}")
                        st.warning("Jadwal berhasil dihapus.")
                        st.rerun()
        else:
            st.info("Belum ada jadwal oncall.")

    # 📋 Evaluasi Performa
    with tab2:
        st.subheader("Evaluasi Performa Asisten per Modul")
        nama_eval = st.text_input("Nama Asisten Evaluasi", key="nama_eval")
        modul = st.text_input("Modul Praktikum", key="modul_eval")
        komentar = st.text_area("Komentar Singkat")

        if st.button("Simpan Evaluasi"):
            input_evaluasi(nama_eval, modul, komentar)
            log_activity(st.session_state.username, "Evaluasi Asisten", f"{nama_eval} - {modul}")
            st.success("Evaluasi berhasil disimpan.")
            st.rerun()

        st.subheader("📊 Data Evaluasi Asisten")
        st.dataframe(get_evaluasi(), use_container_width=True)

    # Berita Acara & Nilai Asisten
    with tab3:
        st.subheader("📄 Lihat Berita Acara & Nilai Asisten")

        # Path folder upload
        nilai_folder = os.path.join(UPLOAD_FOLDER, "nilai")
        baa_folder = os.path.join(UPLOAD_FOLDER, "baa")

        # Daftar file
        daftar_nilai = list_files(nilai_folder)
        daftar_baa = list_files(baa_folder)

        # Fungsi menampilkan file dengan preview
        def tampilkan_file_dengan_preview(file_list, folder_label, folder_path):
            if file_list:
                st.markdown(f"### 📑 {folder_label}")
                for file in file_list:
                    filepath = os.path.join("data/dokumen", folder_path, file)
                    ext = file.split(".")[-1].lower()

                    with st.expander(f"📄 {file}"):
                        # Preview berdasarkan jenis file
                        if ext in ["png", "jpg", "jpeg"]:
                            st.image(filepath, use_container_width=True)
                        elif ext == "pdf":
                            st.components.v1.iframe(filepath, height=500)

                        # Tombol unduh
                        with open(filepath, "rb") as f:
                            st.download_button(
                                label=f"⬇️ Download {file}",
                                data=f.read(),
                                file_name=file,
                                mime="application/octet-stream",
                                key=f"download_{folder_label}_{file}"
                            )
            else:
                st.info(f"Belum ada file di folder {folder_label}.")
        # Tampilkan file nilai & BAA
        tampilkan_file_dengan_preview(daftar_nilai, "File Nilai Asisten", nilai_folder)
        tampilkan_file_dengan_preview(daftar_baa, "File BAA Asisten", baa_folder)

    # 📌 Tugas Dari Koordinator
    with tab4:
        st.subheader("📌 Daftar Tugas")
        tugas_hr = get_tasks().get("hr", [])

        if not tugas_hr:
            st.info("Belum ada tugas yang tercatat untuk human resources praktikum.")
        else:
            for idx, t in enumerate(tugas_hr):
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
                        if st.button("Ceklis", key=f"check_hr_{idx}"):
                            update_task_status("hr", idx, "selesai")
                            log_activity(st.session_state.username, "Ceklis Tugas", f"hr: {t['tugas']}")
                            st.rerun()
