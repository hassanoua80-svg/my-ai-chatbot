
import os
import json
import uuid
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
from google import genai

# -------------------- Configuration --------------------

load_dotenv()

st.set_page_config(
    page_title="My AI Chatbot",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

CHAT_FILE = "conversations.json"
MODEL_NAME = "gemini-2.5-flash"


# -------------------- API Key --------------------

def get_api_key():
    key = os.getenv("GEMINI_API_KEY")

    if key:
        return key

    try:
        return st.secrets["GEMINI_API_KEY"]
    except (KeyError, FileNotFoundError):
        return None


API_KEY = get_api_key()

if not API_KEY:
    st.error(
        "مفتاح Gemini API غير موجود. "
        "أضفه في Streamlit Secrets."
    )
    st.stop()


@st.cache_resource
def get_client(api_key):
    return genai.Client(api_key=api_key)


client = get_client(API_KEY)


# -------------------- Conversations --------------------

def new_chat():
    chat_id = str(uuid.uuid4())

    return {
        "id": chat_id,
        "title": "محادثة جديدة",
        "messages": [],
        "created_at": datetime.now().isoformat(),
    }


def load_conversations():
    if not os.path.exists(CHAT_FILE):
        return []

    try:
        with open(CHAT_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        return data if isinstance(data, list) else []

    except (json.JSONDecodeError, OSError):
        return []


def save_conversations():
    try:
        with open(CHAT_FILE, "w", encoding="utf-8") as file:
            json.dump(
                st.session_state.conversations,
                file,
                ensure_ascii=False,
                indent=2,
            )
    except OSError:
        st.warning(
            "تعذر حفظ المحادثات على الخادم. "
            "قد لا تبقى محفوظة بعد إعادة تشغيل التطبيق."
        )


if "conversations" not in st.session_state:
    st.session_state.conversations = load_conversations()

if "active_chat_id" not in st.session_state:
    if st.session_state.conversations:
        st.session_state.active_chat_id = (
            st.session_state.conversations[0]["id"]
        )
    else:
        chat = new_chat()
        st.session_state.conversations = [chat]
        st.session_state.active_chat_id = chat["id"]
        save_conversations()


def get_active_chat():
    for chat in st.session_state.conversations:
        if chat["id"] == st.session_state.active_chat_id:
            return chat

    chat = new_chat()
    st.session_state.conversations.insert(0, chat)
    st.session_state.active_chat_id = chat["id"]
    save_conversations()
    return chat


# -------------------- Sidebar --------------------

with st.sidebar:
    st.title("💬 My AI Chatbot")
    st.caption("مساعدك الذكي باستعمال Gemini")

    if st.button("＋ محادثة جديدة", use_container_width=True):
        chat = new_chat()
        st.session_state.conversations.insert(0, chat)
        st.session_state.active_chat_id = chat["id"]
        save_conversations()
        st.rerun()

    st.divider()
    st.subheader("محادثاتي")

    for chat in st.session_state.conversations:
        col1, col2 = st.columns([5, 1])

        with col1:
            label = chat.get("title", "محادثة جديدة")[:28]

            if st.button(
                label,
                key=f"open_{chat['id']}",
                use_container_width=True,
            ):
                st.session_state.active_chat_id = chat["id"]
                st.rerun()

        with col2:
            if st.button("🗑️", key=f"delete_{chat['id']}"):
                st.session_state.conversations = [
                    item
                    for item in st.session_state.conversations
                    if item["id"] != chat["id"]
                ]

                if not st.session_state.conversations:
                    replacement = new_chat()
                    st.session_state.conversations = [replacement]
                    st.session_state.active_chat_id = replacement["id"]

                elif st.session_state.active_chat_id == chat["id"]:
                    st.session_state.active_chat_id = (
                        st.session_state.conversations[0]["id"]
                    )

                save_conversations()
                st.rerun()

    st.divider()
    st.caption("Powered by Google Gemini")


# -------------------- Main Chat Interface --------------------

chat = get_active_chat()

st.title("💬 المحادثة")
st.caption(f"المحادثة: {chat['title']}")

if not chat["messages"]:
    st.info(
        "مرحبا بك! 👋\n\n"
        "كتب سؤالك في الأسفل، وغادي نعاونك."
    )

# Display previous messages
for message in chat["messages"]:
    role = message.get("role", "user")

    with st.chat_message(
        "assistant" if role == "assistant" else "user"
    ):
        st.markdown(message.get("content", ""))


# -------------------- Send Message --------------------

prompt = st.chat_input("كتب السؤال ديالك هنا...")

if prompt:
    prompt = prompt.strip()

    if prompt:
        chat["messages"].append({
            "role": "user",
            "content": prompt,
        })

        if chat["title"] == "محادثة جديدة":
            chat["title"] = prompt[:35]

        save_conversations()

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                with st.spinner("Gemini كيوجد ليك الجواب..."):
                    history = []

                    for message in chat["messages"]:
                        history.append({
                            "role": (
                                "user"
                                if message["role"] == "user"
                                else "model"
                            ),
                            "parts": [
                                {"text": message["content"]}
                            ],
                        })

                    response = client.models.generate_content(
                        model=MODEL_NAME,
                        contents=history,
                    )

                    answer = response.text

                    if not answer:
                        answer = "ما توصلني حتى جواب. جرّب سؤال آخر."

                    st.markdown(answer)

                    chat["messages"].append({
                        "role": "assistant",
                        "content": answer,
                    })

                    save_conversations()

            except Exception as error:
                st.error(
                    "وقع مشكل أثناء الاتصال بـ Gemini. "
                    "شوف تفاصيل الخطأ أسفله."
                )
                st.code(repr(error))
