import streamlit as st
import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

if "messages" not in st.session_state:
    st.session_state["messages"] = []

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_input = st.chat_input("메시지를 입력하세요...")

if user_input:
    
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=st.session_state["messages"]  # 이전 대화 전체를 맥락으로 전달
    )
    assistant_reply = response.choices[0].message.content

    st.session_state["messages"].append({"role": "assistant", "content": assistant_reply})
    with st.chat_message("assistant"):
        st.write(assistant_reply)
