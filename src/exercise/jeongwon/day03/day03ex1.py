import os
import openai
from openai import OpenAI
import time
import streamlit as st
import random

openai.api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI()
st.title("chat-bot")

user_input = st.text_input("질문을 입력하세요")

if "chat_log" not in st.session_state:
    st.session_state.chat_log =[]

if user_input:
    st.session_state.chat_log.append(("user",user_input))

    with st.spinner("답변중입니다."):
        response = client.chat.completions.create(
            model = "gpt-4o-mini",
            messages =[ {"role": "system",
          "content": "당신은 친절한 어시스턴트입니다. 사용자의 질문에 친절하게 대답하세요."
        }, 
        *[
        {
        "role": role, "content": msg
        }
        for role, msg in st.session_state.chat_log
            ]
            ]
        )

        reply  = response.choices[0].message.content
        st.session_state.chat_log.append(("assistant", reply))

for role, msg in st.session_state.chat_log:
    st.markdown(f"{role} : {msg}")