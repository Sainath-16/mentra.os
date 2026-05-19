import streamlit as st
import sqlite3
from datetime import datetime
import re
from web_functions import hash_password


def is_valid_username(username):
    if not username.isalnum():
        return False, "Username must contain only letters and numbers."
    if len(username) < 4 or len(username) > 20:
        return False, "Username must be between 4 and 20 characters."
    return True, ""


def is_valid_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number."
    if not re.search(r"[!@#$%^&*]", password):
        return False, "Password must contain at least one special character (!@#$%^&*)."
    return True, ""


def password_strength(password):
    score = 0
    if len(password) >= 8: score += 1
    if re.search(r"[A-Z]", password): score += 1
    if re.search(r"[a-z]", password): score += 1
    if re.search(r"[0-9]", password): score += 1
    if re.search(r"[!@#$%^&*]", password): score += 1
    return score


def app():
    st.title("📝 User Registration")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    if password:
        strength = password_strength(password)
        st.progress(strength / 5)
        st.caption("Password strength")

    if st.button("Register"):
        if not username or not password or not confirm_password:
            st.error("All fields are required.")
            return

        valid_user, msg = is_valid_username(username)
        if not valid_user:
            st.error(msg)
            return

        valid_pass, msg = is_valid_password(password)
        if not valid_pass:
            st.error(msg)
            return

        if password != confirm_password:
            st.error("Passwords do not match.")
            return

        hashed_password = hash_password(password)

        try:
            conn = sqlite3.connect("database/mentra.db")
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO users (username, password, role, created_at)
                VALUES (?, ?, ?, ?)
            """, (
                username,
                hashed_password,
                "user",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))

            conn.commit()
            conn.close()
            st.success("✅ Registration successful! Please login.")

        except sqlite3.IntegrityError:
            st.error("❌ Username already exists.")
