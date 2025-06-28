import streamlit as st
from utils.auth import is_logged_in, register_user
from utils.task_monitor import get_tasks, add_task, update_task_status
from utils.activity_logger import log_activity, get_all_logs
from utils.manual_backup import list_subfolders, zip_selected_folders
from utils.firebase_sync import sync_data_to_cloud
import zipfile
import plotly.express as px
import pandas as pd
import os
from datetime import datetime, timedelta
import json

def show():
    if not is_logged_in() or st.session_state.role != "koordinator":
        st.warning("Anda tidak memiliki akses ke halaman ini.")
        return

    st.title("📊 Dashboard Koordinator Praktikum")
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📅 Jadwal Mengajar Asisten",
        "📌 Tugas Divisi",
        "📈 Visualisasi Progress",
        "➕ Tambah User",
        "🗂️ Backup Manual",
        "📝 Log Aktivitas",
    ])

    # Tab 1: Jadwal Mengajar
    with tab1:
        st.subheader("📅 Jadwal Mengajar Asisten")

        path = "data/jadwal/jadwal_asisten.json"
        os.makedirs("data/jadwal", exist_ok=True)

        # === EXPANDER: FORM INPUT JADWAL ===
        with st.expander("➕ Tambah Jadwal Baru", expanded=True):
            nama_asisten = st.text_input("👤 Nama Asisten")
            kelompok = st.text_input("👥 Kelompok Praktikum", placeholder="Contoh: 55")
            minggu_ke = st.selectbox("📆 Minggu Ke-", [1, 2])
            hari = st.selectbox("🗓️ Hari", ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"])
            shift = st.selectbox("⏱️ Shift", [1, 2, 3, 4])
            nama_modul = st.selectbox("📘 Modul Ke-", [1, 2, 3])

            if st.button("✅ Simpan Jadwal"):
                if nama_asisten and nama_modul and kelompok:
                    data = {}
                    if os.path.exists(path):
                        with open(path, "r") as f:
                            data = json.load(f)

                    if nama_asisten not in data:
                        data[nama_asisten] = []

                    data[nama_asisten].append({
                        "kelompok": kelompok,
                        "minggu": minggu_ke,
                        "hari": hari,
                        "shift": shift,
                        "modul": nama_modul,
                        "verifikasi_hr_nilai": False,
                        "verifikasi_hr_baa": False
                    })

                    with open(path, "w") as f:
                        json.dump(data, f, indent=2)

                    log_activity(st.session_state.username, "Tambah Jadwal",
                                f"{nama_asisten} - Kelompok {kelompok} - Minggu {minggu_ke} - {hari} - Shift {shift} - Modul {nama_modul}")
                    st.success("✅ Jadwal berhasil disimpan!")
                    sync_data_to_cloud()
                    st.rerun()
                else:
                    st.warning("Nama asisten, kelompok, dan modul tidak boleh kosong.")

        # === EXPANDER: REKAP JADWAL ===
        with st.expander("📋 Rekap & Edit Jadwal"):
            data = {}
            if os.path.exists(path):
                with open(path, "r") as f:
                    data = json.load(f)

            all_rows = []
            for asisten, entries in data.items():
                for i, entry in enumerate(entries):
                    all_rows.append({
                        "Asisten": asisten,
                        "Kelompok": entry["kelompok"],
                        "Minggu": entry["minggu"],
                        "Hari": entry["hari"],
                        "Shift": entry["shift"],
                        "Modul": entry["modul"],
                        "Index": i
                    })

            if all_rows:
                for row in all_rows:
                    st.markdown(f"---\n🔹 **{row['Asisten']}** — Kelompok {row['Kelompok']}, Minggu {row['Minggu']}, {row['Hari']}, Shift {row['Shift']}, Modul: {row['Modul']}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✏️ Edit", key=f"edit_{row['Asisten']}_{row['Index']}"):
                            st.session_state.edit_key = (row['Asisten'], row['Index'])
                    with col2:
                        if st.button("🗑️ Hapus", key=f"hapus_{row['Asisten']}_{row['Index']}"):
                            data[row['Asisten']].pop(row['Index'])
                            if not data[row['Asisten']]:
                                del data[row['Asisten']]
                            with open(path, "w") as f:
                                json.dump(data, f, indent=2)
                            log_activity(st.session_state.username, "Hapus Jadwal", f"{row['Asisten']} - {row['Hari']} - Modul {row['Modul']}")
                            st.success("Jadwal dihapus.")
                            sync_data_to_cloud()
                            st.rerun()

                if "edit_key" in st.session_state:
                    asn, idx = st.session_state.edit_key
                    old = data[asn][idx]
                    st.info(f"✏️ Edit Jadwal: {asn} — Minggu {old['minggu']}, {old['hari']}, Shift {old['shift']}, Modul {old['modul']}, Kelompok {old['kelompok']}")
                    new_kelompok = st.text_input("Kelompok Baru", value=old["kelompok"])
                    new_minggu = st.selectbox("Minggu Baru", [1, 2], index=[1, 2].index(old["minggu"]))
                    new_hari = st.selectbox("Hari Baru", ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"],
                                            index=["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"].index(old["hari"]))
                    new_shift = st.selectbox("Shift Baru", [1, 2, 3, 4], index=[1, 2, 3, 4].index(old["shift"]))
                    new_modul = st.selectbox("Modul Baru", [1, 2, 3], index=[1, 2, 3].index(int(old["modul"])))
                    if st.button("💾 Simpan Perubahan"):
                        data[asn][idx] = {
                            "kelompok": new_kelompok,
                            "minggu": new_minggu,
                            "hari": new_hari,
                            "shift": new_shift,
                            "modul": new_modul,
                            "verifikasi_hr_nilai": False,
                            "verifikasi_hr_baa": False
                        }
                        with open(path, "w") as f:
                            json.dump(data, f, indent=2)
                        log_activity(st.session_state.username, "Edit Jadwal", f"{asn} - {new_hari} - Shift {new_shift} - Modul {new_modul}")
                        st.success("Jadwal diperbarui.")
                        st.session_state.pop("edit_key")
                        sync_data_to_cloud()
                        st.rerun()
                    if st.button("❌ Batal"):
                        st.session_state.pop("edit_key")
            else:
                st.info("Belum ada jadwal yang tercatat.")

        # === TABEL TIAP MINGGU ===
        st.markdown("---")
        st.subheader("🧾 Tabel Jadwal Tiap Minggu")

        def render_tabel_minggu(minggu_ke, rows):
            st.markdown(f"### 📅 Minggu {minggu_ke}")
            df = pd.DataFrame([r for r in rows if int(r["Minggu"]) == minggu_ke])
            if not df.empty:
                df = df[["Asisten", "Kelompok", "Hari", "Shift", "Modul"]]
                df = df.sort_values(by=["Hari", "Shift"])
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info(f"Belum ada jadwal untuk minggu {minggu_ke}.")

        render_tabel_minggu(1, all_rows)
        render_tabel_minggu(2, all_rows)

    # Tab 2: Tugas Divisi
    with tab2:
        st.subheader("📌 Tambahkan Tugas Baru untuk Divisi / Role")
        col1, col2 = st.columns(2)
        with col1:
            divisi = st.selectbox("Pilih Divisi", [
                "sekretaris", "bendahara", "hr", "akademik", "hardware", "manajemen_praktikum"
            ])
        with col2:
            tanggal = st.date_input("Tanggal Tugas", value=datetime.now().date())

        tugas = st.text_input("Tugas yang Diberikan")
        deadline = st.date_input("Deadline Tugas", value=datetime.now().date() + timedelta(days=7))

        if st.button("Tambah Tugas"):
            if tugas:
                add_task(divisi, tugas, st.session_state.username, tanggal, deadline)
                log_activity(st.session_state.username, "Tambah Tugas", f"{divisi}: {tugas} (Deadline: {deadline})")
                st.success("Tugas berhasil ditambahkan.")
                sync_data_to_cloud()
                st.rerun()
            else:
                st.warning("Tugas tidak boleh kosong.")

        st.markdown("---")
        st.subheader("📋 Progress & Manajemen Tugas")

        tasks = get_tasks()
        for d in tasks:
            st.markdown(f"### 🔸 {d.capitalize()}")
            for idx, t in enumerate(tasks[d]):
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns([0.4, 0.15, 0.15, 0.15, 0.15])
                    with col1:
                        st.write(f"- {'✅' if t['status'] else '🔲'} **{t['tugas']}**")
                        st.caption(f"📅 {t.get('tanggal', '-')}, ⏰ Deadline: {t.get('deadline', '-')}")

                    with col2:
                        if not t["status"] and st.session_state.role != "koordinator":
                            if st.button("Ceklis", key=f"cek_{d}_{idx}"):
                                update_task_status(d, idx, "selesai")
                                log_activity(st.session_state.username, "Ceklis Tugas", f"{d}: {t['tugas']}")
                                sync_data_to_cloud()
                                st.rerun()

                    with col3:
                        if st.button("Edit", key=f"edit_{d}_{idx}"):
                            st.session_state[f"edit_mode_{d}_{idx}"] = True

                    with col4:
                        if st.button("🗑️ Hapus", key=f"hapus_{d}_{idx}"):
                            update_task_status(d, idx, "hapus")
                            log_activity(st.session_state.username, "Hapus Tugas", f"{d}: {t['tugas']}")
                            st.success("Tugas dihapus.")
                            sync_data_to_cloud()
                            st.rerun()

                    with col5:
                        if t.get("status") and not t.get("validasi", False):
                            if st.session_state.role == "koordinator":
                                if st.button("✅ Validasi", key=f"validasi_{d}_{idx}"):
                                    update_task_status(d, idx, "validasi")
                                    log_activity(st.session_state.username, "Validasi Tugas", f"{d}: {t['tugas']}")
                                    st.success("Tugas divalidasi.")
                                    sync_data_to_cloud()
                                    st.rerun()
                        elif t.get("validasi", False):
                            st.success("✔️ Divalidasi")

                # 🔔 Notifikasi bawah setiap item tugas
                if t.get("status") and not t.get("validasi", False):
                    st.warning("📌 Tugas sudah diceklis namun belum divalidasi oleh koordinator.")
                    # Form Edit
                    if st.session_state.get(f"edit_mode_{d}_{idx}", False):
                        with st.expander("✏️ Edit Tugas", expanded=True):
                            new_task = st.text_input("Tugas Baru", value=t["tugas"], key=f"new_tugas_{d}_{idx}")
                            new_deadline = st.date_input("Deadline Baru", value=pd.to_datetime(t["deadline"]).date(), key=f"new_deadline_{d}_{idx}")
                            if st.button("Simpan Perubahan", key=f"simpan_{d}_{idx}"):
                                update_task_status(d, idx, "edit", new_task=new_task, new_deadline=new_deadline)
                                log_activity(st.session_state.username, "Edit Tugas", f"{d}: {new_task}")
                                st.success("Tugas berhasil diperbarui.")
                                st.session_state.pop(f"edit_mode_{d}_{idx}", None)  # otomatis keluar dari edit mode
                                sync_data_to_cloud()
                                st.rerun()

    # Tab 3: Visualisasi Progress
    with tab3:
        st.subheader("📈 Visualisasi Progress Kerja Divisi")
        summary = []
        tasks = get_tasks()
        for d, tlist in tasks.items():
            total = len(tlist)
            selesai = sum([1 for t in tlist if t.get("status") and t.get("validasi", False)])
            persen = round(selesai / total * 100, 1) if total else 0
            summary.append({"Divisi": d.capitalize(), "Selesai": selesai, "Total": total, "Persen": persen})

        if summary:
            df = pd.DataFrame(summary)
            fig = px.bar(df, x="Divisi", y="Persen", color="Divisi", text="Persen",
                         labels={"Persen": "% Selesai"}, title="Progress Kerja Divisi (%)")
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Belum ada tugas yang dicatat.")

    # Tab 4: Tambah User
    with tab4:
        st.subheader("➕ Tambah User Baru")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        role = st.selectbox("Role", [
            "koordinator", "sekretaris", "bendahara", "hr", "asisten", "akademik", "hardware", "manajemen_praktikum"
        ])
        if st.button("Daftarkan"):
            if username and password:
                register_user(username, password, role)
                log_activity(st.session_state.username, "Tambah User", f"{username} ({role})")
                sync_data_to_cloud()
                st.success(f"User `{username}` dengan role `{role}` berhasil ditambahkan.")
            else:
                st.error("Username dan password tidak boleh kosong.")

        st.markdown("---")
        st.subheader("👥 Daftar User Terdaftar")
        from utils.db import load_users  # pastikan import ini ada di atas
        users = load_users()

        if users:
            for uname, udata in users.items():
                col1, col2, col3, col4 = st.columns([0.25, 0.25, 0.25, 0.25])
                with col1:
                    st.text(f"👤 {uname}")
                with col2:
                    st.code(udata['password'], language='text')
                with col3:
                    st.text(f"🔖 {udata['role']}")
                with col4:
                    if st.button("🗑️ Hapus", key=f"hapus_user_{uname}"):
                        del users[uname]
                        with open("data/db/users.json", "w") as f:
                            json.dump(users, f, indent=2)
                        log_activity(st.session_state.username, "Hapus User", f"{uname} ({udata['role']})")
                        st.success(f"User `{uname}` berhasil dihapus.")
                        sync_data_to_cloud()
                        st.rerun()
        else:
            st.info("Belum ada user yang terdaftar.")

    # Tab 5: Backup/restore
    with tab5:
        st.subheader("🗂️ Backup Manual Folder `data/`")

        # === BUAT FILE BACKUP ===
        all_subfolders = list_subfolders()
        selected_folders = st.multiselect("📁 Pilih subfolder yang ingin dibackup:", all_subfolders)

        if selected_folders:
            if st.button("📦 Buat File ZIP"):
                with st.spinner("Sedang membuat file backup..."):
                    zip_name, zip_file = zip_selected_folders(selected_folders)
                    st.success("✅ File ZIP berhasil dibuat!")
                    st.download_button(
                        label="⬇️ Download Backup",
                        data=zip_file,
                        file_name=zip_name,
                        mime="application/zip"
                    )
        else:
            st.info("Pilih minimal satu folder untuk backup.")

        st.markdown("---")
        st.subheader("📤 Upload File ZIP Backup untuk Restore")

        uploaded_zip = st.file_uploader("Upload file backup (.zip)", type=["zip"])

        if uploaded_zip:
            if st.button("📂 Restore ZIP ke Folder data/"):
                try:
                    with st.spinner("Mengekstrak isi ZIP..."):
                        tmp_path = "restore/uploaded_backup.zip"
                        
                        # Pastikan folder sementara ada
                        os.makedirs(os.path.dirname(tmp_path), exist_ok=True)
                        
                        # Simpan file zip yang diupload ke file sementara
                        with open(tmp_path, "wb") as f:
                            f.write(uploaded_zip.read())

                        # Ekstrak ke folder `data/`
                        with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
                            zip_ref.extractall("data")

                        st.success("✅ Backup berhasil di-restore ke folder data/!")
                        log_activity(st.session_state.username, "Restore Backup", uploaded_zip.name)
                except Exception as e:
                    st.error(f"❌ Gagal mengekstrak file ZIP: {e}")

    # Tab 6: Log Aktivitas
    with tab6:
        st.subheader("📝 Log Aktivitas Semua Role")
        logs = get_all_logs()
        if logs:
            df = pd.DataFrame(logs)
            df = df[["waktu", "user", "aksi", "detail"]]
            df.columns = ["Waktu", "User", "Aksi", "Detail"]
            df = df.sort_values("Waktu", ascending=False).reset_index(drop=True)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Belum ada aktivitas yang tercatat.")

        st.caption("📌 Semua aktivitas tercatat otomatis untuk evaluasi dan transparansi.")
