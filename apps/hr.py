import streamlit as st
import pandas as pd
from utils.auth import is_logged_in
from utils.scheduler import get_oncall_schedule, input_oncall, update_oncall, delete_oncall
from utils.file_handler import list_files
from utils.evaluator import get_evaluasi, input_evaluasi
from utils.activity_logger import log_activity
from utils.task_monitor import get_tasks, update_task_status
from utils.firebase_sync import sync_data_to_cloud
import os
import json
import glob

UPLOAD_FOLDER = "asisten"  # Path folder upload
JADWAL_PATH = "data/jadwal/jadwal_asisten.json"

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

    # Tab 1: Jadwal Oncall
    with tab1:
        st.subheader("Input Jadwal Oncall Asisten")

        nama = st.text_input("Nama Asisten", key="nama_oncall")
        hari = st.text_input("Hari Oncall", key="hari_oncall")
        divisi = st.selectbox("Divisi", [
            "koordinator praktikum", "sekretaris praktikum", "bendahara praktikum",
            "human resources", "akademik praktikum", "hardware & software", "manajemen praktikum"
        ], key="divisi_oncall")

        if st.button("Tambah Jadwal"):
            input_oncall(hari, nama, divisi)
            log_activity(st.session_state.username, "Input Oncall", f"{nama} - {hari}")
            st.success("Jadwal oncall berhasil ditambahkan.")
            sync_data_to_cloud()
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
            selected_row = df_oncall.loc[selected_index]
            edit_nama = st.text_input("Edit Nama", value=selected_row["Nama Asisten"], key="edit_nama")
            edit_hari = st.text_input("Edit Hari", value=selected_row["Hari"], key="edit_hari")
            edit_divisi = st.selectbox("Edit Divisi", [
                "koordinator praktikum", "sekretaris praktikum", "bendahara praktikum",
                "human resources", "akademik praktikum", "hardware & software", "manajemen praktikum"
            ], index=0, key="edit_divisi")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Simpan Perubahan"):
                    update_oncall(selected_index, edit_hari, edit_nama, edit_divisi)
                    log_activity(st.session_state.username, "Edit Oncall", f"{edit_nama} - {edit_hari}")
                    st.success("Jadwal berhasil diperbarui.")
                    sync_data_to_cloud()
                    st.rerun()
            with col2:
                if st.button("🗑️ Hapus Jadwal"):
                    delete_oncall(selected_index)
                    log_activity(st.session_state.username, "Hapus Oncall", f"{selected_row['Nama Asisten']} - {selected_row['Hari']}")
                    st.warning("Jadwal berhasil dihapus.")
                    sync_data_to_cloud()
                    st.rerun()
        else:
            st.info("Belum ada jadwal oncall.")

    # Tab 2: Evaluasi
    with tab2:
        st.subheader("Evaluasi Performa Asisten per Modul")
        nama_eval = st.text_input("Nama Asisten Evaluasi", key="nama_eval")
        modul = st.text_input("Modul Praktikum", key="modul_eval")
        komentar = st.text_area("Komentar Singkat")

        if st.button("Simpan Evaluasi"):
            input_evaluasi(nama_eval, modul, komentar)
            log_activity(st.session_state.username, "Evaluasi Asisten", f"{nama_eval} - {modul}")
            st.success("Evaluasi berhasil disimpan.")
            sync_data_to_cloud()
            st.rerun()

        st.subheader("📊 Data Evaluasi Asisten")
        st.dataframe(get_evaluasi(), use_container_width=True)

    # Tab 3: Jadwal Mengajar Asisten
    with tab3:
        st.subheader("📘 Jadwal Mengajar Asisten")

        if not os.path.exists(JADWAL_PATH):
            st.info("Belum ada jadwal mengajar.")
        else:
            with open(JADWAL_PATH, "r") as f:
                data = json.load(f)

            def check_file_uploaded(asisten, tipe, kelompok, modul, minggu, hari, shift):
                if not all([asisten, tipe, kelompok, modul, minggu, hari, shift]):
                    return False
                folder_path = os.path.join("data/dokumen", "asisten", tipe)
                nama_asisten = asisten.replace(" ", "_")
                hari = hari.lower()
                pattern = f"{tipe}_kelompok_{kelompok}_modul_{modul}_minggu{minggu}_{hari}_shift{shift}_{nama_asisten}_*.*"
                matched_files = glob.glob(os.path.join(folder_path, pattern))
                return len(matched_files) > 0

            all_rows = []
            for asisten, entries in data.items():
                for i, entry in enumerate(entries):
                    entry.setdefault("verifikasi_hr_baa", False)
                    entry.setdefault("verifikasi_hr_nilai", False)

                    all_rows.append({
                        "Asisten": asisten,
                        "Kelompok": entry["kelompok"],
                        "Minggu": entry["minggu"],
                        "Hari": entry["hari"],
                        "Shift": entry["shift"],
                        "Modul": entry["modul"],
                        "✅ BAA": "✅" if check_file_uploaded(asisten, "baa", entry["kelompok"], entry["modul"], entry["minggu"], entry["hari"], entry["shift"]) else "❌",
                        "✅ Nilai": "✅" if check_file_uploaded(asisten, "nilai", entry["kelompok"], entry["modul"], entry["minggu"], entry["hari"], entry["shift"]) else "❌",
                        "☑️ Ceklis HR": "✅" if entry["verifikasi_hr_baa"] or entry["verifikasi_hr_nilai"] else "❌",
                        "Index": i
                    })

            df_jadwal = pd.DataFrame(all_rows)

            # === Filter ===
            if not df_jadwal.empty and "Minggu" in df_jadwal.columns and "Hari" in df_jadwal.columns:
                col1, col2 = st.columns(2)
                with col1:
                    minggu_options = ["Semua"] + sorted(df_jadwal["Minggu"].dropna().unique())
                    filter_minggu = st.selectbox("🔎 Filter Minggu", minggu_options, key="filter_minggu_hr")

                with col2:
                    hari_options = ["Semua"] + sorted(df_jadwal["Hari"].dropna().unique())
                    filter_hari = st.selectbox("🔎 Filter Hari", hari_options, key="filter_hari_hr")

                # Filter berdasarkan input
                if filter_minggu != "Semua":
                    df_jadwal = df_jadwal[df_jadwal["Minggu"] == filter_minggu]
                if filter_hari != "Semua":
                    df_jadwal = df_jadwal[df_jadwal["Hari"] == filter_hari]

                if not df_jadwal.empty:
                    st.dataframe(df_jadwal.drop(columns=["Index"]), use_container_width=True)
                else:
                    st.info("Tidak ada jadwal yang cocok.")
            else:
                st.info("Data jadwal kosong atau kolom tidak lengkap.")

            # === Verifikasi HR Manual (Tampilkan hanya yang belum diverifikasi penuh) ===
            st.markdown("---")
            st.subheader("☑️ Verifikasi Manual oleh HR")

            for asisten, entries in data.items():
                for i, entry in enumerate(entries):
                    entry.setdefault("verifikasi_hr_baa", False)
                    entry.setdefault("verifikasi_hr_nilai", False)

                    if entry["verifikasi_hr_baa"] and entry["verifikasi_hr_nilai"]:
                        continue  # skip yang sudah diverifikasi semua

                    st.markdown(
                        f"#### 🔹 {asisten} | Minggu {entry['minggu']} - {entry['hari']} - Shift {entry['shift']} - Modul {entry['modul']} (Kelompok {entry['kelompok']})"
                    )

                    val_baa = st.checkbox("☑️ Verifikasi BAA", value=entry["verifikasi_hr_baa"], key=f"hr_baa_{asisten}_{i}")
                    val_nilai = st.checkbox("☑️ Verifikasi Nilai", value=entry["verifikasi_hr_nilai"], key=f"hr_nilai_{asisten}_{i}")

                    if st.button("💾 Simpan Verifikasi", key=f"simpan_hr_{asisten}_{i}"):
                        entry["verifikasi_hr_baa"] = val_baa
                        entry["verifikasi_hr_nilai"] = val_nilai

                        with open(JADWAL_PATH, "w") as f:
                            json.dump(data, f, indent=2)
                        log_activity(st.session_state.username, "HR Verifikasi",
                                    f"{asisten} Minggu {entry['minggu']} Shift {entry['shift']}")
                        st.success("✅ Verifikasi HR berhasil disimpan.")
                        sync_data_to_cloud()
                        st.rerun()

            st.markdown("---")
            st.subheader("📄 File Nilai & Berita Acara")

        def tampilkan_file(label, folder_path):
            files = list_files(folder_path)
            if files:
                st.markdown(f"### 📂 {label}")
                for file in files:
                    filepath = os.path.join("data/dokumen", folder_path, file)
                    with st.expander(file):
                        if file.endswith((".png", ".jpg", ".jpeg")):
                            st.image(filepath)
                        elif file.endswith(".pdf"):
                            st.components.v1.iframe(filepath, height=500)
                        with open(filepath, "rb") as f:
                            st.download_button("⬇️ Download", f.read(), file_name=file)
            else:
                st.info(f"Tidak ada file di folder {label}.")

        tampilkan_file("File Nilai Asisten", os.path.join(UPLOAD_FOLDER, "nilai"))
        tampilkan_file("File BAA Asisten", os.path.join(UPLOAD_FOLDER, "baa"))


    # Tab 4: Tugas dari Koordinator
    with tab4:
        st.subheader("📌 Daftar Tugas")
        tugas_hr = get_tasks().get("hr", [])
        if not tugas_hr:
            st.info("Belum ada tugas untuk human resources.")
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
                            sync_data_to_cloud()
                            st.rerun()