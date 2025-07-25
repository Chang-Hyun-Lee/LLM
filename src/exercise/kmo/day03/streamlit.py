import streamlit as st
from openai import OpenAI
import os

# OpenAI client 객체 생성 (환경변수에서 API 키 읽음)
client = OpenAI()

# Streamlit 설정
st.set_page_config(page_title="Chat with GPT", page_icon="💬")
st.title("💬 GPT 멀티턴 채팅")

# 대화 세션 초기화
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": "당신은 친절한 AI 도우미입니다."}]

# 이전 대화 출력
for msg in st.session_state.messages[1:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 사용자 입력
prompt = st.chat_input("메시지를 입력하세요...")

if prompt:
    # 사용자 메시지 저장 및 출력
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # GPT 응답 출력
    with st.chat_message("assistant"):
        with st.spinner("GPT가 생각 중..."):
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=st.session_state.messages,
                stream=True
            )

            full_response = ""
            placeholder = st.empty()
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    placeholder.markdown(full_response)

    # 응답 저장
    st.session_state.messages.append({"role": "assistant", "content": full_response})