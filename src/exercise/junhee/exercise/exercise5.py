#1. llama_index와 Streamlit을 사용하여 인덱스된 파일에 대해서 답변하는 어플리케이션을 작성하시오.
#2. llama_index와 Streamlit을 사용하여 인덱스된 파일에 대해서 답변하는 어플리케이션을 멀티턴으로 바꾸시오.
#3. llama_index와 Streamlit을 사용하여 파일을 업로드하고 업로드한 파일 전체에 대해서 설명하는 어플리케이션을 작성하시오.
#4. 3의 어플리케이션에서 파일을 리스트업하고 삭제할 수 있는 인터페이스를 작성하시오.


import streamlit as st
import time
import os
import openai
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage

openai.api_key = os.getenv("OPENAI_API_KEY")
Settings.llm = OpenAI(temperature = 0.2, model = "gpt-4o-mini")


# UI 구현
# ----------------------------------------------------------------------------
with st.sidebar:
    st.subheader("파일 업로드")
    uploaded_files = st.file_uploader("파일 업로드", type = ["pdf", "txt", "md"], accept_multiple_files = True)

st.title("📄 문서를 업로드하고 질문하세요!")
# ----------------------------------------------------------------------------


# 파일 폴더 위치 지정
PERSIST_DIR = "./storage"
UPLOAD_DIR = "uploaded_files"

# 업로드 디렉토리 생성
os.makedirs(UPLOAD_DIR, exist_ok = True)

# 📁 파일 업로드
if uploaded_files:
    for file in uploaded_files:
        with open(os.path.join(UPLOAD_DIR, file.name), "wb") as f:
            f.write(file.getbuffer())
    st.success("파일 업로드 완료!")
    


# 채팅 초기 화면 출력 
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "안녕! 무엇이 궁금해?"}
    ]



if "query_engine" not in st.session_state:
    st.session_state.query_engine = None

for message in st.session_state.messages[:]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# 사용자 입력 받기
if prompt := st.chat_input("텍스트를 입력하세요"):

    if not os.path.exists(PERSIST_DIR):
        if uploaded_files:
            documents = SimpleDirectoryReader(UPLOAD_DIR).load_data()
            index = VectorStoreIndex.from_documents(documents)
            index.storage_context.persist(persist_dir = PERSIST_DIR)
    else:
        storage_context = StorageContext.from_defaults(persist_dir = PERSIST_DIR)
        index = load_index_from_storage(storage_context)
    
    # 쿼리 엔진 설정
    st.session_state.query_engine = index.as_query_engine()

    # 사용자의 입력을 추가하기
    st.session_state.messages.append({"role": "user", "content": prompt})
    # 사용자의 입력을 보여주기
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = st.session_state.query_engine.query(prompt)
        st.markdown(response)
    # 답변 저장
    st.session_state.messages.append({"role": "assistant", "content": response})




