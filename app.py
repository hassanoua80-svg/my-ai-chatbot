
import os
import json
import uuid
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from google import genai

# ---------------- Configuration ----------------
load_dotenv()

st.set_page_config(
    page_title="My AI Chat",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

MODEL_NAME = "gemini-3.8-flash"
CHAT_FILE = Path("conversations.json")


# ---------------- API key ----------------
def get_api_key():
    key = os.getenv("GEMINI_API_KEY", "").strip()

    if key:
        return key

    try:
        return st.secrets["GEMINI_API_KEY"].strip()
    except Exception:
        return ""


# ---------------- Conversation storage ----------------
def load_chats():
    if not CHAT_FILE.exists():
        return {}

    try:
        with CHAT_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_chats():
    try:
        with CHAT_FILE.open("w", encoding="utf-8") as file:
            json.dump(
                st.session_state.chats,
                file,
                ensure_ascii=False,
                indent=2,
            )
    except OSError:
        st.warning("تعذر حفظ المحادثات في الملف المحلي.")


def new_chat():
    chat_id = str(uuid.uuid4())
    st.session_state.chats[chat_id] = {
        "title": "محادثة جديدة",
        "messages": [],
    }
    st.session_state.active_chat = chat_id
    save_chats()


# ---------------- Session initialization ----------------
if "chats" not in st.session_state:
    st.session_state.chats = load_chats()

if "active_chat" not in st.session_state:
    st.session_state.active_chat = None

if (
    st.session_state.active_chat not in st.session_state.chats
    and st.session_state.chats
):
    st.session_state.active_chat = next(iter(st.session_state.chats))

if not st.session_state.chats:
    new_chat()


# ---------------- Professional design ----------------
st.markdown(
    """
    <style>
    :root {
        --background: #ffffff;
        --sidebar: #f7f7f8;
        --text: #252525;
        --border: #e5e7eb;
        --accent: #10a37f;
    }

    .stApp {
        background: var(--background);
        color: var(--text);
    }

    header[data-testid="stHeader"] {
        background: rgba(255,255,255,0.95);
    }

    section[data-testid="stSidebar"] {
        background: var(--sidebar);
        border-right: 1px solid var(--border);
    }

    .block-container {
        max-width: 900px;
        padding-top: 1.5rem;
        padding-bottom: 5rem;
    }

    .hero {
        text-align: center;
        padding: 2rem 0 1.5rem;
    }

    .hero-icon {
        font-size: 44px;
        margin-bottom: 8px;
    }

    .hero h1 {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -1px;
    }

    .hero p {
        color: #777;
        font-size: 1rem;
        margin-top: 10px;
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
        min-height: 42px;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        border-color: var(--accent);
        color: var(--accent);
    }

    .sidebar-heading {
        font-size: 1.2rem;
        font-weight: 700;
        padding: 0.5rem 0 1rem;
    }

    .footer-note {
        text-align: center;
        color: #888;
        font-size: 0.8rem;
        padding-top: 1.5rem;
    }

    @media (max-width: 768px) {
        .block-container {
            padding: 0.8rem 0.6rem 4rem;
        }

        .hero h1 {
            font-size: 1.8rem;
        }

        [data-testid="stChatMessage"] {
            padding: 0.8rem;
            border-radius: 12px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------- Sidebar ----------------
with st.sidebar:
    st.markdown(
        '<div class="sidebar-heading">💬 My AI Chat</div>',
        unsafe_allow_html=True,
    )

    if st.button("＋ محادثة جديدة", use_container_width=True):
        new_chat()
        st.rerun()

    st.divider()
    st.caption("محادثاتك السابقة")

    # Most recent conversations first
    chat_ids = list(st.session_state.chats.keys())[::-1]

    for chat_id in chat_ids:
        chat = st.session_state.chats[chat_id]
        title = chat.get("title", "محادثة جديدة")
        short_title = title[:27] + ("…" if len(title) > 27 else "")

        col1, col2 = st.columns([5, 1])

        with col1:
            if st.button(
                f"💬 {short_title}",
                key=f"open_{chat_id}",
                use_container_width=True,
            ):
                st.session_state.active_chat = chat_id
                st.rerun()

        with col2:
            if st.button("⋯", key=f"menu_{chat_id}"):
                st.session_state[f"show_delete_{chat_id}"] = (
                    not st.session_state.get(f"show_delete_{chat_id}", False)
                )

        if st.session_state.get(f"show_delete_{chat_id}", False):
            if st.button(
                "🗑️ حذف المحادثة",
                key=f"delete_{chat_id}",
                use_container_width=True,
            ):
                del st.session_state.chats[chat_id]
                st.session_state.pop(f"show_delete_{chat_id}", None)

                if st.session_state.active_chat == chat_id:
                    st.session_state.active_chat = None

                if not st.session_state.chats:
                    new_chat()
                else:
                    st.session_state.active_chat = next(
                        iter(st.session_state.chats)
                    )

                save_chats()
                st.rerun()

    st.divider()
    st.caption("مدعوم بالذكاء الاصطناعي Gemini")


# ---------------- Current chat ----------------
active_id = st.session_state.active_chat

if active_id not in st.session_state.chats:
    new_chat()
    active_id = st.session_state.active_chat

current_chat = st.session_state.chats[active_id]
messages = current_chat["messages"]


if not messages:
    st.markdown(
        """
        <div class="hero">
            <div class="hero-icon">💬</div>
            <h1>المحادثة</h1>
            <p>مرحباً بك! كيف يمكنني مساعدتك اليوم؟</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown("## 💬 المحادثة")


# Display previous messages
for message in messages:
    role = message.get("role", "assistant")
    content = message.get("content", "")

    with st.chat_message(
        "user" if role == "user" else "assistant"
    ):
        st.markdown(content)


# ---------------- Send a message ----------------
prompt = st.chat_input("اكتب سؤالك هنا...")

if prompt:
    api_key = get_api_key()

    if not api_key:
        st.error(
            "مفتاح Gemini غير موجود. أضف GEMINI_API_KEY في "
            "Streamlit Secrets."
        )
        st.stop()

    # Save and display user message
    messages.append({"role": "user", "content": prompt})

    if current_chat["title"] == "محادثة جديدة":
        current_chat["title"] = prompt[:40]

    save_chats()

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            client = genai.Client(api_key=api_key)

            history = []
            for message in messages:
                history.append(
                    {
                        "role": (
                            "user"
                            if message["role"] == "user"
                            else "model"
                        ),
                        "parts": [{"text": message["content"]}],
                    }
                )

            with st.spinner("جاري التفكير..."):
                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=history,
                )

            answer = response.text

            if not answer:
                answer = "لم أتمكن من إنشاء جواب. حاول مرة أخرى."

            st.markdown(answer)

            messages.append(
                {"role": "assistant", "content": answer}
            )
            save_chats()

        except Exception as error:
            # Remove the unanswered user message so it can be retried
            if messages and messages[-1]["role"] == "user":
                messages.pop()
                save_chats()

            st.error("وقع مشكل أثناء الاتصال بـ Gemini.")
            st.code(repr(error))

st.markdown(
    '<div class="footer-note">'
    'تحقق من المعلومات المهمة قبل الاعتماد عليها.'
    '</div>',
    unsafe_allow_html=True,
)
