## 실습 #1: gradio로 만든 멀티턴 채팅 어플리케이션을 streamlit으로 유사하게 구현하시오.

import streamlit as st
import os
from dotenv import load_dotenv
from openai import OpenAI
import random
import time

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.title('심플쳇봇만들기')

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Let's start chatting! 👇"}]

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("질문을 입력해 주세요..."): 
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        assistant_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages= st.session_state.messages,
        )
        st.session_state.messages.append({"role": "assistant", "content": assistant_response.choices[0].message.content})

        # Simulate stream of response with milliseconds delay
        message_placeholder = st.empty()
        full_response = ""
        for chunk in assistant_response.choices[0].message.content.split():
            full_response += chunk + " "
            time.sleep(0.05)
            # Add a blinking cursor to simulate typing
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
 
