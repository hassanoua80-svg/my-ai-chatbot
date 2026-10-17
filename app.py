
# ---------- Professional ChatGPT-style design ----------
st.markdown("""
<style>
:root {
    --chat-bg: #ffffff;
    --chat-sidebar: #f7f7f8;
    --chat-text: #242424;
    --chat-border: #e5e5e5;
}

.stApp {
    background: var(--chat-bg);
    color: var(--chat-text);
}

header[data-testid="stHeader"] {
    background: rgba(255, 255, 255, 0.9);
}

section[data-testid="stSidebar"] {
    background: var(--chat-sidebar);
    border-right: 1px solid var(--chat-border);
}

section[data-testid="stSidebar"] button {
    border-radius: 10px;
}

.block-container {
    max-width: 900px;
    padding-top: 2rem;
    padding-bottom: 7rem;
}

[data-testid="stChatMessage"] {
    border: 1px solid #eeeeee;
    border-radius: 16px;
    padding: 1rem 1.1rem;
    margin-bottom: 12px;
    background: #ffffff;
}

[data-testid="stChatInput"] {
    border-radius: 18px;
}

[data-testid="stChatInput"] textarea {
    font-size: 16px;
    line-height: 1.7;
}

.stButton > button {
    border-radius: 12px;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    border-color: #888888;
}

h1, h2, h3 {
    letter-spacing: -0.4px;
}

@media (max-width: 768px) {
    .block-container {
        padding: 1rem 0.7rem 5rem 0.7rem;
    }

    [data-testid="stChatMessage"] {
        padding: 0.8rem;
        border-radius: 12px;
    }
}
</style>
""", unsafe_allow_html=True)
# ------------------------------------------------------
