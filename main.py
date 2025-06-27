import streamlit as st
import os
from utils.auth import login, logout, is_logged_in
from utils.config import PAGE_TABS_BY_ROLE
from utils.firebase_sync import sync_data_from_cloud, sync_data_to_cloud

st.set_page_config(page_title="Sistem Manajemen Praktikum MBC", layout="wide")

def handle_cred_upload():
    st.sidebar.subheader("📄 Upload Firebase Credential")
    uploaded_cred = st.sidebar.file_uploader("Pilih file `firebase_cred.json`", type=["json"])
    if uploaded_cred:
        os.makedirs("utils", exist_ok=True)
        cred_path = os.path.join("utils", "firebase_cred.json")
        with open(cred_path, "wb") as f:
            f.write(uploaded_cred.read())
        st.sidebar.success("✅ Credential berhasil diupload.")
        
        # Force init dan sync ulang setelah upload
        from utils.firebase_sync import init_firebase
        init_firebase(force_reinit=True)
        sync_data_from_cloud()
        st.rerun()


def main():
    if not os.path.exists("utils/firebase_cred.json"):
        st.warning("⚠️ Firebase credential belum tersedia.")
        handle_cred_upload()
        return

    # 🔄 Sinkronisasi awal saat aplikasi dibuka
    sync_data_from_cloud()

    if not is_logged_in():
        login()
        return

    # Sidebar Info Pengguna
    username = st.session_state.username
    role = st.session_state.role
    st.sidebar.title("👤 Selamat datang")
    st.sidebar.markdown(f"**User:** `{username}`")
    st.sidebar.markdown(f"**Role:** `{role}`")

    # 🔄 Sinkronisasi ke cloud saat logout
    st.sidebar.button("🚪 Logout", on_click=lambda: [sync_data_to_cloud(), logout()])

    # Role Koordinator bisa akses semua tab
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
