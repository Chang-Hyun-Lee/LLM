# streamlit_chat_app.py

import streamlit as st
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

st.title("멀티턴 스트리밍 챗봇")

# 시스템 역할 정의
system_prompt = {
    "role": "system",
    "content": "당신은 친절한 어시스턴트입니다. 사용자의 질문에 친절하게 대답하세요."
}

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = [system_prompt]

# 이전 메시지 출력
for msg in st.session_state.messages:
    if msg["role"] in ["user", "assistant"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# 입력창
user_input = st.chat_input("메시지를 입력하세요.")

# GPT 응답 스트리밍 처리
def stream_gpt_response(messages):
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.5,
        stream=True
    )
    full_reply = ""
    for chunk in response:
        delta = chunk.choices[0].delta
        if delta and delta.content:
            full_reply += delta.content
            yield full_reply

# 사용자 입력 처리
if user_input:
    # 1. 유저 메시지 저장 및 출력
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 2. GPT 응답 준비
    with st.chat_message("assistant"):
        msg_box = st.empty()
        reply_text = ""
        for partial in stream_gpt_response(st.session_state.messages):
            reply_text = partial
            msg_box.markdown(reply_text)

    # 3. 전체 응답 저장
    st.session_state.messages.append({"role": "assistant", "content": reply_text})

# 초기화 버튼
if st.button("대화 초기화"):
    st.session_state.messages = [system_prompt]
    st.rerun()
