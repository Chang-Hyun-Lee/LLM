import streamlit as st
import openai
import time

# 페이지 설정
st.set_page_config(page_title="JL Assistant", page_icon="📘")
st.title("📘 JLPT GPT-4 어시스턴트")
st.markdown("일본어 문장, 단어, 표현에 대해 자유롭게 질문해보세요!")

# OpenAI API 키 입력 받기
api_key = st.text_input("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", type="password")
assistant_id = "asst_D821axlkyNeIJiWcCY808LZh"  # 정확한 Assistant ID 입력

# 세션 상태 초기화
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# API 키가 있을 때만 실행
if api_key:
    openai.api_key = api_key

    if not st.session_state.thread_id:
        thread = openai.beta.threads.create()
        st.session_state.thread_id = thread.id

    user_input = st.text_input("✍️ 질문을 입력하세요:")

    if st.button("질문하기") and user_input:
        st.session_state.messages.append(("user", user_input))

        openai.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=user_input
        )

        run = openai.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=assistant_id,
        )

        with st.spinner("JL Assistant가 응답 중입니다..."):
            while True:
                run_status = openai.beta.threads.runs.retrieve(
                    thread_id=st.session_state.thread_id,
                    run_id=run.id,
                )
                if run_status.status == "completed":
                    break
                time.sleep(1)

        messages = openai.beta.threads.messages.list(thread_id=st.session_state.thread_id)
        answer = messages.data[0].content[0].text.value
        st.session_state.messages.append(("assistant", answer))

    # 채팅 UI 출력
    for role, msg in reversed(st.session_state.messages):
        if role == "user":
            st.markdown(f"**🙋‍♂️ 질문:** {msg}")
        else:
            st.markdown(f"**🤖 JL Assistant:** {msg}")
else:
    st.warning("먼저 OpenAI API 키를 입력하세요.")
