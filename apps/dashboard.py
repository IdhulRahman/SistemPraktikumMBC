import streamlit as st
from utils.auth import is_logged_in, register_user
from utils.task_monitor import get_tasks, add_task, update_task_status
from utils.activity_logger import log_activity, get_all_logs
from utils.manual_backup import list_subfolders, zip_selected_folders
import plotly.express as px
import pandas as pd
import os
from datetime import datetime, timedelta

def show():
    if not is_logged_in() or st.session_state.role != "koordinator":
        st.warning("Anda tidak memiliki akses ke halaman ini.")
        return

    st.title("📊 Dashboard Koordinator Praktikum")
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "➕ Tambah User",
        "📌 Tugas Divisi",
        "📈 Visualisasi Progress",
        "🗂️ Backup Manual",
        "📝 Log Aktivitas"
    ])

    # Tab 1: Tambah User
    with tab1:
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
                st.success(f"User `{username}` dengan role `{role}` berhasil ditambahkan.")
            else:
                st.error("Username dan password tidak boleh kosong.")

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
                                st.rerun()

                    with col3:
                        if st.button("Edit", key=f"edit_{d}_{idx}"):
                            st.session_state[f"edit_mode_{d}_{idx}"] = True

                    with col4:
                        if st.button("🗑️ Hapus", key=f"hapus_{d}_{idx}"):
                            update_task_status(d, idx, "hapus")
                            log_activity(st.session_state.username, "Hapus Tugas", f"{d}: {t['tugas']}")
                            st.success("Tugas dihapus.")
                            st.rerun()

                    with col5:
                        if t.get("status") and not t.get("validasi", False):
                            if st.session_state.role == "koordinator":
                                if st.button("✅ Validasi", key=f"validasi_{d}_{idx}"):
                                    update_task_status(d, idx, "validasi")
                                    log_activity(st.session_state.username, "Validasi Tugas", f"{d}: {t['tugas']}")
                                    st.success("Tugas divalidasi.")
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

    # Tab 4: Backup Manual
    with tab4:
        st.subheader("🗂️ Backup Manual Folder `data/`")

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

    # Tab 5: Log Aktivitas
    with tab5:
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

