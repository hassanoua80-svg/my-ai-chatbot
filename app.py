
import os
import json
import uuid
import streamlit as st
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
from dotenv import load_dotenv
from google import genai

load_dotenv()

st.set_page_config(
    page_title="My AI Chatbot",
    page_icon="🤖",
    layout="wide"
)

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    try:
        API_KEY = st.secrets["GEMINI_API_KEY"]
    except (KeyError, FileNotFoundError):
        API_KEY = None
CHAT_FILE = "conversations.json"

if not API_KEY:
    st.error("تأكد من وجود GEMINI_API_KEY في ملف .env")
    st.stop()

client = genai.Client(api_key=API_KEY)

# ---------- Save and load conversations ----------

def load_conversations():
    if os.path.exists(CHAT_FILE):
        try:
            with open(CHAT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_conversations():
    with open(CHAT_FILE, "w", encoding="utf-8") as f:
        json.dump(
            st.session_state.conversations,
            f,
            ensure_ascii=False,
            indent=2
        )


if "conversations" not in st.session_state:
    st.session_state.conversations = load_conversations()

if "active_chat" not in st.session_state:
    st.session_state.active_chat = None


def new_chat():
    chat_id = str(uuid.uuid4())
    st.session_state.conversations[chat_id] = {
        "title": "محادثة جديدة",
        "messages": []
    }
    st.session_state.active_chat = chat_id
    save_conversations()


def get_active_chat():
    chat_id = st.session_state.active_chat
    if chat_id and chat_id in st.session_state.conversations:
        return st.session_state.conversations[chat_id]
    return None


# ---------- Design ----------

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #eef2ff, #ffffff);
}
h1 {
    color: #2563eb;
}
[data-testid="stChatMessage"] {
    border-radius: 14px;
    padding: 12px;
}
</style>
""", unsafe_allow_html=True)

# ---------- Sidebar ----------

st.sidebar.title("🤖 My AI Chatbot")
st.sidebar.caption("مساعدك الذكي")

theme = st.sidebar.radio(
    "🎨 المظهر",
    ["☀️ النهاري", "🌙 الليلي"]
)

if theme == "🌙 الليلي":
    st.markdown("""
    <style>
    .stApp {
        background: #111827 !important;
        color: #f9fafb !important;
    }
    [data-testid="stChatMessage"] {
        background: #1f2937 !important;
        color: #ffffff !important;
        border: 1px solid #374151;
    }
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li {
        color: #ffffff !important;
    }
    </style>
    """, unsafe_allow_html=True)

if st.sidebar.button("➕ محادثة جديدة", use_container_width=True):
    new_chat()
    st.rerun()

st.sidebar.divider()
st.sidebar.subheader("📚 المحادثات السابقة")

# Show saved chats
for chat_id, chat in reversed(list(st.session_state.conversations.items())):
    title = chat.get("title", "محادثة جديدة")

    col1, col2 = st.sidebar.columns([4, 1])

    with col1:
        if st.button(
            f"💬 {title[:28]}",
            key=f"open_{chat_id}",
            use_container_width=True
        ):
            st.session_state.active_chat = chat_id
            st.rerun()

    with col2:
        if st.button("🗑️", key=f"delete_{chat_id}"):
            del st.session_state.conversations[chat_id]

            if st.session_state.active_chat == chat_id:
                st.session_state.active_chat = None

            save_conversations()
            st.rerun()

# ---------- Main chat ----------

st.title("💬 المحادثة")

chat = get_active_chat()

if chat is None:
    st.info("مرحبا! بدا محادثة جديدة من القائمة الجانبية.")
else:
    st.caption(f"المحادثة: {chat['title']}")

    for message in chat["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("كتب السؤال ديالك هنا...")

    if prompt:
        chat["messages"].append({
            "role": "user",
            "content": prompt
        })

        if chat["title"] == "محادثة جديدة":
            chat["title"] = prompt[:28]

        save_conversations()

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                with st.spinner("كنوجد ليك الجواب..."):
                    history = [
                        {
                            "role": (
                                "user"
                                if m["role"] == "user"
                                else "model"
                            ),
                            "parts": [{"text": m["content"]}]
                        }
                        for m in chat["messages"]
                    ]

                    response = client.models.generate_content(
                        model="gemini-3.5-flash",
                        contents=history
                    )

                    answer = response.text or "ما توصلني حتى جواب."

                st.markdown(answer)

                chat["messages"].append({
                    "role": "assistant",
                    "content": answer
                })
                save_conversations()

            except Exception as error:
    st.error("Gemini request failed")
    st.code(repr(error))
