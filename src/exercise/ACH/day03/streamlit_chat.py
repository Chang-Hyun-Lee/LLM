# app.py

import os
import openai
import streamlit as st
from dotenv import load_dotenv

# ✅ 환경변수 로드
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if api_key is None:
    raise ValueError("❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")

openai.api_key = api_key

# ✅ 페이지 설정
st.set_page_config(
    page_title="🧠 멀티턴 챗봇",
    page_icon="🤖",
    layout="centered"
)

# ✅ 타이틀 및 설명
st.title("🤖 멀티턴 대화 챗봇")
st.markdown("💬 GPT-4 기반 대화형 AI와 자연스럽게 대화를 이어가보세요.")

# ✅ 세션 상태 초기화
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ✅ 기존 대화 렌더링
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ✅ 사용자 입력 받기
user_input = st.chat_input("메시지를 입력하세요...")

# ✅ 사용자 입력 처리
if user_input:
    # 사용자 메시지 표시 및 기록
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 메시지 목록 구성
    messages = [{"role": "system", "content": "저는 도움을 주는 AI 어시스턴트입니다. 어떻게 도와드릴까요?"}]
    for m in st.session_state.chat_history:
        messages.append({"role": m["role"], "content": m["content"]})

    # GPT 응답 생성
    with st.chat_message("assistant"):
        response_container = st.empty()
        full_response = ""

        for chunk in openai.chat.completions.create(
            model="gpt-4",
            messages=messages,
            stream=True,
        ):
            if chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content
                response_container.markdown(full_response + "▌")

        response_container.markdown(full_response)
        # GPT 응답 저장
        st.session_state.chat_history.append({"role": "assistant", "content": full_response})

# ✅ 대화 초기화 버튼
if st.button("🗑️ 대화 초기화"):
    st.session_state.chat_history = []
    st.experimental_rerun()

#streamlit run streamlit_chat.py