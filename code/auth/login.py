import streamlit as st
import sqlite3
from web_functions import verify_password


def app():

    # ===== WELCOME HEADER =====
    st.markdown(
        """
        <div style="text-align:center; margin-bottom:2rem;">
            <h1>Welcome to <span style="color:#4f46e5;">MENTRA</span> 🧠</h1>
            <p style="font-size:1.1rem; color:#475569;">
                AI-Based Student Stress Prediction System<br>
                Sign in to continue
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ===== LOGIN FORM (NO HTML WRAPPER) =====
    username = st.text_input("Username", placeholder="Enter your username")
    password = st.text_input(
        "Password",
        type="password",
        placeholder="Enter your password"
    )

    if st.button("🔐 Login"):
        if not username or not password:
            st.error("Please enter username and password.")
            return

        # -------- EXISTING LOGIC (UNCHANGED) --------
        conn = sqlite3.connect("database/mentra.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, role, password FROM users WHERE username = ?
        """, (username,))

        user = cursor.fetchone()
        conn.close()

        if user is None:
            st.error("❌ Invalid username or password.")
            return

        user_id, role, stored_password = user

        if not verify_password(password, stored_password):
            st.error("❌ Invalid username or password.")
            return

        # -------- LOGIN SUCCESS --------
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.user_id = user_id
        st.session_state.role = role

        st.success(f"✅ Logged in as {username} ({role})")
        st.rerun()
