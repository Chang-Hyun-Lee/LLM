import os
import streamlit as st
from openai import OpenAI
import time

# 환경변수에서 API 키 읽기
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("환경변수 OPENAI_API_KEY가 설정되어 있지 않습니다.")
    st.stop()

client = OpenAI(api_key=api_key)

ASSISTANT_ID = "asst_vKsnmuZX2sUZI9vhdSAEVCKT"

st.set_page_config(page_title="💬 Assistant 챗봇", layout="centered")
st.title("💬 Assistant 챗봇")

if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id
    st.session_state.messages = []

for role, content in st.session_state.messages:
    with st.chat_message(role):
        st.markdown(content)

user_input = st.chat_input("메시지를 입력하세요...")

if user_input:
    st.session_state.messages.append(("user", user_input))
    with st.chat_message("user"):
        st.markdown(user_input)

    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=user_input
    )

    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=ASSISTANT_ID
    )

    with st.chat_message("assistant"):
        with st.spinner("Assistant가 응답 중입니다..."):
            while True:
                run_status = client.beta.threads.runs.retrieve(
                    thread_id=st.session_state.thread_id,
                    run_id=run.id
                )
                if run_status.status == "completed":
                    break
                elif run_status.status == "failed":
                    st.error("Assistant 처리 실패")
                    break
                time.sleep(1)

            messages = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)
            for msg in messages.data:
                if msg.role == "assistant":
                    assistant_reply = msg.content[0].text.value
                    st.markdown(assistant_reply)
                    st.session_state.messages.append(("assistant", assistant_reply))
                    break
