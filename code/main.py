import streamlit as st
from Tabs import user_dashboard


# =========================================================
# 🎨 Load Global CSS (LIGHT MODE ONLY)
# =========================================================
def load_css():
    with open("assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# =========================================================
# 📄 Page Imports
# =========================================================

# Auth pages
from auth.login import app as login_app
from auth.register import app as register_app

# User & Admin pages
from Tabs import home, detect, data, admin_dashboard, user_management

# =========================================================
# ⚙️ Page Configuration
# =========================================================
st.set_page_config(
    page_title="MENTRA – Student Stress Prediction",
    page_icon="🧠",
    layout="wide"
)

# =========================================================
# 🧠 Session Defaults
# =========================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "role" not in st.session_state:
    st.session_state.role = None

if "username" not in st.session_state:
    st.session_state.username = None

# =========================================================
# 🔐 NOT LOGGED IN → LOGIN / REGISTER
# =========================================================
if not st.session_state.logged_in:
    st.sidebar.markdown(
        """
        <div class="sidebar-brand">
            <h2>MENTRA 🧠</h2>
            <p>AI-Based Student Stress Prediction</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.sidebar.divider()

    st.sidebar.markdown("### 🔐 Authentication")

    auth_choice = st.sidebar.radio(
        "Choose an option",
        ["Login", "Register"],
        label_visibility="collapsed"
    )

    if auth_choice == "Login":
        login_app()
    else:
        register_app()

    st.stop()  # ⛔ Stop app here if not logged in

# =========================================================
# ✅ LOGGED IN → ROLE-BASED NAVIGATION
# =========================================================

# ---------- SIDEBAR BRAND ----------
st.sidebar.markdown(
    """
    <div class="sidebar-brand">
        <h2>MENTRA 🧠</h2>
        <p>Student Stress Prediction System</p>
    </div>
    """,
    unsafe_allow_html=True
)

# ---------- USER / ADMIN CARD ----------
st.sidebar.markdown(
    f"""
    <div class="sidebar-user-card">
        <strong>{st.session_state.username}</strong>
        <span>{st.session_state.role.capitalize()} Account</span>
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.divider()

# ---------- ROLE-BASED NAVIGATION ----------
if st.session_state.role == "user":
    pages = {
        "🏠 Home": home,
        "📊 Dashboard": user_dashboard,
        "🧠 Stress Prediction": detect
    }


elif st.session_state.role == "admin":
    pages = {
        "🏠 Home": home,
        "📊 Admin Dashboard": admin_dashboard,
        "👥 User Management": user_management,
        "📄 Dataset Info": data
    }

else:
    st.error("Unauthorized access.")
    st.stop()

if "page" not in st.session_state:
    st.session_state.page = list(pages.keys())[0]

page = st.sidebar.radio(
    "Navigate",
    list(pages.keys()),
    index=list(pages.keys()).index(st.session_state.page),
    label_visibility="collapsed"
)

st.session_state.page = page


# ---------- LOGOUT ----------
st.sidebar.divider()
with st.sidebar.container():
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# =========================================================
# 🚀 Load Selected Page
# =========================================================
pages[page].app()
