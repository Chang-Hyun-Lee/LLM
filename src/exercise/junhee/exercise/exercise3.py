# 실습: gradio로 만든 멀티턴 채팅 어플리케이션을 streamlit으로 유사하게 구현하시오.

import streamlit as st
import random
import time
import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")


st.title("멋쟁이 ChatBot")

# 채팅 초기 화면 출력 
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "당신은 친절한 AI 챗봇입니다."},
        {"role": "assistant", "content": "안녕! 무엇이 궁금해?"}
    ]

for message in st.session_state.messages[1:]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])



# 사용자 입력 받기
if prompt := st.chat_input("텍스트를 입력하고 엔터를 치거나 이미지를 업로드하세요"):
    # 사용자의 입력을 추가하기
    st.session_state.messages.append({"role": "user", "content": prompt})
    # 사용자의 입력을 보여주기
    with st.chat_message("user"):
        st.markdown(prompt)

    # 챗봇 응답 생성 및 출력
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        assistant_response = openai.ChatCompletion.create(
            model = "gpt-4o",
            messages = st.session_state.messages,
            temperature = 0.7,
            stream = True
        )
        
        for chunk in assistant_response:
            if "choices" in chunk:
                delta = chunk["choices"][0]["delta"]
                if "content" in delta:
                    full_response += delta["content"]
                    message_placeholder.markdown(full_response + "▌")
                    time.sleep(0.03)
        message_placeholder.markdown(full_response)

    # 챗봇의 답변 추가
    st.session_state.messages.append({"role": "assistant", "content": full_response})