import streamlit as st
import openai
import os
import time
import random
import json
import sys  # sys.path.append("..")  # 상위 디렉토리 모듈 임포트 가능하게 설정


# OpenAI API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY")  # 또는 직접 입력: openai.api_key = "your-key"

# Generator 함수 정의
def create_generator(history):
    chat_logs = []

    for item in history:
        if item["user"] is not None:  # 사용자
            chat_logs.append({"role": "user", "content": item["user"]})
        if item["bot"] is not None:  # 챗봇
            chat_logs.append({"role": "assistant", "content": item["bot"]})

    messages = [
        {"role": "system", "content": "당신은 친절한 어시스턴트입니다. 사용자의 질문에 친절하게 대답하세요."}
    ]
    messages.extend(chat_logs)

    return openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.5,
        max_tokens=1024,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stream=True
    )

# Streamlit 변경  from gradio
st.set_page_config(page_title="Chatbot", layout="wide")
st.title("Welcome to Chatbot")

# 초기화
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 입력창
user_input = st.chat_input("Your message...")

# 사용자 메시지 처리
if user_input:
    st.session_state.chat_history.append({"user": user_input, "bot": ""})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        bot_response_area = st.empty()
        response_text = ""
        try:
            gen = create_generator(st.session_state.chat_history)
            for chunk in gen:
                delta = chunk.choices[0].delta
                if delta.content:
                    response_text += delta.content
                    bot_response_area.markdown(response_text + "▌")  # 타이핑 효과
            bot_response_area.markdown(response_text)
        except Exception as e:
            response_text = "⚠️ 오류가 발생했습니다: " + str(e)
            bot_response_area.markdown(response_text)

        st.session_state.chat_history[-1]["bot"] = response_text

# 대화 초기화 버튼
if st.button("Clear"):
    st.session_state.chat_history = []
    st.rerun()