import streamlit as st
from utils.db import load_users, save_users
from utils.firebase_sync import sync_data_to_cloud

def ganti_akun_sidebar():
    with st.expander("🔐 Ganti Username / Password"):
        current_user = st.session_state.get("username").lower()
        users = load_users()

        # Mapping username ke lowercase untuk pencocokan aman
        user_map = {uname.lower(): uname for uname in users}
        if current_user not in user_map:
            st.error("Akun tidak ditemukan.")
            return

        matched_user = user_map[current_user]

        old_pass = st.text_input("Password Lama", type="password", key="old_pass")
        new_user_input = st.text_input("Username Baru", value=matched_user, key="new_user")
        new_user = new_user_input.strip().lower()
        new_pass = st.text_input("Password Baru", type="password", key="new_pass")

        if st.button("💾 Simpan Perubahan", key="simpan_ganti_userpass"):
            if old_pass != users[matched_user]["password"]:
                st.error("Password lama salah.")
                return
            if not new_user or not new_pass:
                st.error("Username dan password tidak boleh kosong.")
                return
            if new_user != matched_user.lower() and new_user in [u.lower() for u in users]:
                st.error("Username baru sudah digunakan.")
                return

            # Simpan perubahan
            users[new_user] = {
                "password": new_pass,
                "role": users[matched_user]["role"]
            }

            if new_user != matched_user:
                del users[matched_user]
                st.session_state.username = new_user  # Update session state

            save_users(users)
            st.success("Akun berhasil diperbarui. Silakan logout dan login ulang.")
            sync_data_to_cloud()
