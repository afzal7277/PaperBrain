import streamlit as st
from auth import allowed_buckets, logout, current_user
from bucket_manager import list_documents
from rag import chat_with_bucket


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


def render_user_page():
    username = current_user()
    buckets  = allowed_buckets()

    # ── Sidebar ───────────────────────────────────────
    with st.sidebar:
        st.markdown(f"### 👤 {username}")
        st.divider()

        if not buckets:
            st.warning("No buckets assigned.\nContact your admin.")
            st.divider()
            if st.button("🚪 Logout", use_container_width=True):
                logout()
                st.rerun()
            return

        st.markdown("**Select a Bucket**")
        selected = st.session_state.get("active_bucket", buckets[0])
        if selected not in buckets:
            selected = buckets[0]

        for b in buckets:
            is_active = b == selected
            label     = f"{bucket_emoji(b)} {b}"
            if is_active:
                st.markdown(
                    f"<div style='background:#1e3a5f;border-radius:8px;padding:8px 12px;"
                    f"margin-bottom:4px;font-weight:600;color:#60a5fa'>{label} ✓</div>",
                    unsafe_allow_html=True
                )
            else:
                if st.button(label, key=f"bucket_btn_{b}", use_container_width=True):
                    st.session_state.active_bucket = b
                    st.rerun()

        st.divider()

        # Bucket info
        docs = list_documents(selected)
        st.caption(f"📄 {len(docs)} document(s) in this bucket")
        if docs:
            with st.expander("View documents"):
                for _, info in docs.items():
                    st.caption(f"• {info['filename']}" + (f"\n  _{info.get('description', '')}_" if info.get("description") else ""))

        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            logout()
            st.rerun()

    # ── Main Chat Area ────────────────────────────────
    st.session_state.active_bucket = selected

    st.markdown(f"## {bucket_emoji(selected)} {selected}")
    st.caption(f"Your questions will be answered using only **{selected}** documents.")

    # Check if bucket has documents
    docs = list_documents(selected)
    if not docs:
        st.warning(f"⚠️ The **{selected}** bucket has no documents yet. Please ask your admin to upload some.")
        return

    # Chat history per bucket
    hist_key = f"chat_{username}_{selected}"
    if hist_key not in st.session_state:
        st.session_state[hist_key] = []

    # Welcome message
    if not st.session_state[hist_key]:
        st.info(f"👋 Hi **{username}**! Ask me anything about the **{selected}** documents.")

    # Display messages
    chat_container = st.container(height=450)
    with chat_container:
        for msg in st.session_state[hist_key]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                # Show sources for assistant messages
                if msg["role"] == "assistant" and msg.get("sources"):
                    with st.expander(f"📎 {len(msg['sources'])} source(s) referenced"):
                        for s in msg["sources"]:
                            col1, col2 = st.columns([2, 1])
                            col1.markdown(f"📄 **{s['filename']}**")
                            col2.caption(f"Page {s['page']}")
                            if s.get("desc"):
                                st.caption(f"_{s['desc']}_")
                            st.markdown(
                                f"<div style='background:#1e293b;border-left:3px solid #3b82f6;"
                                f"padding:8px 12px;border-radius:4px;font-size:13px;color:#94a3b8;"
                                f"margin-top:4px'>{s['text'][:250]}{'...' if len(s['text']) > 250 else ''}</div>",
                                unsafe_allow_html=True
                            )

    # Input row
    col1, col2 = st.columns([6, 1])
    user_input = col1.chat_input(f"Ask about {selected}...")
    if col2.button("🗑️ Clear chat", key=f"clear_{selected}"):
        st.session_state[hist_key] = []
        st.rerun()

    if user_input:
        st.session_state[hist_key].append({
            "role": "user", "content": user_input, "sources": []
        })

        with st.spinner(f"Searching {selected} documents..."):
            answer, sources = chat_with_bucket(
                selected,
                user_input,
                st.session_state[hist_key]
            )

        st.session_state[hist_key].append({
            "role": "assistant",
            "content": answer,
            "sources": sources
        })
        st.rerun()
