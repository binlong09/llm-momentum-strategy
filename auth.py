"""
Simple authentication for production deployment
Disabled for local development
Includes persistent login for 7 days using browser cookies
"""
import streamlit as st
import os
import hashlib
import hmac
from datetime import datetime, timedelta
import extra_streamlit_components as stx


# Cookie manager singleton
@st.cache_resource
def get_cookie_manager():
    """Get cookie manager instance (cached)"""
    return stx.CookieManager()


def is_production():
    """Check if running in production (deployed) environment"""
    # Check if running on Streamlit Cloud or other deployment
    return (
        "auth" in st.secrets  # Secrets configured (production)
        or os.getenv("STREAMLIT_RUNTIME_ENV") == "cloud"  # Streamlit Cloud
        or os.getenv("ENABLE_AUTH") == "true"  # Manual flag
    )


def generate_token(username: str, password: str, secret: str) -> str:
    """Generate a secure token for the user"""
    data = f"{username}:{password}:{secret}"
    return hashlib.sha256(data.encode()).hexdigest()


def verify_token(token: str, username: str, password: str, secret: str) -> bool:
    """Verify if the token is valid"""
    expected_token = generate_token(username, password, secret)
    return hmac.compare_digest(token, expected_token)


def check_authentication():
    """
    Check if user is authenticated.
    Only runs in production - disabled for local development.
    Persistent login for 7 days using browser cookies.

    Returns:
        bool: True if authenticated or running locally, False otherwise
    """

    # Disable auth for local development
    if not is_production():
        return True

    # Initialize session state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    # If already authenticated in this session, return True
    if st.session_state.authenticated:
        return True

    # Get credentials from secrets
    try:
        username = st.secrets["auth"]["username"]
        password = st.secrets["auth"]["password"]
        # Use a secret key for token generation (can be same as password or separate)
        secret_key = st.secrets["auth"].get("secret_key", password)
    except (KeyError, FileNotFoundError):
        # If secrets not configured, allow access (fail open for local dev)
        st.warning("⚠️ Authentication not configured. Running in open mode.")
        return True

    # Get cookie manager
    cookie_manager = get_cookie_manager()

    # Check for existing auth cookie
    auth_token = cookie_manager.get("auth_token")

    if auth_token:
        # Verify the token
        if verify_token(auth_token, username, password, secret_key):
            # Valid token - auto-login
            st.session_state.authenticated = True
            return True
        else:
            # Invalid token - clear it
            cookie_manager.delete("auth_token")

    # Show login form
    st.markdown("# 🔒 Login Required")
    st.markdown("Please enter your credentials to access the dashboard.")
    st.markdown("*Login will be remembered for 7 days*")

    with st.form("login_form"):
        input_username = st.text_input("Username")
        input_password = st.text_input("Password", type="password")
        remember_me = st.checkbox("Remember me for 7 days", value=True)
        submit = st.form_submit_button("Login")

        if submit:
            if input_username == username and input_password == password:
                st.session_state.authenticated = True

                # Set cookie for persistent login
                if remember_me:
                    token = generate_token(username, password, secret_key)
                    # Set cookie to expire in 7 days
                    expires_at = datetime.now() + timedelta(days=7)
                    cookie_manager.set(
                        "auth_token",
                        token,
                        expires_at=expires_at
                    )

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
            # Clear session state
            st.session_state.authenticated = False

            # Clear cookie
            try:
                cookie_manager = get_cookie_manager()
                cookie_manager.delete("auth_token")
            except:
                pass

            st.rerun()
