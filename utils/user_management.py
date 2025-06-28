from utils.db import load_users, save_users
import streamlit as st

def ganti_akun_sidebar():
    with st.expander("🔐 Ganti Username / Password"):
        current_user = st.session_state.get("username")
        users = load_users()

        # Case-insensitive pencocokan user
        matched_user = None
        for uname in users:
            if uname.lower() == current_user.lower():
                matched_user = uname
                break

        if not matched_user:
            st.error("Akun tidak ditemukan.")
            return

        old_pass = st.text_input("Password Lama", type="password", key="old_pass")
        new_user = st.text_input("Username Baru", value=matched_user, key="new_user")
        new_pass = st.text_input("Password Baru", type="password", key="new_pass")

        if st.button("💾 Simpan Perubahan", key="simpan_ganti_userpass"):
            if old_pass != users[matched_user]["password"]:
                st.error("Password lama salah.")
                return
            if not new_user or not new_pass:
                st.error("Username dan password tidak boleh kosong.")
                return
            if new_user != matched_user and new_user in users:
                st.error("Username baru sudah digunakan.")
                return

            # Simpan perubahan
            users[new_user] = {
                "password": new_pass,
                "role": users[matched_user]["role"]
            }

            # Hapus username lama jika diganti
            if new_user != matched_user:
                del users[matched_user]
                st.session_state.username = new_user  # Update session

            save_users(users)
            st.success("Akun berhasil diperbarui. Silakan logout dan login ulang.")
