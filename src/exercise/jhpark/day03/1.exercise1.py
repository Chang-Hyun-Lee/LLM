import streamlit as st
import random
import time

import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

def create_generator(history):
    chat_logs = []

    for item in history:
        if item[0] is not None: # 사용자
            message =  {
              "role": "user",
              "content": item[0]
            }
            chat_logs.append(message)            
        if item[1] is not None: # 챗봇
            message =  {
              "role": "assistant",
              "content": item[1]
            }
            chat_logs.append(message)            
    
    messages=[
        {
          "role": "system",
          "content": "당신은 친절한 어시스턴트입니다. 사용자의 질문에 친절하게 대답하세요."
        }
    ]
    messages.extend(chat_logs)
        
    gen = openai.chat.completions.create(
      model="gpt-4o-mini",
      messages=messages,
      temperature=0.5,
      max_tokens=4096,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0,
      stream=True
    )
    return gen


# 유저 메시지 입력
st.title("Chatbot")
user_message = st.text_input("You:", key="input")

# Clear 버튼
if st.button("Clear"):
    st.session_state.history = []

# 사용자 메시지를 history에 추가
if user_message:
    st.session_state.history.append([user_message, None])

# 대답 생성기 함수 (Gradio에서 create_generator 대체용)
def create_generator(history):
    """
    예시용 generator. 실제로는 OpenAI 또는 다른 모델의 스트리밍 응답을 여기서 받아야 합니다.
    """
    import time
    full_response = "이것은 예시 응답입니다. 스트리밍처럼 나눠서 출력됩니다."
    for token in full_response.split():
        time.sleep(0.2)  # 스트리밍처럼 보이도록 지연
        yield token + " "

# 최신 메시지에 대한 응답 생성
if st.session_state.history and st.session_state.history[-1][1] is None:
    st.session_state.history[-1][1] = ""
    gen = create_generator(st.session_state.history)
    response_placeholder = st.empty()
    for token in gen:
        st.session_state.history[-1][1] += token
        # 실시간 반영
        with response_placeholder.container():
            for user, bot in st.session_state.history:
                st.markdown(f"**You:** {user}")
                st.markdown(f"**Bot:** {bot if bot else '...'}")

# 최종 대화 렌더링
for user, bot in st.session_state.history:
    st.markdown(f"**You:** {user}")
    st.markdown(f"**Bot:** {bot}")
