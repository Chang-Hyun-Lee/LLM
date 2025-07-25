# 실습 #2: LangChain으로 만들어진 pdf 답변 어플리케이션을 streamlit으로 구현하시오. 예전에 만든 ingest.py로 인덱스하시오. (시간이 된다면) 파일 업로드 기능을 추가한다. 

import os
import streamlit as st
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

from langchain.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS

@st.cache_resource
def get_db():
    return FAISS.load_local("faiss-nj-IU", embeddings=OpenAIEmbeddings(), allow_dangerous_deserialization=True)

def chat_with_bot(history, db):
    content = "당신은 친절한 어시스턴트입니다. 주어진 데이터를 보고 사용자에 친절하게 대답하세요.\n" 
    content += "*" * 50
    docs = db.similarity_search(history[-1]["content"])
    for doc in docs:
        content += doc.page_content + "\n"
        content += "*" * 50
        
    messages = [
        {
          "role": "system",
          "content": content
        }
    ]
    messages.extend(history)

    gen = openai.chat.completions.create(
      model="gpt-4o-mini",
      messages=messages,
      temperature=0,
      max_tokens=4096,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0,
      stream=True
    )
    return gen

# Streamlit 앱 정의
def main():
    st.title("RAG Chatbot with Streamlit and OpenAI")
    st.chat_input(placeholder="대화를 입력해주세요.", key="chat_input")

    db = get_db()
    
    if "messages" not in st.session_state:
        st.session_state.messages = []        

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_input := st.session_state["chat_input"]:
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content":user_input})

        gen = chat_with_bot(st.session_state.messages, db)
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""        
            for chunk in gen:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content":full_response})

if __name__ == "__main__":
    main()
