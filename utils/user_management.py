import json
import os
import streamlit as st

USERS_FILE = "data/users.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def ganti_akun_page():
    st.subheader("🔐 Ganti Username & Password")

    current_user = st.session_state.get("username")
    users = load_users()

    if current_user not in users:
        st.error("Akun Anda tidak ditemukan di sistem.")
        return

    current_pass = st.text_input("Masukkan Password Lama", type="password")
    if current_pass != users[current_user]:
        st.warning("Password lama tidak cocok.")
        return

    new_username = st.text_input("Username Baru", value=current_user)
    new_password = st.text_input("Password Baru", type="password")

    if st.button("💾 Simpan Perubahan"):
        if not new_username.strip() or not new_password.strip():
            st.error("Username dan password tidak boleh kosong.")
            return

        # Validasi duplikasi username
        if new_username != current_user and new_username in users:
            st.error("Username baru sudah digunakan.")
            return

        # Simpan perubahan
        users[new_username] = new_password
        if new_username != current_user:
            del users[current_user]
        save_users(users)

        # Update session
        st.session_state.username = new_username
        st.success("Akun berhasil diperbarui. Silakan logout dan login kembali.")
