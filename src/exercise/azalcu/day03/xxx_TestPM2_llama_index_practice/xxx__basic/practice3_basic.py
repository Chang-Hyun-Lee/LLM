# basic/practice3_basic.py
import streamlit as st
import os
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

st.title("📂 기초: 파일 업로드 & 요약")

# API 키 입력
api_key = st.text_input("OpenAI API Key", type="password")

# 파일 업로드
uploaded_file = st.file_uploader("파일 업로드", type=['pdf', 'txt', 'docx'])

if api_key and uploaded_file:
    # LlamaIndex 설정
    Settings.llm = OpenAI(api_key=api_key)
    Settings.embed_model = OpenAIEmbedding(api_key=api_key)
    
    # 업로드 폴더 생성
    os.makedirs("../uploads", exist_ok=True)
    
    # 파일 저장
    file_path = os.path.join("../uploads", uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # 문서 로드 및 인덱싱
    documents = SimpleDirectoryReader("../uploads").load_data()
    index = VectorStoreIndex.from_documents(documents)
    query_engine = index.as_query_engine()
    
    st.success(f"✅ {uploaded_file.name} 업로드 완료!")
    
    # 자동 요약
    if st.button("📄 파일 요약"):
        response = query_engine.query("이 문서의 전체 내용을 요약해주세요.")
        st.write("**요약:**")
        st.write(response)
    
    # 질문하기
    question = st.text_input("문서에 대해 질문하세요:")
    if question:
        response = query_engine.query(question)
        st.write("**답변:**")
        st.write(response)
else:
    if not api_key:
        st.warning("API 키를 입력해주세요.")
    if not uploaded_file:
        st.info("파일을 업로드해주세요.")