import os
import streamlit as st
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

from llama_index.llms.openai import OpenAI
from llama_index.core import Settings
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.chat_engine import ContextChatEngine
from llama_index.core.memory import ChatMemoryBuffer

# 데이터 저장 경로
SOURCE_FOLDER = "../data"

# 디렉토리 내 파일 목록
def list_files_in_directory(directory):
    try:
        files = os.listdir(directory)
        return [f for f in files if os.path.isfile(os.path.join(directory, f))]
    except Exception as e:
        st.error(f"Error: {e}")
        return []

# 파일 저장
def save_uploaded_file(directory, file):
    if not os.path.exists(directory):
        os.makedirs(directory)
    with open(os.path.join(directory, file.name), 'wb') as f:
        f.write(file.getbuffer())

# llama_index 인덱스 생성
@st.cache_resource
def get_index():
    Settings.llm = OpenAI(temperature=0, model="gpt-4o-mini")
    try:
        documents = SimpleDirectoryReader(SOURCE_FOLDER).load_data()
        return VectorStoreIndex.from_documents(documents)
    except Exception as e:
        st.error(f"문서 로딩 실패: {e}")
        return None

# 메모리 초기화
@st.cache_resource
def get_memory():
    return ChatMemoryBuffer.from_defaults()

# 챗봇 응답
def chat_with_bot(user_input, index):
    chat_engine = index.as_chat_engine(
        chat_mode="context",
        memory=get_memory(),
        system_prompt="당신은 친절한 어시스턴트입니다. 사용자의 질문에 친절하게 답변하세요.",
    )
    return chat_engine.stream_chat(user_input)

# 파일 삭제
def delete_file(filename):
    file_path = os.path.join(SOURCE_FOLDER, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        get_index.clear()
        st.rerun()

# 메인 앱
def main():
    st.title("📚 RAG Chatbot with llama_index + OpenAI")

    if "file_uploader_key" not in st.session_state:
        st.session_state["file_uploader_key"] = 0

    with st.sidebar:
        st.subheader("📁 파일 업로드 및 삭제")
        upload_file = st.file_uploader("PDF 업로드", type=['pdf'], key=st.session_state["file_uploader_key"])
        if upload_file:
            save_uploaded_file(SOURCE_FOLDER, upload_file)
            get_index.clear()
            st.session_state["file_uploader_key"] += 1
            st.rerun()

        files = list_files_in_directory(SOURCE_FOLDER)
        if files:
            selected_file = st.selectbox("삭제할 파일 선택", files)
            if st.button("선택한 파일 삭제"):
                delete_file(selected_file)

    index = get_index()
    if index is None:
        st.stop()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("질문을 입력하세요...")
    if user_input:
        st.chat_message("user").markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        response = chat_with_bot(user_input, index)

        with st.chat_message("assistant"):
            msg_box = st.empty()
            full_response = ""
            for chunk in response.response_gen:
                full_response += chunk
                msg_box.markdown(full_response + "▌")
            msg_box.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})

if __name__ == "__main__":
    main()
