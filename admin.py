import streamlit as st
from auth import (
    get_all_users, create_user, update_user_buckets,
    toggle_user_enabled, delete_user, change_password, logout
)
from bucket_manager import (
    list_buckets, create_bucket, delete_bucket,
    list_documents, get_stats
)
from rag import ingest_pdf, delete_pdf, chat_with_bucket
from config import ADMIN_ROLE, USER_ROLE


# ── Helpers ───────────────────────────────────────────

def bucket_emoji(name: str) -> str:
    mapping = {
        "medical": "🏥", "health": "🏥",
        "sales": "💼", "finance": "💰", "financial": "💰",
        "legal": "⚖️", "law": "⚖️",
        "tech": "🔧", "technology": "🔧", "engineering": "🔧",
        "hr": "👥", "human": "👥",
        "marketing": "📣",
        "research": "🔬",
        "education": "📚",
    }
    for key, emoji in mapping.items():
        if key in name.lower():
            return emoji
    return "🪣"


# ── Dashboard Tab ─────────────────────────────────────

def render_dashboard():
    st.subheader("📊 Dashboard Overview")

    stats   = get_stats()
    users   = get_all_users()
    n_users = len([u for u, d in users.items() if d["role"] == USER_ROLE])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🪣 Buckets",   stats["total_buckets"])
    c2.metric("📄 Documents", stats["total_docs"])
    c3.metric("🔢 Chunks",    stats["total_chunks"])
    c4.metric("👥 Users",     n_users)

    st.divider()
    st.markdown("### Per-Bucket Breakdown")

    if not stats["buckets"]:
        st.info("No buckets created yet. Go to the **Buckets** tab to create one.")
        return

    for b in stats["buckets"]:
        with st.expander(f"{bucket_emoji(b['name'])} **{b['name']}**  —  {b['docs']} docs · {b['chunks']} chunks"):
            if b["description"]:
                st.caption(b["description"])
            col1, col2 = st.columns(2)
            col1.metric("Documents", b["docs"])
            col2.metric("Indexed Chunks", b["chunks"])


# ── Buckets Tab ───────────────────────────────────────

def render_buckets():
    st.subheader("🪣 Manage Buckets")

    # Create bucket
    with st.expander("➕ Create New Bucket", expanded=False):
        with st.form("create_bucket_form"):
            bname = st.text_input("Bucket Name", placeholder="e.g. Medical, Sales, Legal")
            bdesc = st.text_area("Description (optional)", placeholder="What kind of documents go here?", height=80)
            if st.form_submit_button("Create Bucket", type="primary"):
                ok, msg = create_bucket(bname.strip(), bdesc.strip())
                if ok:
                    st.success(f"✅ Bucket '{bname}' created!")
                    st.rerun()
                else:
                    st.error(msg)

    st.divider()

    buckets = list_buckets()
    if not buckets:
        st.info("No buckets yet. Create one above.")
        return

    for bucket in buckets:
        with st.expander(f"{bucket_emoji(bucket)} **{bucket}**", expanded=False):
            docs = list_documents(bucket)

            # Upload PDF
            st.markdown("**📤 Upload PDF**")
            with st.form(f"upload_{bucket}"):
                uploaded = st.file_uploader("Choose a PDF", type=["pdf"], key=f"file_{bucket}")
                doc_desc = st.text_input("Document description / tag", placeholder="e.g. Q3 Report, Drug Guidelines", key=f"desc_{bucket}")
                if st.form_submit_button("Upload & Index", type="primary"):
                    if uploaded:
                        with st.spinner("Indexing PDF..."):
                            ok, msg, n = ingest_pdf(bucket, uploaded.read(), uploaded.name, doc_desc)
                        if ok:
                            st.success(f"✅ {msg}")
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.warning("Please select a PDF file.")

            # Documents list
            st.markdown(f"**📄 Documents ({len(docs)})**")
            if not docs:
                st.caption("No documents uploaded yet.")
            else:
                for doc_id, info in docs.items():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    col1.markdown(f"📄 **{info['filename']}**")
                    col2.caption(f"{info.get('description', '—')} · {info['chunks']} chunks")
                    if col3.button("🗑️", key=f"del_{doc_id}", help="Delete this document"):
                        ok, msg = delete_pdf(bucket, doc_id)
                        if ok:
                            st.success(f"Deleted '{info['filename']}'")
                            st.rerun()
                        else:
                            st.error(msg)

            st.divider()
            # Delete bucket
            if st.button(f"🗑️ Delete Bucket '{bucket}'", key=f"delbucket_{bucket}", type="secondary"):
                ok, msg = delete_bucket(bucket)
                if ok:
                    st.success(f"Bucket '{bucket}' deleted.")
                    st.rerun()
                else:
                    st.error(msg)


# ── Users Tab ─────────────────────────────────────────

