import os
import streamlit as st
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
    ServiceContext,  
)
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.openai import OpenAI

# Streamlit 페이지 설정
st.set_page_config(page_title="streamlit and llama", layout="centered")
st.title("📄 문서 기반 Q&A 어플리케이션")

# 업로드된 파일 저장 폴더
UPLOAD_DIR = "uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

uploaded_files = st.file_uploader("문서를 업로드하세요 (PDF, TXT 등)", type=["pdf", "txt"], accept_multiple_files=True)

# 파일 저장
if uploaded_files:
    for uploaded_file in uploaded_files:
        file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
    st.success("파일 업로드 완료!")

    # 문서 읽기 및 인덱싱
    with st.spinner("문서를 인덱싱하는 중..."):
        documents = SimpleDirectoryReader(UPLOAD_DIR).load_data()
        service_context = ServiceContext.from_defaults(llm=OpenAI(temperature=0, model="gpt-4o-mini"))
        index = VectorStoreIndex.from_documents(documents, service_context=service_context)
        query_engine = index.as_query_engine()
    st.success("인덱스 생성 완료!")

    # 질문 입력
    question = st.text_input("질문을 입력하세요:")
    if question:
        with st.spinner("답변 생성 중..."):
            answer = query_engine.query(question)
        st.subheader("🧠 답변")
        st.write(answer.response)
