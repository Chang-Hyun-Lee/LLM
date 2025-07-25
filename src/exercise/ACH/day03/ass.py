import os
import openai
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if api_key is None:
    raise ValueError("❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")

openai.api_key = api_key

st.set_page_config(
    page_title="🧠 멀티턴 챗봇",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 멀티턴 대화 챗봇")
st.markdown("💬 GPT-4 기반 대화형 AI와 자연스럽게 대화를 이어가보세요.")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 기존 대화 렌더링
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("메시지를 입력하세요...")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    messages = []
    for m in st.session_state.chat_history:
        messages.append({"role": m["role"], "content": m["content"]})

    # Assistant API 호출
    with st.chat_message("assistant"):
        response_container = st.empty()
        full_response = ""

        # asst_vKsnmuZX2sUZI9vhdSAEVCK 는 Assistant ID입니다.
        for chunk in openai.assistant.chat.completions.create(
            assistant_id="asst_vKsnmuZX2sUZI9vhdSAEVCK",
            messages=messages,
            stream=True,
        ):
            delta = chunk.choices[0].delta
            if delta.get("content"):
                full_response += delta.content
                response_container.markdown(full_response + "▌")

        response_container.markdown(full_response)
        st.session_state.chat_history.append({"role": "assistant", "content": full_response})

if st.button("🗑️ 대화 초기화"):
    st.session_state.chat_history = []
    st.experimental_rerun()