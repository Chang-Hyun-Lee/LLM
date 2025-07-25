##실습 #1: gradio로 만든 멀티턴 채팅 어플리케이션을 streamlit으로 유사하게 구현하시오.
## 미완성 코드
## 미완성 코드. 예제풀다가 넘어가서 패스함.

import streamlit as st

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


st.title('Gradio 처럼 만든 멀티턴 채팅' + '스마일 :sunglasses:')

history = ''

if "history" not in st.session_state:
    st.session_state.history = [{"role": "assistant", "content": "질문하이소"}]

for history in st.session_state.history:
    with st.chat_message(history["role"]):
        st.markdown(history["content"])

ch_in = st.chat_input('뭐 궁금하니?')
if ch_in is not None:
    st.session_state.history.append({"role": "user", "content": ch_in})

    gen_Msg = create_generator(history)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        for char in gen_Msg:
            if char.choices[0].delta.content is not None:
                full_response[-1][1] += char.choices[0].delta.content

        message_placeholder.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})

