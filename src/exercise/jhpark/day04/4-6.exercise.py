import openai
import streamlit as st
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.llms.openai import OpenAI
import os
import tempfile
from llama_index.core import Settings

# OpenAI API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY")

# Streamlit 설정
st.set_page_config(page_title="파일 설명기", layout="centered")
st.title("📄 파일 전체 설명기 (LlamaIndex + Streamlit)")

# 파일 업로드
uploaded_file = st.file_uploader("파일을 업로드하세요 (PDF, TXT, DOCX)", type=["pdf", "txt", "docx"])

# 이전 결과 초기화
if "summary" not in st.session_state:
    st.session_state.summary = None

if uploaded_file:
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success("파일 업로드 완료. 처리 중...")

        # 문서 읽기
        reader = SimpleDirectoryReader(temp_dir)
        docs = reader.load_data()

        # LLM 설정 (전역)
        Settings.llm = OpenAI(temperature=0, model="gpt-4o-mini")

        @st.cache_resource
        def get_index(_documents):
            return VectorStoreIndex.from_documents(_documents)

        # 인덱스 생성
        index = get_index(docs)
        
        # 쿼리 엔진 생성 및 요약 실행
        query_engine = index.as_query_engine()
        response = query_engine.query("이 문서의 내용을 요약해 주세요.")
        st.session_state.summary = response.response

        # 결과 출력
        st.subheader("📌 문서 요약")
        st.write(response.response)
