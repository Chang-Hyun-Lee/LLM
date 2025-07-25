#  실습 #1: Streamlit과 Assistant API를 이용하여 세션을 유지하는 멀티턴 챗봇을 만드시오. 단 Assistant는 미리 만들어서 id를 얻어둔다. (시간이 된다면) stream 기능을 추가한다.

#  asst_UIoILByMFhNJ0Q18C0m69eko

import os
import streamlit as st
from openai import OpenAI

# OpenAI 클라이언트 생성
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 미리 생성된 Assistant ID
ASSISTANT_ID = "asst_UIoILByMFhNJ0Q18C0m69eko"

# Streamlit 페이지 설정
st.set_page_config(page_title="Assistant API Chatbot", page_icon="🤖")
st.title("🤖 Assistant API 멀티턴 챗봇 (스트리밍 지원)")

# 세션 초기화
if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id
    st.session_state.messages = []

# 사용자 입력
user_input = st.text_input("메시지를 입력하세요:")

# 사용자 메시지 전송
if st.button("전송") and user_input.strip():
    # Thread에 사용자 메시지 추가
    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=user_input
    )
    st.session_state.messages.append(("user", user_input))

    # 스트리밍으로 Assistant 응답 받기
    placeholder = st.empty()
    response_text = ""

    with client.beta.threads.runs.stream(
        thread_id=st.session_state.thread_id,
        assistant_id=ASSISTANT_ID
    ) as stream:
        for event in stream:
            if event.type == "response.output_text.delta":
                response_text += event.delta
                placeholder.markdown(f"**🤖 어시스턴트:** {response_text}")
        stream.until_done()

    st.session_state.messages.append(("assistant", response_text))

# 이전 대화 출력
for role, msg in st.session_state.messages:
    if role == "user":
        st.markdown(f"**🙋 사용자:** {msg}")
    else:
        st.markdown(f"**🤖 어시스턴트:** {msg}")


for msg in sessionstate:
    with msg("role"):
        msg("content")