def render_users():
    st.subheader("👥 User Management")
    buckets = list_buckets()

    # Create user
    with st.expander("➕ Create New User", expanded=False):
        with st.form("create_user_form"):
            uname  = st.text_input("Username")
            upass  = st.text_input("Password", type="password")
            urole  = st.selectbox("Role", [USER_ROLE, ADMIN_ROLE])
            ubucks = st.multiselect("Assign Buckets", buckets) if urole == USER_ROLE else []
            if st.form_submit_button("Create User", type="primary"):
                ok, msg = create_user(uname.strip(), upass, urole, ubucks if urole == USER_ROLE else ["*"])
                if ok:
                    st.success(f"✅ User '{uname}' created!")
                    st.rerun()
                else:
                    st.error(msg)

    st.divider()
    st.markdown("### Existing Users")

    users = get_all_users()
    for uname, udata in users.items():
        if uname == "admin" and udata["role"] == ADMIN_ROLE:
            # Show admin row but no destructive actions on primary admin
            with st.expander(f"👑 **{uname}** — Admin (primary)", expanded=False):
                st.caption("Primary admin account. Password can be changed below.")
                with st.form(f"pw_{uname}"):
                    new_pw = st.text_input("New Password", type="password")
                    if st.form_submit_button("Change Password"):
                        ok, msg = change_password(uname, new_pw)
                        st.success(msg) if ok else st.error(msg)
            continue

        enabled = udata.get("enabled", True)
        role    = udata.get("role", USER_ROLE)
        icon    = "👑" if role == ADMIN_ROLE else ("👤" if enabled else "🚫")
        status  = "Active" if enabled else "Disabled"

        with st.expander(f"{icon} **{uname}** — {role.capitalize()} · {status}", expanded=False):
            col1, col2 = st.columns(2)

            # Bucket permissions (only for regular users)
            if role == USER_ROLE and buckets:
                current_buckets = udata.get("buckets", [])
                new_buckets = st.multiselect(
                    "Bucket Access",
                    buckets,
                    default=[b for b in current_buckets if b in buckets],
                    key=f"bucks_{uname}"
                )
                if st.button("💾 Save Permissions", key=f"save_{uname}"):
                    update_user_buckets(uname, new_buckets)
                    st.success("Permissions updated!")
                    st.rerun()

            st.divider()
            c1, c2, c3 = st.columns(3)

            # Enable/Disable toggle
            toggle_label = "✅ Enable" if not enabled else "🚫 Disable"
            if c1.button(toggle_label, key=f"toggle_{uname}"):
                toggle_user_enabled(uname)
                st.rerun()

            # Change password
            with c2.popover("🔑 Change Password"):
                with st.form(f"pw_{uname}"):
                    new_pw = st.text_input("New Password", type="password", key=f"newpw_{uname}")
                    if st.form_submit_button("Update"):
                        ok, msg = change_password(uname, new_pw)
                        st.success(msg) if ok else st.error(msg)

            # Delete user
            if c3.button("🗑️ Delete", key=f"del_{uname}"):
                delete_user(uname)
                st.success(f"User '{uname}' deleted.")
                st.rerun()


# ── Admin Chat Tab ────────────────────────────────────

def render_admin_chat():
    st.subheader("💬 Chat — Test Any Bucket")

    buckets = list_buckets()
    if not buckets:
        st.info("No buckets available. Create a bucket and upload PDFs first.")
        return

    selected = st.selectbox(
        "Select Bucket to Test",
        buckets,
        format_func=lambda b: f"{bucket_emoji(b)} {b}"
    )

    if not selected:
        return

    docs = list_documents(selected)
    if not docs:
        st.warning(f"⚠️ Bucket **{selected}** has no documents. Upload PDFs in the Buckets tab.")
        return

    st.caption(f"Chatting with **{selected}** · {len(docs)} document(s) loaded")

    # Session key per bucket for admin
    hist_key = f"admin_chat_{selected}"
    if hist_key not in st.session_state:
        st.session_state[hist_key] = []

    # Display chat history
    chat_container = st.container(height=420)
    with chat_container:
        if not st.session_state[hist_key]:
            st.markdown(
                f"<div style='text-align:center;color:#888;padding:40px 0'>Ask anything about the <b>{selected}</b> documents</div>",
                unsafe_allow_html=True
            )
        for msg in st.session_state[hist_key]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("sources"):
                    with st.expander(f"📎 {len(msg['sources'])} source(s)"):
                        for s in msg["sources"]:
                            st.caption(f"📄 **{s['filename']}** · Page {s['page']}")
                            st.markdown(f"> {s['text'][:200]}...")

    col1, col2 = st.columns([5, 1])
    user_input = col1.chat_input(f"Ask about {selected}...")
    if col2.button("🗑️ Clear", key=f"clear_admin_{selected}"):
        st.session_state[hist_key] = []
        st.rerun()

    if user_input:
        st.session_state[hist_key].append({"role": "user", "content": user_input})
        with st.spinner("Thinking..."):
            answer, sources = chat_with_bucket(selected, user_input, st.session_state[hist_key])
        st.session_state[hist_key].append({
            "role": "assistant", "content": answer, "sources": sources
        })
        st.rerun()


# ── Main Admin Page ───────────────────────────────────

def render_admin_page():
    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👑 Admin Panel")
        st.caption(f"Logged in as **admin**")
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            logout()
            st.rerun()

    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "🪣 Buckets", "👥 Users", "💬 Chat"])
    with tab1: render_dashboard()
    with tab2: render_buckets()
    with tab3: render_users()
    with tab4: render_admin_chat()
