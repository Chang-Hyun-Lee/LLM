import streamlit as st
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.llms.openai import OpenAI
import os
import shutil

# 임시 업로드 디렉토리
UPLOAD_DIR = "uploaded_docs"

st.set_page_config(page_title="문서 설명 챗봇", layout="centered")
st.title("📄 문서 설명 어플리케이션")

# 업로드 처리
uploaded_file = st.file_uploader("문서를 업로드하세요 (PDF, TXT 등)", type=["pdf", "txt", "md"])
if uploaded_file:
    # 임시 디렉토리 생성
    if os.path.exists(UPLOAD_DIR):
        shutil.rmtree(UPLOAD_DIR)
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # 파일 저장
    with open(os.path.join(UPLOAD_DIR, uploaded_file.name), "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success(f"'{uploaded_file.name}' 업로드 완료!")

    # 데이터 로드 및 인덱싱
    with st.spinner("문서를 분석 중입니다..."):
        documents = SimpleDirectoryReader(UPLOAD_DIR).load_data()
        index = VectorStoreIndex.from_documents(documents)
        query_engine = index.as_query_engine(llm=OpenAI(model="gpt-4"))

    # 질의창
    user_question = st.text_input("문서에 대해 궁금한 점을 질문해보세요:")
    if user_question:
        with st.spinner("답변 생성 중..."):
            response = query_engine.query(user_question)
            st.markdown("### 🤖 답변:")
            st.write(response.response)

    # 요약 버튼
    if st.button("문서 전체 요약"):
        with st.spinner("요약 생성 중..."):
            summary = query_engine.query("이 문서를 요약해줘.")
            st.markdown("### 📝 요약:")
            st.write(summary)
