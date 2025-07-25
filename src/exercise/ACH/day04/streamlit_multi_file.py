import os
import streamlit as st
import openai
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.chat_engine import ContextChatEngine
from llama_index.core.memory import ChatMemoryBuffer

# OpenAI API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY")

# 파일 저장 함수
def save_uploaded_file(directory, file):
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    with open(os.path.join(directory, file.name), 'wb') as f:
        f.write(file.getbuffer())

# 인덱스 캐싱
@st.cache_resource
def get_index():
    Settings.llm = OpenAI(temperature=0, model="gpt-4o-mini")

    documents = []
    try:
        documents = SimpleDirectoryReader("../data").load_data()
    except Exception as e:
        print(f"An error occurred: {e}")        
        
    index = VectorStoreIndex.from_documents(documents)
    return index

# 메모리 캐싱
@st.cache_resource
def get_memory():
    return ChatMemoryBuffer.from_defaults()

# 챗봇과 대화 함수
def chat_with_bot(user_input, index):
    chat_engine = index.as_chat_engine(
        chat_mode="context",
        memory=get_memory(),
        system_prompt="당신은 친절한 어시스턴트입니다. 사용자의 질문에 친절하게 답변하세요.",
    )
    response = chat_engine.stream_chat(user_input)
    return response

# Streamlit 앱 메인 함수
def main():
    st.set_page_config(page_title="RAG Chatbot", layout="wide")
    st.title("🧠 RAG Chatbot with Streamlit, LlamaIndex and OpenAI")

    # 초기화
    if "file_uploader_key" not in st.session_state:
        st.session_state["file_uploader_key"] = 0

    # 사이드바 UI
    with st.sidebar:
        st.subheader("📁 파일 업로드")
        data_dir = "../data"
        upload_file = st.file_uploader("PDF 파일 업로드", type=['pdf'], key=st.session_state["file_uploader_key"])

        if upload_file is not None:
            save_uploaded_file(data_dir, upload_file)
            get_index.clear()
            st.session_state["file_uploader_key"] += 1
            st.rerun()

        # 업로드된 파일 목록 및 삭제 UI
        st.subheader("📂 업로드된 파일")
        if os.path.exists(data_dir):
            files = os.listdir(data_dir)
            if files:
                for file in files:
                    file_path = os.path.join(data_dir, file)
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"📄 {file}")
                    with col2:
                        if st.button("❌", key=f"delete_{file}"):
                            os.remove(file_path)
                            get_index.clear()
                            st.rerun()
            else:
                st.info("업로드된 파일이 없습니다.")
        else:
            st.info("업로드 디렉토리가 존재하지 않습니다.")

    # 인덱스 생성
    index = get_index()

    # 메시지 세션 초기화
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 이전 메시지 출력
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 사용자 입력
    user_input = st.chat_input("대화를 입력해주세요.")
    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        response = chat_with_bot(user_input, index)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            for chunk in response.response_gen:
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})

if __name__ == "__main__":
    main()
