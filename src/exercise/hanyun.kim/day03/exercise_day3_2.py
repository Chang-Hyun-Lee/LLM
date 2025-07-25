# 실습 #2: LangChain으로 만들어진 pdf 답변 어플리케이션을 streamlit으로 구현하시오. 
# 예전에 만든 ingest.py로 인덱스하시오. 
# (시간이 된다면) 파일 업로드 기능을 추가한다. 

import streamlit as st
import os
from dotenv import load_dotenv
from openai import OpenAI
import random
import time

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


from langchain.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings

#embeddings = HuggingFaceEmbeddings()
embeddings = OpenAIEmbeddings()

from langchain.vectorstores import FAISS

@st.cache_resource
def get_db():
    return FAISS.load_local("shower", embeddings=embeddings, allow_dangerous_deserialization=True)

# 스트림


import random
import time

import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

def create_system_content(systext):
    content = "당신은 친절한 어시스턴트입니다. 주어진 데이터를 보고 사용자에 친절하게 대답하세요.\n" 
    content += "*" * 50
    docs = get_db().similarity_search(systext)
    for doc in docs:
        content += doc.page_content + "\n"
        content += "*" * 50
        
    system_content = {
          "role": "system",
          "content": content
        }
    return system_content

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("질문을 입력해 주세요..."): 
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        merge_msgs=[]
  
        merge_msgs.append(create_system_content(prompt))
        for msg in st.session_state.messages:
            merge_msgs.append(msg)
        # st.write(merge)

        assistant_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages= merge_msgs,
        )
        st.session_state.messages.append({"role": "assistant", "content": assistant_response.choices[0].message.content})

        # Simulate stream of response with milliseconds delay
        message_placeholder = st.empty()
        full_response = ""
        for chunk in assistant_response.choices[0].message.content.split():
            full_response += chunk + " "
            time.sleep(0.05)
            # Add a blinking cursor to simulate typing
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)