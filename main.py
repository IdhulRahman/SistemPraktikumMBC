import streamlit as st
from utils.auth import login, logout, is_logged_in
from utils.config import PAGE_TABS_BY_ROLE

st.set_page_config(page_title="Sistem Manajemen Praktikum MBC", layout="wide")

def main():
    if not is_logged_in():
        login()
        return

    # Sidebar Info Pengguna
    username = st.session_state.username
    role = st.session_state.role
    st.sidebar.title("👤 Selamat datang")
    st.sidebar.markdown(f"**User:** `{username}`")
    st.sidebar.markdown(f"**Role:** `{role}`")
    st.sidebar.button("🚪 Logout", on_click=logout)

    # Role Koordinator bisa akses semua tab dari semua role
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
