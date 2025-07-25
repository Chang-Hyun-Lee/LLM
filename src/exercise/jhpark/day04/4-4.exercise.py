import openai
import streamlit as st
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, ServiceContext
from llama_index.llms.openai import OpenAI
import os
import tempfile
from llama_index.core import Settings

openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="파일 설명기", layout="centered")

st.title("📄 파일 전체 설명기 (LlamaIndex + Streamlit)")

uploaded_file = st.file_uploader("파일을 업로드하세요 (PDF, TXT, DOCX)", type=["pdf", "txt", "docx"])

if uploaded_file:
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success("파일 업로드 완료. 처리 중...")

        # 문서 읽기
        reader = SimpleDirectoryReader(temp_dir)
        docs = reader.load_data()

        @st.cache_resource
         def get_index():
             Settings.llm = OpenAI(temperature=0, model="gpt-4o-mini")

             documents = []
             try:
               documents = SimpleDirectoryReader("./data").load_data()
             except Exception as e:
               print(f"An error occurred: {e}")        
        
             index = VectorStoreIndex.from_documents(
               documents,
           )
           return index
        
        # 요약용 쿼리엔진
        query_engine = index.as_query_engine()

        # 파일 내용 요약
        response = query_engine.query("이 문서의 내용을 요약해 주세요.")

        st.subheader("📌 문서 요약")
        st.write(response.response)
