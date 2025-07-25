import streamlit as st
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("Streamlit으로 만든 채팅 App")

# 기존 메시지 출력 (순서대로)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 사용자 입력
if prompt := st.chat_input("메시지를 입력하세요"):
    # 사용자 메시지 기록 및 출력
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # GPT 응답 받기
    with st.chat_message("assistant"):
        response_container = st.empty()  # 채팅 실시간 출력할 자리
        full_response = ""

        response_stream = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            stream=True,
            temperature=0.5,
            max_tokens=1024,
        )

        for chunk in response_stream:
            if chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content
                response_container.markdown(full_response + "▌")

        response_container.markdown(full_response)  # 최종 응답 표시
        st.session_state.messages.append({"role": "assistant", "content": full_response})

    # 📌 자동 스크롤 (Streamlit은 내장 지원 없음 → 아래에 빈 공간 넣는 방식)
    st.write("")  # 여유 공간
    st.markdown(
        """
        <script>
        var bottom = document.body.scrollHeight;
        window.scrollTo({top: bottom, behavior: 'smooth'});
        </script>
        """,
        unsafe_allow_html=True,
    )
