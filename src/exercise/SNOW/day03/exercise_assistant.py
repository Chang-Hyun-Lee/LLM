import streamlit as st
import openai
import uuid

# 시크릿에서 키 불러오기
openai.api_key = st.secrets["OPENAI_API_KEY"]
assistant_id = "asst_vKsnmuZX2sUZI9vhdSAEVCKT"

# 세션 상태 초기화
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.title("🤖 Assistant API 챗봇")
st.caption("세션을 유지하며 Assistant와 멀티턴 대화합니다")

# Thread가 없다면 새로 생성
if st.session_state.thread_id is None:
    thread = openai.beta.threads.create()
    st.session_state.thread_id = thread.id

# 이전 대화 표시
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 입력 처리
user_input = st.chat_input("메시지를 입력하세요")
if user_input:
    # 사용자 메시지 추가
    with st.chat_message("user"):
        st.markdown(user_input)

    st.session_state.chat_history.append({"role": "user", "content": user_input})

    # 메시지 추가
    openai.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=user_input
    )

    # 실행 및 스트리밍 응답 표시
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""

        run = openai.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=assistant_id,
            stream=True  # ✅ 스트리밍 응답
        )

        for chunk in run:
            if chunk.event == "thread.message.delta":
                delta = chunk.data.delta
                if delta.content:
                    full_response += delta.content[0].text.value
                    placeholder.markdown(full_response)

        st.session_state.chat_history.append({"role": "assistant", "content": full_response})