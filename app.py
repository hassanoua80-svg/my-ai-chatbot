
import os
import re
import json
import uuid
import base64
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from google import genai
from google.genai import types

# ==================================================
# 1. CONFIGURATION
# ==================================================

load_dotenv()

st.set_page_config(
    page_title="My AI Chat",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

MODEL_NAME = "gemini-3.8-flash"
CHAT_FILE = Path("conversations.json")

SYSTEM_INSTRUCTION = """
أنت مساعد ذكي ومحترف.
- أجب دائماً باللغة العربية الفصحى افتراضياً.
- إذا طلب المستخدم الدارجة المغربية، فأجب بالدارجة المغربية.
- إذا كتب المستخدم بالدارجة المغربية، يمكنك الإجابة بنفس اللهجة.
- اشرح البرمجة بطريقة واضحة ومبسطة.
- اعرض الأكواد داخل كتل Markdown وحدد لغة الكود.
- لا تغيّر لغة الإجابة إلا إذا طلب المستخدم ذلك.
- كن دقيقاً، منظماً، ومفيداً.
"""


# ==================================================
# 2. API KEY
# ==================================================

def get_api_key():
    key = os.getenv("GEMINI_API_KEY", "").strip()

    if key:
        return key

    try:
        return st.secrets["GEMINI_API_KEY"].strip()
    except Exception:
        return ""


# ==================================================
# 3. CONVERSATION STORAGE
# ==================================================

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
        st.warning("تعذر حفظ المحادثات محلياً.")


def new_chat():
    chat_id = str(uuid.uuid4())

    st.session_state.chats[chat_id] = {
        "title": "محادثة جديدة",
        "messages": [],
    }

    st.session_state.active_chat = chat_id
    save_chats()


# ==================================================
# 4. FORMAT TEXT AND CODE
# ==================================================

def render_assistant_message(content):
    """
    عرض جواب المساعد مع تنسيق الأكواد.
    الأكواد تظهر داخل st.code مع زر النسخ المدمج.
    """

    pattern = r"```([a-zA-Z0-9_+#.-]*)[ \t]*\n(.*?)```"

    parts = re.split(pattern, content, flags=re.DOTALL)

    i = 0

    while i < len(parts):
        if i + 2 < len(parts):
            if parts[i].strip():
                st.markdown(parts[i])

            language = parts[i + 1].strip() or "text"
            code = parts[i + 2].rstrip("\n")

            st.code(
                code,
                language=language,
                line_numbers=True,
                wrap_lines=True,
            )

            i += 3

        else:
            if parts[i].strip():
                st.markdown(parts[i])

            i += 1


# ==================================================
# 5. COPY ANSWER BUTTON
# ==================================================

def copy_button(content, key):
    encoded = base64.b64encode(
        content.encode("utf-8")
    ).decode("ascii")

    html = """
    <button id="copy-button"
        style="
            background:#f7f7f8;
            border:1px solid #dddddd;
            border-radius:9px;
            padding:7px 12px;
            cursor:pointer;
            font-size:13px;
            color:#333;
        ">
        📋 نسخ الجواب
    </button>

    <script>
    const button = document.getElementById("copy-button");
    const encoded = "__CONTENT__";

    function decodeText(value) {
        const binary = atob(value);
        const bytes = Uint8Array.from(
            binary,
            character => character.charCodeAt(0)
        );
        return new TextDecoder("utf-8").decode(bytes);
    }

    button.addEventListener("click", async () => {
        const text = decodeText(encoded);

        try {
            await navigator.clipboard.writeText(text);
            button.innerText = "✅ تم النسخ";
        } catch (error) {
            const area = document.createElement("textarea");
            area.value = text;
            document.body.appendChild(area);
            area.select();

            const success = document.execCommand("copy");
            area.remove();

            button.innerText = success
                ? "✅ تم النسخ"
                : "تعذر النسخ تلقائياً";
        }
    });
    </script>
    """

    # Prevent HTML/JavaScript injection from the answer.
    html = html.replace("__CONTENT__", encoded)

    components.html(html, height=45)


# ==================================================
# 6. SESSION STATE
# ==================================================

if "chats" not in st.session_state:
    st.session_state.chats = load_chats()

if "active_chat" not in st.session_state:
    st.session_state.active_chat = None

if (
    st.session_state.active_chat
    not in st.session_state.chats
):
    if st.session_state.chats:
        st.session_state.active_chat = next(
            iter(st.session_state.chats)
        )
    else:
        new_chat()


# ==================================================
# 7. PROFESSIONAL DESIGN
# ==================================================

st.markdown(
    """
    <style>
    .stApp {
        background: #ffffff;
        color: #252525;
    }

    header[data-testid="stHeader"] {
        background: rgba(255,255,255,0.95);
    }

    section[data-testid="stSidebar"] {
        background: #f7f7f8;
        border-right: 1px solid #e5e7eb;
    }

    .block-container {
        max-width: 900px;
        padding-top: 1.5rem;
        padding-bottom: 5rem;
    }

    .hero {
        text-align: center;
        padding: 3rem 0 2rem;
    }

    .hero-icon {
        font-size: 48px;
        margin-bottom: 10px;
    }

    .hero h1 {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
    }

    .hero p {
        color: #777777;
        margin-top: 12px;
        font-size: 1rem;
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
        min-height: 40px;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        border-color: #10a37f;
        color: #10a37f;
    }

    .sidebar-title {
        font-size: 1.2rem;
        font-weight: 700;
        padding: 0.5rem 0 1rem;
    }

    .footer-note {
        text-align: center;
        color: #888888;
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


# ==================================================
# 8. SIDEBAR
# ==================================================

with st.sidebar:
    st.markdown(
        '<div class="sidebar-title">💬 My AI Chat</div>',
        unsafe_allow_html=True,
    )

    if st.button("＋ محادثة جديدة", use_container_width=True):
        new_chat()
        st.rerun()

    st.divider()
    st.caption("المحادثات السابقة")

    chat_ids = list(st.session_state.chats.keys())[::-1]

    for chat_id in chat_ids:
        chat = st.session_state.chats[chat_id]
        title = chat.get("title", "محادثة جديدة")

        short_title = (
            title[:25] + "…"
            if len(title) > 25
            else title
        )

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
                state_key = f"delete_mode_{chat_id}"

                st.session_state[state_key] = (
                    not st.session_state.get(state_key, False)
                )

        if st.session_state.get(
            f"delete_mode_{chat_id}", False
        ):
            if st.button(
                "🗑️ حذف المحادثة",
                key=f"delete_{chat_id}",
                use_container_width=True,
            ):
                del st.session_state.chats[chat_id]

                if st.session_state.active_chat == chat_id:
                    st.session_state.active_chat = None

                st.session_state.pop(
                    f"delete_mode_{chat_id}", None
                )

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


# ==================================================
# 9. ACTIVE CONVERSATION
# ==================================================

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


# Display conversation history
for index, message in enumerate(messages):
    role = message.get("role", "assistant")
    content = message.get("content", "")

    with st.chat_message(
        "user" if role == "user" else "assistant"
    ):
        if role == "assistant":
            render_assistant_message(content)
            copy_button(
                content,
                f"history-{active_id}-{index}",
            )
        else:
            st.markdown(content)


# ==================================================
# 10. SEND MESSAGE TO GEMINI
# ==================================================

prompt = st.chat_input("اكتب سؤالك هنا...")

if prompt:
    api_key = get_api_key()

    if not api_key:
        st.error(
            "مفتاح Gemini غير موجود. "
            "أضف GEMINI_API_KEY في Streamlit Secrets."
        )
        st.stop()

    # Save user message
    messages.append({
        "role": "user",
        "content": prompt,
    })

    if current_chat["title"] == "محادثة جديدة":
        current_chat["title"] = prompt[:40]

    save_chats()

    # Display user message immediately
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            client = genai.Client(api_key=api_key)

            history = []

            for message in messages:
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

            with st.spinner("جاري التفكير..."):
                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=history,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION
                    ),
                )

            answer = response.text or (
                "لم أتمكن من إنشاء جواب. حاول مرة أخرى."
            )

            render_assistant_message(answer)
            copy_button(
                answer,
                f"new-{uuid.uuid4().hex[:8]}",
            )

            messages.append({
                "role": "assistant",
                "content": answer,
            })

            save_chats()

        except Exception as error:
            if messages and messages[-1]["role"] == "user":
                messages.pop()
                save_chats()

            st.error("وقع مشكل أثناء الاتصال بـ Gemini.")
            st.code(repr(error))

# ==================================================
# 11. FOOTER
# ==================================================

st.markdown(
    """
    <div class="footer-note">
        تحقق من المعلومات المهمة قبل الاعتماد عليها.
    </div>
    """,
    unsafe_allow_html=True,
)
