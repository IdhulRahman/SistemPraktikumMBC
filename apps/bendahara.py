import streamlit as st
from utils.finance_tools import get_log_kas, input_kas
from utils.task_monitor import get_tasks, update_task_status
from utils.activity_logger import log_activity
from utils.auth import is_logged_in
import os
import pandas as pd
import openpyxl

EXCEL_FOLDER = "data/bendahara/laporan_excel" 

def show():
    if not is_logged_in():
        st.warning("Anda harus login untuk mengakses halaman ini.")
        return

    st.title("💰 Bendahara Praktikum")
    tab1, tab2, tab3, tab4 = st.tabs(["🧾 Input Transaksi", "📊 Log Keuangan", "📤 Upload Laporan Kas", "📌 Tugas Dari Koordinator"])

    # 🧾 Tab Input Transaksi
    with tab1:
        st.subheader("📥 Form Input Transaksi Kas")

        if st.session_state.role in ["bendahara", "koordinator"]:
            jenis = st.radio("Jenis Transaksi", ["Pemasukan", "Pengeluaran"], horizontal=True)
            col1, col2 = st.columns(2)
            with col1:
                jumlah = st.number_input("Jumlah (Rp)", min_value=0)
            with col2:
                tanggal = st.date_input("Tanggal Transaksi")

            keterangan = st.text_input("Keterangan Transaksi", placeholder="Contoh: Uang pendaftaran")

            if st.button("💾 Simpan Transaksi"):
                if jumlah > 0 and keterangan.strip():
                    input_kas(jenis, jumlah, keterangan, tanggal)
                    log_activity(st.session_state.username, f"Input {jenis}", f"{jumlah} - {keterangan}")
                    st.success("✅ Transaksi berhasil disimpan.")
                    st.rerun()
                else:
                    st.error("⚠️ Jumlah dan keterangan tidak boleh kosong.")
        else:
            st.warning("❌ Hanya bendahara dan koordinator yang dapat menginput transaksi.")

    # 📊 Tab Log Keuangan
    with tab2:
        st.subheader("📋 Riwayat Transaksi Keuangan")

        df = get_log_kas()

        if df.empty:
            st.info("ℹ️ Belum ada data transaksi kas yang tercatat.")
        else:
            st.dataframe(df, use_container_width=True)

            st.download_button(
                label="⬇️ Export Data Keuangan (.csv)",
                data=df.to_csv(index=False).encode(),
                file_name="log_keuangan.csv",
                mime="text/csv"
            )

        st.caption("📌 Log ini bersifat transparan dan dapat dilihat oleh seluruh asisten.")

    # 📤 Tab Upload Laporan Kas
    with tab3:
        st.subheader("📤 Upload File Excel Laporan Kas")

        if st.session_state.role in ["bendahara", "koordinator"]:
            file = st.file_uploader("Pilih file laporan keuangan (.xlsx / .xls)", type=["xlsx", "xls"], key="upload_excel_kas")

            if file:
                if st.button("📤 Kirim Laporan"):
                    os.makedirs(EXCEL_FOLDER, exist_ok=True)
                    file_path = os.path.join(EXCEL_FOLDER, file.name)
                    with open(file_path, "wb") as f:
                        f.write(file.read())
                    log_activity(st.session_state.username, "Upload File Excel", file.name)
                    st.success(f"✅ File '{file.name}' berhasil diupload.")
                    st.rerun()

        # Tampilkan file Excel yang tersedia
        st.markdown("### 📑 Daftar File Excel:")
        if os.path.exists(EXCEL_FOLDER):
            excel_files = [f for f in os.listdir(EXCEL_FOLDER) if f.endswith((".xlsx", ".xls"))]
        else:
            excel_files = []

        if not excel_files:
            st.info("Belum ada file Excel yang diupload.")
        else:
            for fname in excel_files:
                file_path = os.path.join(EXCEL_FOLDER, fname)

                with st.expander(f"📄 {fname}"):
                    try:
                        df_excel = pd.read_excel(file_path, engine="openpyxl")
                        st.dataframe(df_excel, use_container_width=True)
                    except Exception as e:
                        st.error(f"Gagal membaca file: {e}")

                    if st.session_state.role in ["bendahara", "koordinator"]:
                        if st.button("🗑️ Hapus File", key=f"hapus_excel_{fname}"):
                            os.remove(file_path)
                            log_activity(st.session_state.username, "Hapus File Excel", fname)
                            st.success(f"File '{fname}' berhasil dihapus.")
                            st.rerun()

    #  📌 Tab Tugas Dari Koordinator
    with tab4:
        st.subheader("📌 Daftar Tugas")
        tugas_divisi = get_tasks().get("bendahara", [])

        if not tugas_divisi:
            st.info("Belum ada tugas yang tercatat untuk bendahara.")
        else:
            for idx, t in enumerate(tugas_divisi):
                col1, col2 = st.columns([0.85, 0.15])
                with col1:
                    status_icon = "✅" if t["status"] else "🔲"
                    st.markdown(f"""
                        **{status_icon} {t['tugas']}**  
                        🧑‍💼 Oleh: `{t['dibuat_oleh']}`  
                        📆 Tanggal dibuat: `{t.get('tanggal', '-')}`  
                        ⏰ Deadline: `{t.get('deadline', '-')}`
                    """)

                    # Status validasi
                    if t.get("status") and not t.get("validasi", False):
                        st.warning("📌 Sudah diceklis, menunggu validasi koordinator.")
                    elif t.get("validasi", False):
                        st.success("✔️ Telah divalidasi")

                with col2:
                    if not t["status"] and st.session_state.role != "koordinator":
                        if st.button("Ceklis", key=f"check_bendahara_{idx}"):
                            update_task_status("bendahara", idx, "selesai")
                            log_activity(
                                st.session_state.username,
                                "Ceklis Tugas",
                                f"bendahara: {t['tugas']}"
                            )
                            st.rerun()


