## 실습 #1. llama_index와 Streamlit을 사용하여 인덱스된 파일에 대해서 답변하는 어플리케이션을 작성하시오.
## 실습 #2. llama_index와 Streamlit을 사용하여 인덱스된 파일에 대해서 답변하는 어플리케이션을 멀티턴으로 바꾸시오.


import os
import streamlit as st
import openai
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

openai.api_key = os.getenv("OPENAI_API_KEY")

def using_llama(query):
    documents = SimpleDirectoryReader("data").load_data()
    index = VectorStoreIndex.from_documents(documents)
    query_engine = index.as_query_engine()
    response = query_engine.query(query)
    return response

def main():
    st.title("RAG Chatbot with Streamlit and OpenAI")
    st.chat_input(placeholder="대화를 입력해주세요.", key="chat_input")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []        

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_input := st.session_state["chat_input"]:
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content":user_input})
        print(user_input)

        gen = using_llama(user_input)
        print(gen)
        with st.chat_message("assistant"):
            st.markdown(gen)
            st.session_state.messages.append({"role": "assistant", "content":gen})
       
if __name__ == "__main__":
    main()
