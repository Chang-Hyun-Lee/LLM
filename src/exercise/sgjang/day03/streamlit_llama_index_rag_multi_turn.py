import os
import streamlit as st
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

from llama_index.llms.openai import OpenAI
from llama_index.core import Settings
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.chat_engine import ContextChatEngine
from llama_index.core.memory import ChatMemoryBuffer

@st.cache_resource
def get_index():
    Settings.llm = OpenAI(temperature=0.2, model="gpt-4o-mini")

    documents = []
    try:
        documents = SimpleDirectoryReader("../data").load_data()
    except Exception as e:
        print(f"An error occurred: {e}")        
        
    index = VectorStoreIndex.from_documents(
        documents,
    )
    return index

@st.cache_resource
def get_memory():
    memory = ChatMemoryBuffer.from_defaults()
    return memory

def chat_with_bot(user_input, index):

    chat_engine = index.as_chat_engine(
        chat_mode="context",
        memory=get_memory(),
        system_prompt=(
            "당신은 친절한 어시스턴트입니다. 사용자의 질문에 친절하게 답변하세요."
        ),
    )
    response = chat_engine.stream_chat(user_input)
    return response
    
# Streamlit 앱 정의
def main():
    st.title("RAG Chatbot with Streamlit, llama_index and OpenAI")
    st.chat_input(placeholder="대화를 입력해주세요.", key="chat_input")

    index = get_index()
    
    if "messages" not in st.session_state: # 세션에 내용 없으면 0번 부여
        st.session_state.messages = []        

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_input := st.session_state["chat_input"]:
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content":user_input})
        response = chat_with_bot(user_input, index)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""        
            for text in response.response_gen:
                full_response += text
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content":full_response})

if __name__ == "__main__":
    main()
