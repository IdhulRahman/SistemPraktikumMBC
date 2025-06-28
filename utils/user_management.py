import streamlit as st
from utils.db import load_users, save_users
from utils.firebase_sync import sync_data_to_cloud
from firebase_admin import firestore

def ganti_akun_sidebar():
    with st.expander("🔐 Ganti Username / Password"):
        st.info("Masukkan password lama dan data baru Anda.")

        # Username lama otomatis dari session_state
        old_user_input = st.text_input(
            "Username Lama",
            value=st.session_state.get("username", ""),
            key="old_user"
        ).strip().lower()

        old_pass = st.text_input("Password Lama", type="password")
        new_user_input = st.text_input("Username Baru", value=old_user_input, key="new_user").strip().lower()
        new_pass = st.text_input("Password Baru", type="password")

        users = load_users()

        if st.button("💾 Simpan Perubahan", key="simpan_ganti_userpass"):
            if old_user_input not in users:
                st.error("Username lama tidak ditemukan.")
                return
            if users[old_user_input]["password"] != old_pass:
                st.error("Password lama salah.")
                return
            if not new_user_input or not new_pass:
                st.error("Username dan password baru tidak boleh kosong.")
                return
            if new_user_input != old_user_input and new_user_input in users:
                st.error("Username baru sudah digunakan.")
                return

            # Update akun
            users[new_user_input] = {
                "password": new_pass,
                "role": users[old_user_input]["role"]
            }
            if new_user_input != old_user_input:
                del users[old_user_input]
                st.session_state.username = new_user_input  # update session

            save_users(users)
            sync_data_to_cloud()
            st.success("Akun berhasil diperbarui. Silakan logout dan login ulang.")
