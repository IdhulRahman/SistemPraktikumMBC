import streamlit as st
import json
from utils.db import load_users
import os

def login():
    st.title("🔐 Login Sistem Praktikum")

    username_input = st.text_input("Username")
    username = username_input.lower() if username_input else ""
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if not username or not password:
            st.warning("Silakan isi username dan password.")
            return

        users = load_users()
        if username in users and users[username]["password"] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = users[username]["role"]

            st.success(f"Selamat datang, {username} 👋 (Role: {st.session_state.role})")
            st.rerun()
        else:
            st.error("Username atau password salah.")

def logout():
    """
    Menghapus semua state login yang aktif.
    """
    keys_to_clear = ["logged_in", "username", "role"]
    for key in keys_to_clear:
        st.session_state.pop(key, None)
    st.success("Berhasil logout.")
    st.rerun()

def is_logged_in():
    """
    Mengecek apakah user sedang login.
    """
    return st.session_state.get("logged_in", False)

USER_DB = "data/db/users.json"

def register_user(username, password, role):
    if not os.path.exists(USER_DB):
        with open(USER_DB, "w") as f:
            json.dump({}, f)

    with open(USER_DB, "r") as f:
        users = json.load(f)

    users[username] = {"password": password, "role": role}

    with open(USER_DB, "w") as f:
        json.dump(users, f, indent=2)
