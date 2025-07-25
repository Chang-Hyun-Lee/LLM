# gradio로 만든 멀티턴 채팅 어플리케이션을 stramlit으로 유사하게 구현하시오.

import streamlit as st
import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

if "history" not in st.session_state:
    st.session_state.history = []

for message in st.session_state.history:
    user_msg, bot_msg = message
    with st.chat_message("user"):
        st.markdown(user_msg)
    with st.chat_message("assistant"):
        st.markdown(bot_msg)
        
user_input = st.chat_input("질문 입력!")

def stream_response(history):
    messages = [
        {"role": "system", "content": "당신은 친절한 어시스턴트입니다. 사용자의 질문에 친절하게 대답하세요."}
    ]

    for user, bot in history:
        messages.append({"role": "user", "content": user})
        messages.append({"role": "assistant", "content": bot})

    messages.append({"role": "user", "content": user_input})

    stream = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.5,
        max_tokens=1024,
        stream=True
    )

    response_text = ""
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                response_text += delta.content
                message_placeholder.markdown(response_text + "▌")
        message_placeholder.markdown(response_text)
    
    return response_text


if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)

    response = stream_response(st.session_state.history)
    st.session_state.history.append((user_input, response))
