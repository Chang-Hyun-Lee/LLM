# 실습 #1: gradio로 만든 멀티턴 채팅 어플리케이션을 streamlit으로 유사하게 구현하시오.

import openai                    # OpenAI 라이브러리 임포트
import os                        # 환경변수를 사용하기 위한 os 모듈
import streamlit as st           # Streamlit 앱을 만들기 위한 라이브러리

# OpenAI API 키를 환경변수에서 불러오기
openai.api_key = os.getenv("OPENAI_API_KEY")
# ※ 만약 환경변수를 사용하지 않는다면 아래처럼 직접 입력도 가능함:
# openai.api_key = "sk-..."

# GPT와 대화를 수행하는 함수
def chat_with_bot(messages):
    # OpenAI Chat API 호출 (스트리밍 응답 사용)
    gen = openai.chat.completions.create(
        model="gpt-4o-mini",           # 사용할 모델 (gpt-4o-mini, gpt-3.5-turbo 등)
        messages=messages,             # 지금까지의 대화 내역을 전달
        temperature=0.7,               # 창의성 설정 (높을수록 다양성 ↑)
        max_tokens=4096,               # 최대 생성 토큰 수
        stream=True                    # 스트리밍 응답 사용 (단계적으로 답변 받기)
    )
    return gen                         # 제너레이터 형태로 반환됨

# Streamlit 앱을 정의하는 main 함수
def main():
    st.title("Multi-turn Chatbot with Streamlit and OpenAI")  # 앱 제목 표시

    # 사용자 입력창 표시 (st.chat_input은 입력 시 자동 submit됨)
    st.chat_input(placeholder="대화를 입력해주세요.", key="chat_input")

    # 세션 상태에 messages(대화기록)가 없으면 초기화
    if "messages" not in st.session_state:
        st.session_state.messages = []        

    # 저장된 대화기록을 순차적으로 출력
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):                 # 사용자 또는 GPT의 말풍선
            st.markdown(message["content"])                    # 대화 내용 표시

    # 사용자가 입력한 텍스트 가져오기
    if user_input := st.session_state["chat_input"]:
        # 사용자 메시지 출력
        with st.chat_message("user"):
            st.markdown(user_input)
        # 사용자 메시지를 세션에 저장
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })

        # GPT에 대화 내역 전달하여 응답 받기 (스트리밍)
        gen = chat_with_bot(st.session_state.messages)

        # GPT의 응답 출력 영역 준비
        with st.chat_message("assistant"):
            message_placeholder = st.empty()   # 실시간 출력할 공간
            full_response = ""                 # 전체 GPT 응답을 저장할 문자열

            # 스트리밍으로 한 덩어리씩 응답을 받으며 출력
            for chunk in gen:
                # chunk.choices[0].delta.content 에 응답 텍스트가 들어 있음
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")  # 입력중 표시

            # 최종적으로 출력 마무리
            message_placeholder.markdown(full_response)

            # GPT 응답을 대화 기록에 저장
            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response
            })

# 메인 함수 호출
if __name__ == "__main__":
    main()
