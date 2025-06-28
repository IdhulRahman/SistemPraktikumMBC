import streamlit as st
import json
from utils.auth import login, logout, is_logged_in
from utils.config import PAGE_TABS_BY_ROLE
from utils.firebase_sync import (
    sync_data_from_cloud,
    sync_data_to_cloud,
    test_firebase_connections,
)
from utils.db import save_users

st.set_page_config(page_title="Sistem Manajemen Praktikum MBC", layout="wide")

USERS_PATH = "data/db/users.json"

def show_account_settings():
    with st.sidebar.expander("🔐 Ubah Username / Password", expanded=False):
        try:
            with open(USERS_PATH, "r") as f:
                users = json.load(f)

            old_username = st.session_state.username
            role = st.session_state.role

            st.markdown("### ✏️ Form Penggantian Akun")
            st.text_input("👤 Username Lama", value=old_username, disabled=True)
            current_password = st.text_input("🔑 Password Saat Ini", type="password")
            new_username = st.text_input("🆕 Username Baru", placeholder="Masukkan username baru (huruf kecil saja)")
            new_password = st.text_input("🔒 Password Baru", type="password")

            if st.button("💾 Simpan Perubahan"):
                old_username_lower = old_username.lower()
                new_username_lower = new_username.strip().lower()

                if old_username_lower not in users:
                    st.error("❌ User tidak ditemukan.")
                elif current_password != users[old_username_lower]["password"]:
                    st.error("❌ Password saat ini salah.")
                elif new_username_lower == "":
                    st.warning("⚠️ Username baru tidak boleh kosong.")
                elif new_username_lower != old_username_lower and new_username_lower in users:
                    st.warning("⚠️ Username baru sudah digunakan.")
                else:
                    # Update user data
                    updated_user_data = {
                        "password": new_password,
                        "role": users[old_username_lower]["role"]
                    }
                    users.pop(old_username_lower)
                    users[new_username_lower] = updated_user_data

                    # Simpan ke lokal
                    save_users(users)
                    st.toast("✅ File lokal users.json diperbarui.")

                    # Info login ulang manual
                    st.success("✅ Akun berhasil diperbarui.")
                    sync_data_to_cloud()
                    st.toast("🔄 Sinkronisasi selesai.")
                    st.info("Silakan logout dan login kembali untuk menggunakan akun baru. (opsional)")



        except Exception as e:
            st.error(f"❌ Terjadi kesalahan saat memproses akun: {e}")


def main():
    # 🔌 Cek koneksi Firebase
    firestore_ok, storage_ok = test_firebase_connections()

    with st.sidebar:
        st.subheader("🌐 Status Koneksi Firebase")
        st.markdown(f"**Firestore:** {'🟢 Terhubung' if firestore_ok else '🔴 Gagal'}")
        st.markdown(f"**Storage:** {'🟢 Terhubung' if storage_ok else '🔴 Gagal'}")

    # 🔄 Sync from cloud hanya 1x di awal
    if firestore_ok and storage_ok:
        if "already_synced" not in st.session_state:
            sync_data_from_cloud()
            st.session_state.already_synced = True
    else:
        st.error("Gagal terhubung ke Firebase. Periksa kembali credential dan koneksi internet.")
        return

    if not is_logged_in():
        login()
        return

    # Sidebar Info Pengguna
    username = st.session_state.username
    role = st.session_state.role
    st.sidebar.title("👤 Selamat datang")
    st.sidebar.markdown(f"**User:** `{username}`")
    st.sidebar.markdown(f"**Role:** `{role}`")

    # Form ubah akun
    show_account_settings()

    # Tombol logout
    st.sidebar.button("🚪 Logout", on_click=lambda: [sync_data_to_cloud(), logout()])

    # Navigasi berdasarkan role
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
