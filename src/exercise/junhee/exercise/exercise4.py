# 실습: Streamlit과 Assistant API를 이용하여 세션을 유지하는 멀티턴 챗봇을 만드시오. 단 Assistant는 미리 만들어서 id를 얻어둔다. (시간이 된다면) stream 기능을 추가한다.

# assistants_id = asst_UIoILByMFhNJ0Q18C0m69eko


import streamlit as st
import time
import os
import openai
from openai import OpenAI

openai.api_key = os.getenv("OPENAI_API_KEY")
assistant_id = "asst_UIoILByMFhNJ0Q18C0m69eko"

client = OpenAI()



assistant = client.beta.assistants.create(
    name = "수학 선생님",
    instructions = "당신은 친절한 수학선생님입니다. 사용자가 질문하는 수학문제에 대답하기 위해 code를 작성하고 실행하세요.",
    tools = [{"type": "code_interpreter"}],
    model = "gpt-4o-mini"
)



thread = None
if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state["thread_id"] = thread.id
else:
    thread_id = st.session_state["thread_id"]
    thread = client.beta.threads.retrieve(thread_id)





for message in st.session_state.messages[1:]:
    if(message["role"] != "system"):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


# 사용자 입력 받기
if prompt := st.chat_input("텍스트를 입력하고 엔터를 치거나 이미지를 업로드하세요"):

    message = client.beta.threads.messages.create(
        thread_id = thread.id,
        role = "user",
        content = prompt  
    )   
    # 사용자의 입력을 추가하기
    st.session_state.messages.append({"role": "user", "content": prompt})
    # 사용자의 입력을 보여주기
    with st.chat_message("user"):
        st.markdown(prompt)
    
    content = ""
    db = get_db()
    docs = db.similarity_search(prompt)
    for doc in docs:
        content += doc.page_content + "\n"
        content += "-" * 50 + "\n"
        
    st.session_state.messages.append({"role": "system", "content": content})

    # 챗봇 응답 생성 및 출력
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        assistant_response = openai.chat.completions.create(
            model = "gpt-4o",
            messages = st.session_state.messages,
            temperature = 0.5,
            max_tokens = 512,
            top_p = 1,
            frequency_penalty = 0,
            presence_penalty = 0,
            stream = True
        )

        for chunk in assistant_response:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                content = delta.content
                full_response += content
                message_placeholder.markdown(full_response + "▌")
                time.sleep(0.03)
        message_placeholder.markdown(full_response)

    # 챗봇의 답변 추가
    st.session_state.messages.append({"role": "assistant", "content": full_response})