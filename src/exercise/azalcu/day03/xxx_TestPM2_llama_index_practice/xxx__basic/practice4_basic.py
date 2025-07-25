# basic/practice4_basic.py
import streamlit as st
import os
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

st.title("🗂️ 기초: 파일 관리 & QA")

# API 키 입력
api_key = st.text_input("OpenAI API Key", type="password")

# 업로드 폴더 생성
os.makedirs("../uploads", exist_ok=True)

# 파일 업로드
uploaded_file = st.file_uploader("새 파일 업로드", type=['pdf', 'txt', 'docx'])

if uploaded_file:
    file_path = os.path.join("../uploads", uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"✅ {uploaded_file.name} 업로드 완료!")

# 파일 목록 표시
files = os.listdir("../uploads")
if files:
    st.write("**📁 업로드된 파일들:**")
    
    # 파일 선택 및 삭제
    selected_file = st.selectbox("파일 선택:", files)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ 선택된 파일 삭제"):
            os.remove(os.path.join("../uploads", selected_file))
            st.success(f"{selected_file} 삭제됨!")
            st.rerun()
    
    with col2:
        if st.button("🗑️ 모든 파일 삭제"):
            for file in files:
                os.remove(os.path.join("../uploads", file))
            st.success("모든 파일 삭제됨!")
            st.rerun()

# QA 기능
if api_key and files:
    Settings.llm = OpenAI(api_key=api_key)
    Settings.embed_model = OpenAIEmbedding(api_key=api_key)
    
    documents = SimpleDirectoryReader("../uploads").load_data()
    index = VectorStoreIndex.from_documents(documents)
    query_engine = index.as_query_engine()
    
    st.write(f"✅ {len(documents)}개 문서 준비 완료!")
    
    question = st.text_input("모든 파일에 대해 질문하세요:")
    if question:
        response = query_engine.query(question)
        st.write("**답변:**")
        st.write(response)
else:
    if not api_key:
        st.warning("API 키를 입력해주세요.")
    if not files:
        st.info("파일을 업로드해주세요.")