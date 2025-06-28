import json
import os
import streamlit as st
from utils.firebase_sync import upload_to_storage, download_from_storage

USERS_FILE = "data/users.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        download_from_storage("users.json", USERS_FILE)
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)
    upload_to_storage(USERS_FILE, "users.json")

def ganti_akun_sidebar():
    with st.expander("🔐 Ganti Username / Password"):
        current_user = st.session_state.get("username")
        users = load_users()

        if current_user not in users:
            st.error("Akun tidak ditemukan.")
            return

        old_pass = st.text_input("Password Lama", type="password", key="old_pass")
        new_user = st.text_input("Username Baru", value=current_user, key="new_user")
        new_pass = st.text_input("Password Baru", type="password", key="new_pass")

        if st.button("💾 Simpan Perubahan", key="simpan_ganti_userpass"):
            if old_pass != users[current_user]["password"]:
                st.error("Password lama salah.")
                return
            if not new_user or not new_pass:
                st.error("Username dan password tidak boleh kosong.")
                return
            if new_user != current_user and new_user in users:
                st.error("Username baru sudah digunakan.")
                return

            # Simpan perubahan username dan password
            users[new_user] = {
                "password": new_pass,
                "role": users[current_user]["role"]  # role tidak berubah
            }
            if new_user != current_user:
                del users[current_user]
                st.session_state.username = new_user

            save_users(users)
            st.success("Akun berhasil diperbarui. Silakan logout dan login ulang.")
