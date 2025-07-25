# 실습: LangChain으로 만들어진 pdf 답변 어플리케이션을 streamlit으로 구현하시오. 
# 예전에 만든 ingest.py로 인덱스하시오. (시간이 된다면) 파일 업로드 기능을 추가한다. 

import streamlit as st
import random
import time
import os
import openai
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS

embeddings = OpenAIEmbeddings()
# @st.cache_resource
# def get_db():
#    return FAISS.load_local("shower", embeddings = embeddings, allow_dangerous_deserialization = True)

db = FAISS.load_local("shower", embeddings = embeddings, allow_dangerous_deserialization = True)

openai.api_key = os.getenv("OPENAI_API_KEY")

st.title("소나기 ChatBot")

# 채팅 초기 화면 출력 
if "messages" not in st.session_state:
    content = "당신은 친절한 어시스턴트입니다. 주어진 데이터를 보고 사용자에 친절하게 대답하세요.\n"
    st.session_state.messages = [
        {"role": "system", "content": content},
        {"role": "assistant", "content": "안녕! 무엇이 궁금해?"}
    ]

for message in st.session_state.messages[1:]:
    if(message["role"] != "system"):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


# 사용자 입력 받기
if prompt := st.chat_input("텍스트를 입력하고 엔터를 치거나 이미지를 업로드하세요"):
    # 사용자의 입력을 추가하기
    st.session_state.messages.append({"role": "user", "content": prompt})
    # 사용자의 입력을 보여주기
    with st.chat_message("user"):
        st.markdown(prompt)
    
    content = ""
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