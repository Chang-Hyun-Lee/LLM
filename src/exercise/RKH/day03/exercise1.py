import gradio as gr
import time
import openai
import os

import streamlit as st

openai.api_key = os.getenv("OPENAI_API_KEY")

def sendLang():
    messages = [{"role": "system", "content": "당신은 친절한 AI 비서입니다."}]
    #messages.append({"role": "user", "content": prompt})
    
    #for user, bot in history:
    #    if user:
    #        messages.append({"role": "user", "content": user})
    #    if bot:
    #        messages.append({"role": "assistant", "content": bot})
    

    messages = [{"role": "system", "content": "당신은 친절한 AI 비서입니다."}]
    messages.extend(st.session_state.messages)  # 이전 메시지들 추가

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.5,
        max_tokens=1024,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    result = response.choices[0].message.content
    return result

if "messages" not in st.session_state:
    st.session_state.messages = []

# 기존 채팅 기록 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 사용자 입력 처리
if prompt := st.chat_input("말씀해주세요."):
    # 사용자 입력 표시 및 저장
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 응답 생성 및 표시
    response = sendLang()
    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})