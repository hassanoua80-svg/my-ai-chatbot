
import os
import streamlit as st
from dotenv import load_dotenv
from google import genai

load_dotenv()

st.set_page_config(
    page_title="My AI Chatbot",
    page_icon="🤖",
    layout="centered"
)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("تأكد من وجود GEMINI_API_KEY داخل ملف .env")
    st.stop()

client = genai.Client(api_key=api_key)

st.markdown("""
<style>
.stApp {
    background-color: #f7f8fc;
}
.block-container {
    max-width: 850px;
    padding-top: 2rem;
}
.stChatMessage {
    border-radius: 16px;
    padding: 12px;
}
h1 {
    color: #3438a5;
}
</style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.title("🤖 مساعدي الذكي")
    st.caption("مساعدك الشخصي باستعمال Gemini")

    if st.button("➕ محادثة جديدة", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.write("💬 المحادثة الحالية")
    st.caption("تقدر تبدا محادثة جديدة فالوقت اللي بغيتي.")

st.title("🤖 My AI Chatbot")
st.write("مرحبا بك! سولني على البرمجة أو أي موضوع آخر.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("كتب السؤال ديالك هنا..."):
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    history = []

    for message in st.session_state.messages:
        history.append({
            "role": "user" if message["role"] == "user" else "model",
            "parts": [{"text": message["content"]}]
        })

    try:
        with st.spinner("⏳ Gemini كيوجد الجواب..."):
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=history
            )

        answer = response.text or "ما توصلني حتى جواب."

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

        with st.chat_message("assistant"):
            st.markdown(answer)

    except Exception:
        st.error(
            "وقع مشكل فالاتصال بـ Gemini. "
            "تأكد من المفتاح واسم الموديل والإنترنت."
        )
