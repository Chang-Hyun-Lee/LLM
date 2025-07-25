import streamlit as st
import pandas as pd
from datetime import datetime as dt
import datetime
import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")
# conversation_history = []

if 'message' not in st.session_state:
    st.session_state.messages = []
    st.write(f"저장 안됨: {st.session_state.messages}")

if 'message' in st.session_state:    
    st.write(f"저장 내용: {st.session_state.messages}")

conversation_history = st.session_state.messages

def greet(input_string):
    # conversation_history.append({"role": "user", "content": input_string})
    st.session_state.messages.append('message', {"role": "user", "content": input_string})
    response = openai.chat.completions.create(
    model="gpt-4o-mini",
    messages=conversation_history,
    temperature=0.5,
    max_tokens=256,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0
    )

    response_text = response.choices[0].message.content
    conversation_history.append({"role": "assistant", "content": response_text})

    return response_text

chat1 = st.text_input(
    label='채팅', 
    placeholder='여기에서 채팅해요.'
)
st.write(f"채팅 내용: {chat1}")
strResponse = greet(chat1)

st.text_area(
    label='채팅 내용',
    value = strResponse)





