import streamlit as st
import pandas as pd
from utils.auth import is_logged_in
from utils.task_monitor import get_tasks, update_task_status
from utils.activity_logger import log_activity
from utils.firebase_sync import sync_data_to_cloud
import json
import os
from datetime import date

FOLDER = "data/hardware"  # Folder untuk menyimpan data hardware
INVENTARIS_FILE = "data/hardware/inventaris.csv"
MAINTENANCE_FILE = "data/hardware/maintenance.csv"
LAPORAN_MAINTENANCE_FILE = "data/hardware/laporan_maintenance.csv"
os.makedirs(FOLDER, exist_ok=True)

def load_csv(path):
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()

def save_csv(path, df):
    df.to_csv(path, index=False)

def show():
    if not is_logged_in() or st.session_state.role not in ["hardware", "koordinator"]:
        st.warning("Anda tidak memiliki akses ke halaman ini.")
        return

    st.title("🛠️ Divisi Hardware & Software")

    tab1, tab2, tab3, tab4 = st.tabs([
        "🔧 Inventaris",
        "🗓️ Jadwal Maintenance",
        "🧾 Laporan Maintenance",
        "📌 Tugas Dari Koordinator"
    ])

    # === TAB 1: INVENTARIS ===
    with tab1:
        st.subheader("📦 Manajemen Inventaris Alat")

        with st.form("form_inventaris"):
            st.markdown("### ➕ Tambah Inventaris Baru")
            alat = st.text_input("Nama Alat", placeholder="Contoh: Oscilloscope")
            jumlah = st.number_input("Jumlah Alat", min_value=1, step=1)
            keterangan = st.text_area("Keterangan", placeholder="Contoh: Digunakan untuk praktikum sinyal dan sistem.")
            submit = st.form_submit_button("✅ Simpan Inventaris")

        if submit:
            if alat.strip():
                df = load_csv(INVENTARIS_FILE)
                if not df.empty and alat.lower() in df["nama"].str.lower().values:
                    df.loc[df["nama"].str.lower() == alat.lower(), "jumlah"] += jumlah
                else:
                    df = pd.concat([df, pd.DataFrame([{
                        "nama": alat,
                        "jumlah": jumlah,
                        "keterangan": keterangan
                    }])], ignore_index=True)
                save_csv(INVENTARIS_FILE, df)
                log_activity(st.session_state.username, "Tambah Inventaris", f"{alat} - {jumlah} - {keterangan}")
                st.success("✅ Inventaris berhasil disimpan.")
                sync_data_to_cloud()
                st.rerun()
            else:
                st.warning("⚠️ Nama alat tidak boleh kosong.")
        # Tampilkan daftar inventaris
        st.markdown("### 📋 Daftar Inventaris")
        df = load_csv(INVENTARIS_FILE)

        if not df.empty:
            total = df["jumlah"].sum()

            for idx, row in df.iterrows():
                with st.expander(f"🔧 {row['nama']} ({row['jumlah']} buah)"):
                    col_info, col_action = st.columns([0.85, 0.15])

                    with col_info:
                        st.markdown(
                            f"""
                            <div style="
                                padding: 10px;
                                border-left: 5px solid #4F8BF9;
                                background-color: #FAFAFA;
                                border-radius: 6px;
                                font-size: 15px;
                                color: #333;
                                margin-bottom: 10px;
                            ">
                                <p><strong>📦 Nama:</strong> {row['nama']}</p>
                                <p><strong>🔢 Jumlah:</strong> {row['jumlah']} buah</p>
                                <p><strong>📝 Keterangan:</strong> {row.get('keterangan', '-')}</p>
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )

                    with col_action:
                        if st.button("🗑️ Hapus", key=f"hapus_inventaris_{idx}"):
                            df = df.drop(idx).reset_index(drop=True)
                            save_csv(INVENTARIS_FILE, df)
                            log_activity(st.session_state.username, "Hapus Inventaris", row["nama"])
                            sync_data_to_cloud()
                            st.rerun()

            st.caption(f"📦 Total Seluruh Inventaris: **{total}** alat")
        else:
            st.info("Belum ada data inventaris.")

    # === TAB 2: JADWAL MAINTENANCE ===
    with tab2:
        st.subheader("🗓️ Input Jadwal Maintenance oleh Asisten")
        with st.form("form_maintenance"):
            asisten = st.text_input("Nama Asisten")
            modul = st.text_input("Modul yang Dicek")
            tanggal = st.date_input("Tanggal Maintenance", value=date.today())
            catatan = st.text_area("Catatan Maintenance")
            submit = st.form_submit_button("📌 Simpan Jadwal")

        if submit:
            if asisten.strip() and modul.strip():
                df = load_csv(MAINTENANCE_FILE)
                new = pd.DataFrame([{
                    "asisten": asisten.strip(),
                    "modul": modul.strip(),
                    "tanggal": str(tanggal),
                    "catatan": catatan.strip()
                }])
                df = pd.concat([df, new], ignore_index=True)
                save_csv(MAINTENANCE_FILE, df)
                log_activity(st.session_state.username, "Input Maintenance", f"{asisten} - {modul}")
                st.success("Jadwal maintenance berhasil disimpan.")
                sync_data_to_cloud()
                st.rerun()
            else:
                st.warning("Nama asisten dan modul tidak boleh kosong.")
                
        st.markdown("### 📋 Daftar Jadwal Maintenance")
        df = load_csv(MAINTENANCE_FILE)

        if not df.empty:
            for _, row in df.iterrows():
                with st.container():
                    st.markdown(f"""
                        <div style="border:1px solid #ccc; padding: 10px; border-radius: 8px; margin-bottom: 10px;">
                            <b>📅 Tanggal:</b> <code>{row['tanggal']}</code><br>
                            <b>👤 Asisten:</b> {row['asisten']}<br>
                            <b>🧪 Modul:</b> {row['modul']}<br>
                            {"<b>📝 Catatan:</b> " + row['catatan'] if row['catatan'] else ""}
                        </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("Belum ada jadwal maintenance.")


    # === TAB 3: LAPORAN MAINTENANCE ===
    with tab3:
        st.subheader("📄 Laporan Maintenance Alat (diisi Asisten)")
        with st.form("form_laporan"):
            alat = st.text_input("Nama Alat", placeholder="Contoh: Oscilloscope")
            modul = st.text_input("Modul Ke", placeholder="Contoh: 2")
            catatan = st.text_area("Catatan Maintenance")
            submit = st.form_submit_button("📝 Kirim Laporan")

        if submit:
            if alat.strip() and modul.strip() and catatan.strip():
                df = load_csv(LAPORAN_MAINTENANCE_FILE)
                new = pd.DataFrame([{
                    "tanggal": str(date.today()),
                    "asisten": st.session_state.get("username", "Unknown"),
                    "alat": alat.strip(),
                    "modul": modul.strip(),
                    "catatan": catatan.strip()
                }])
                df = pd.concat([df, new], ignore_index=True)
                save_csv(LAPORAN_MAINTENANCE_FILE, df)
                log_activity(st.session_state.username, "Kirim Laporan Maintenance", alat)
                st.success("Laporan berhasil dikirim.")
                sync_data_to_cloud()
                st.rerun()
            else:
                st.warning("Semua kolom wajib diisi.")

        with st.expander("📊 Lihat Daftar Laporan Maintenance"):
            df = load_csv(LAPORAN_MAINTENANCE_FILE)
            if not df.empty:
                df.index += 1
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Belum ada laporan yang dikirim.")

    # === TAB 4: TUGAS KOORDINATOR ===
    with tab4:
        st.subheader("📌 Daftar Tugas")
        tugas_hardware = get_tasks().get("hardware", [])

        if not tugas_hardware:
            st.info("Belum ada tugas yang tercatat untuk divisi hardware & software.")
        else:
            for idx, t in enumerate(tugas_hardware):
                col1, col2 = st.columns([0.85, 0.15])
                with col1:
                    status_icon = "✅" if t["status"] else "🔲"
                    st.markdown(f"""
                        **{status_icon} {t['tugas']}**  
                        🧑‍💼 Oleh: `{t['dibuat_oleh']}`  
                        📆 Tanggal dibuat: `{t.get('tanggal', '-')}`  
                        ⏰ Deadline: `{t.get('deadline', '-')}`
                    """)
                    # Validasi status
                    if t.get("status") and not t.get("validasi", False):
                        st.warning("📌 Sudah diceklis, menunggu validasi koordinator.")
                    elif t.get("validasi", False):
                        st.success("✔️ Telah divalidasi")

                with col2:
                    if not t["status"] and st.session_state.role != "koordinator":
                        if st.button("Ceklis", key=f"check_hardware_{idx}"):
                            update_task_status("hardware", idx, "selesai")
                            log_activity(st.session_state.username, "Ceklis Tugas", f"hardware & software: {t['tugas']}")
                            sync_data_to_cloud()
                            st.rerun()
