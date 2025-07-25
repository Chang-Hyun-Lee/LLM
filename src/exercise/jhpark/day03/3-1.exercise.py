import streamlit as st
import openai
import uuid
import os
from openai import OpenAI

# OpenAI API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY")

# 미리 생성된 Assistant ID
ASSISTANT_ID = "asst_vKsnmuZX2sUZI9vhdSAEVCKT"

# 세션 초기화
if "thread_id" not in st.session_state:
    thread = openai.beta.threads.create()
    st.session_state.thread_id = thread.id
    st.session_state.messages = []

# 타이틀
st.title("🧠 Assistant API 기반 멀티턴 챗봇")

# 사용자 입력 받기
user_input = st.text_input("💬 메시지를 입력하세요:", key="input")

if user_input:
    # 사용자 메시지 Thread에 추가
    openai.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=user_input,
    )

    # 채팅 기록에 사용자 메시지 추가
    st.session_state.messages.append(("user", user_input))

    # Assistant 실행 요청
    run = openai.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=ASSISTANT_ID,
    )

    # 응답 완료까지 대기
    with st.spinner("Assistant가 답변 중입니다..."):
        while True:
            run_status = openai.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id,
                run_id=run.id,
            )
            if run_status.status == "completed":
                break

    # 응답 메시지 가져오기
    messages = openai.beta.threads.messages.list(
        thread_id=st.session_state.thread_id
    )

    # 가장 마지막 Assistant 응답 추출
    for msg in reversed(messages.data):
        if msg.role == "assistant":
            assistant_response = msg.content[0].text.value
            st.session_state.messages.append(("assistant", assistant_response))
            break

# 전체 메시지 출력
for role, message in st.session_state.messages:
    if role == "user":
        st.markdown(f"🧑‍💻 **You:** {message}")
    else:
        st.markdown(f"🤖 **Assistant:** {message}")
