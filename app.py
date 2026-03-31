import streamlit as st
from config import APP_TITLE, APP_ICON
from auth import init_default_users, is_logged_in, is_admin, login
from admin import render_admin_page
from chat import render_user_page

# ── Page config ───────────────────────────────────────
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Global styles ─────────────────────────────────────
st.markdown("""
<style>
    /* Hide default Streamlit chrome */
    #MainMenu { visibility: hidden; }
    footer     { visibility: hidden; }

    /* Chat message styling */
    .stChatMessage { border-radius: 12px; margin-bottom: 8px; }

    /* Metric cards */
    [data-testid="metric-container"] {
        background: rgba(30,41,59,0.5);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 16px;
    }

    /* Sidebar bucket buttons */
    .stButton button {
        border-radius: 8px;
        transition: all 0.2s;
    }

    /* Expander headers */
    .streamlit-expanderHeader { font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ── Init ──────────────────────────────────────────────
init_default_users()

# ── Routing ───────────────────────────────────────────
if not is_logged_in():
    # Login screen
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            "<h1 style='text-align:center;font-size:2.5rem'>📄 RAG Chatbot</h1>",
            unsafe_allow_html=True
        )
        st.markdown(
            "<p style='text-align:center;color:#94a3b8;margin-bottom:2rem'>"
            "AI-powered document assistant with role-based bucket access"
            "</p>",
            unsafe_allow_html=True
        )

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            submitted = st.form_submit_button("Login →", type="primary", use_container_width=True)

        if submitted:
            if not username or not password:
                st.error("Please enter both username and password.")
            else:
                ok, err = login(username.strip(), password)
                if ok:
                    st.rerun()
                else:
                    st.error(err)

        st.divider()
        st.markdown(
            "<div style='text-align:center;font-size:12px;color:#475569'>"
            "Default credentials: <code>admin / admin123</code> · <code>user / user123</code>"
            "</div>",
            unsafe_allow_html=True
        )

else:
    # Route based on role
    if is_admin():
        render_admin_page()
    else:
        render_user_page()
