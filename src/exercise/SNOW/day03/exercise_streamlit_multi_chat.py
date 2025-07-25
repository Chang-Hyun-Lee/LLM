import streamlit as st
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ✅ OpenAI API 키 설정

# 🧠 메시지 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "당신은 친절한 어시스턴트입니다. 사용자의 질문에 친절하게 대답하세요."}
    ]

# 🎨 제목 표시
st.title("🤖 GPT-4o 스트리밍 챗봇")
st.caption("Streamlit을 사용하여 구현됨")

# 💬 이전 대화 표시
for msg in st.session_state.messages[1:]:  # system 메시지는 제외
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ⌨️ 사용자 입력 처리
user_input = st.chat_input("질문을 입력하세요")
if user_input:
    # 사용자 메시지 저장 및 표시
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # ⏳ GPT-4o 스트리밍 응답 표시
    with st.chat_message("assistant"):
        response_box = st.empty()
        full_response = ""

        stream = client.chat.completions.create(model="gpt-4o",
        messages=st.session_state.messages,
        stream=True,
        temperature=0.5,
        max_tokens=4096,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0)

        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            full_response += delta
            response_box.markdown(full_response)

        # 챗봇 메시지 저장
        st.session_state.messages.append({"role": "assistant", "content": full_response})