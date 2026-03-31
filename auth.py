import json
import os
import bcrypt
import streamlit as st
from config import USERS_FILE, DATA_DIR, ADMIN_ROLE, USER_ROLE


# ── Helpers ───────────────────────────────────────────

def _load_users() -> dict:
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)


def _save_users(users: dict):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


# ── Init default admin ────────────────────────────────

def init_default_users():
    """Create default admin + user on first run."""
    users = _load_users()
    changed = False

    if "admin" not in users:
        users["admin"] = {
            "password": _hash_password("admin123"),
            "role": ADMIN_ROLE,
            "buckets": ["*"],
            "enabled": True
        }
        changed = True

    if "user" not in users:
        users["user"] = {
            "password": _hash_password("user123"),
            "role": USER_ROLE,
            "buckets": [],
            "enabled": True
        }
        changed = True

    if changed:
        _save_users(users)


# ── Auth actions ──────────────────────────────────────

def login(username: str, password: str) -> tuple[bool, str]:
    """Returns (success, error_message)."""
    users = _load_users()
    if username not in users:
        return False, "Invalid username or password."
    u = users[username]
    if not u.get("enabled", True):
        return False, "Your account has been disabled. Contact admin."
    if not _verify_password(password, u["password"]):
        return False, "Invalid username or password."

    # Set session
    st.session_state.logged_in   = True
    st.session_state.username    = username
    st.session_state.role        = u["role"]
    st.session_state.buckets     = u["buckets"]
    st.session_state.chat_history = {}
    return True, ""


def logout():
    for key in ["logged_in", "username", "role", "buckets", "chat_history", "active_bucket"]:
        st.session_state.pop(key, None)


def is_logged_in() -> bool:
    return st.session_state.get("logged_in", False)


def current_user() -> str:
    return st.session_state.get("username", "")


def current_role() -> str:
    return st.session_state.get("role", "")


def is_admin() -> bool:
    return current_role() == ADMIN_ROLE


def allowed_buckets() -> list:
    buckets = st.session_state.get("buckets", [])
    if "*" in buckets:
        from bucket_manager import list_buckets
        return list_buckets()
    return buckets


# ── User management (admin only) ──────────────────────

def get_all_users() -> dict:
    return _load_users()


def create_user(username: str, password: str, role: str, buckets: list) -> tuple[bool, str]:
    users = _load_users()
    if username in users:
        return False, f"User '{username}' already exists."
    if not username.strip():
        return False, "Username cannot be empty."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."

    users[username] = {
        "password": _hash_password(password),
        "role": role,
        "buckets": buckets,
        "enabled": True
    }
    _save_users(users)
    return True, ""


def update_user_buckets(username: str, buckets: list):
    users = _load_users()
    if username in users:
        users[username]["buckets"] = buckets
        _save_users(users)


def toggle_user_enabled(username: str):
    users = _load_users()
    if username in users:
        users[username]["enabled"] = not users[username].get("enabled", True)
        _save_users(users)


def delete_user(username: str):
    users = _load_users()
    if username in users:
        del users[username]
        _save_users(users)


def change_password(username: str, new_password: str) -> tuple[bool, str]:
    if len(new_password) < 6:
        return False, "Password must be at least 6 characters."
    users = _load_users()
    if username not in users:
        return False, "User not found."
    users[username]["password"] = _hash_password(new_password)
    _save_users(users)
    return True, ""
