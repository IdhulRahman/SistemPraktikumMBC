import streamlit as st
from utils.auth import login, logout, is_logged_in
from utils.config import PAGE_TABS_BY_ROLE
from utils.firebase_sync import sync_data_from_cloud, sync_data_to_cloud, test_firebase_connections
from utils.user_management import ganti_akun_sidebar

st.set_page_config(page_title="Sistem Manajemen Praktikum MBC", layout="wide")

def main():
    # 🔌 Cek koneksi Firebase
    firestore_ok, storage_ok = test_firebase_connections()

    with st.sidebar:
        st.subheader("🌐 Status Koneksi Firebase")
        st.markdown(f"**Firestore:** {'🟢 Terhubung' if firestore_ok else '🔴 Gagal'}")
        st.markdown(f"**Storage:** {'🟢 Terhubung' if storage_ok else '🔴 Gagal'}")

    # 🔄 Sinkronisasi awal hanya jika koneksi sukses
    if firestore_ok and storage_ok:
        sync_data_from_cloud()
    else:
        st.error("Gagal terhubung ke Firebase. Periksa kembali credential dan koneksi internet.")
        return

    if not is_logged_in():
        login()
        return

    # Sidebar Info Pengguna
    username = st.session_state.username
    role = st.session_state.role
    with st.sidebar:
        st.title("👤 Selamat datang")
        st.markdown(f"**User:** `{username}`")
        st.markdown(f"**Role:** `{role}`")

        st.markdown("---")
        ganti_akun_sidebar()

        if st.button("🚪 Logout"):
            sync_data_to_cloud()
            logout()

    # Tampilkan tab sesuai role
    if role == "koordinator":
        combined_tabs = {}
        for r_tabs in PAGE_TABS_BY_ROLE.values():
            combined_tabs.update(r_tabs)
        allowed_tabs = combined_tabs
    else:
        allowed_tabs = PAGE_TABS_BY_ROLE.get(role, {})

    if allowed_tabs:
        tab_labels = list(allowed_tabs.keys())
        tabs = st.tabs(tab_labels)
        for i, label in enumerate(tab_labels):
            with tabs[i]:
                allowed_tabs[label].show()
    else:
        st.warning("Role Anda belum memiliki halaman yang tersedia.")

if __name__ == "__main__":
    main()
