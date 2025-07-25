import streamlit as st
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SentenceSplitter
import os

# 환경변수에서 OpenAI API Key 가져오기
import openai
openai.api_key = os.getenv("OPENAI_API_KEY")

# llama_index 전역 설정
Settings.llm = OpenAI(temperature=0, model="gpt-4o-mini")
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=20)

# Streamlit 앱
st.title("📄 문서 기반 질문 응답 시스템")

# 인덱스 생성
@st.cache_resource
def load_index():
    documents = SimpleDirectoryReader("data").load_data()
    index = VectorStoreIndex.from_documents(documents)
    return index.as_query_engine()

query_engine = load_index()

# 사용자 입력
query = st.text_input("질문을 입력하세요:")

# 답변 출력
if query:
    with st.spinner("답변 생성 중..."):
        response = query_engine.query(query)
        st.success("✅ 답변")
        st.write(response.response)
