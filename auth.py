"""
Simple authentication for production deployment
Disabled for local development
"""
import streamlit as st
import os


def is_production():
    """Check if running in production (deployed) environment"""
    # Check if running on Streamlit Cloud or other deployment
    return (
        "auth" in st.secrets  # Secrets configured (production)
        or os.getenv("STREAMLIT_RUNTIME_ENV") == "cloud"  # Streamlit Cloud
        or os.getenv("ENABLE_AUTH") == "true"  # Manual flag
    )


def check_authentication():
    """
    Check if user is authenticated.
    Only runs in production - disabled for local development.

    Returns:
        bool: True if authenticated or running locally, False otherwise
    """

    # Disable auth for local development
    if not is_production():
        return True

    # Initialize session state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    # If already authenticated, return True
    if st.session_state.authenticated:
        return True

    # Get credentials from secrets
    try:
        username = st.secrets["auth"]["username"]
        password = st.secrets["auth"]["password"]
    except (KeyError, FileNotFoundError):
        # If secrets not configured, allow access (fail open for local dev)
        st.warning("⚠️ Authentication not configured. Running in open mode.")
        return True

    # Show login form
    st.markdown("# 🔒 Login Required")
    st.markdown("Please enter your credentials to access the dashboard.")

    with st.form("login_form"):
        input_username = st.text_input("Username")
        input_password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

        if submit:
            if input_username == username and input_password == password:
                st.session_state.authenticated = True
                st.success("✅ Authentication successful!")
                st.rerun()
            else:
                st.error("❌ Invalid username or password")

    return False


def add_logout_button():
    """Add logout button to sidebar (only in production)"""
    if is_production() and st.session_state.get("authenticated", False):
        st.sidebar.markdown("---")
        if st.sidebar.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.rerun()
