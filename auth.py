"""Simple bcrypt-based auth backed by MongoDB."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

import bcrypt
import streamlit as st

from db import get_db


def _users():
    return get_db().users


def register(username: str, password: str) -> tuple[bool, str]:
    username = username.strip().lower()
    if not username or len(password) < 6:
        return False, "Username required and password must be 6+ chars."
    if _users().find_one({"username": username}):
        return False, "Username already taken."
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    _users().insert_one({
        "username": username,
        "password_hash": pw_hash,
        "created_at": datetime.utcnow(),
    })
    return True, "Account created."


def login(username: str, password: str) -> bool:
    username = username.strip().lower()
    user = _users().find_one({"username": username})
    if not user:
        return False
    return bcrypt.checkpw(password.encode(), user["password_hash"])


def current_user() -> Optional[str]:
    return st.session_state.get("user")


def logout() -> None:
    st.session_state.pop("user", None)


def login_ui() -> None:
    st.title("🔬 ML Experiment Tracker")
    st.caption("Sign in to track your machine learning experiments.")

    tab_login, tab_signup = st.tabs(["Sign in", "Create account"])

    with tab_login:
        with st.form("login_form"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Sign in", use_container_width=True, type="primary"):
                if login(u, p):
                    st.session_state["user"] = u.strip().lower()
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

    with tab_signup:
        with st.form("signup_form"):
            u = st.text_input("Username", key="su_u")
            p = st.text_input("Password (6+ chars)", type="password", key="su_p")
            if st.form_submit_button("Create account", use_container_width=True):
                ok, msg = register(u, p)
                (st.success if ok else st.error)(msg)
                if ok:
                    st.session_state["user"] = u.strip().lower()
                    st.rerun()


def require_auth() -> str:
    user = current_user()
    if not user:
        login_ui()
        st.stop()
    return user
