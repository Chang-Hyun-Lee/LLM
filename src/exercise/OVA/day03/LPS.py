# pdf_qa_app.py

import streamlit as st
import os
import tempfile

from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.chains.qa_with_sources import load_qa_with_sources_chain

# 🔐 OpenAI API 키 설정
os.environ["OPENAI_API_KEY"] = "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"

# 📘 Streamlit 기본 설정
st.set_page_config(page_title="LangChain PDF 질문 응답기", page_icon="📄")
st.title("📄 LangChain PDF 질문 응답기")

# 📤 PDF 업로드
uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type="pdf")

if uploaded_file:
    # 임시 저장소에 파일 저장
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_pdf_path = tmp_file.name

    st.success("✅ PDF 업로드 완료. 인덱싱 중...")

    # 📄 문서 로드 및 분할
    loader = PyPDFLoader(tmp_pdf_path)
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    split_docs = splitter.split_documents(documents)

    # 🔍 임베딩 및 벡터 저장소
    embeddings = OpenAIEmbeddings()
    db = FAISS.from_documents(split_docs, embeddings)

    retriever = db.as_retriever()

    # 🤖 고급 QA 체인 (map_reduce)
    llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="map_reduce",  # 핵심 개선!
        retriever=retriever,
        return_source_documents=False,
    )

    # 🧠 사용자 질문 입력
    st.markdown("#### 예시 질문:")
    st.markdown("- 소녀가 던진 조약돌의 의미는 무엇인가요?")
    st.markdown("- 마지막 장면에서 무슨 일이 벌어졌나요?")
    st.markdown("- 소나기의 상징적 의미는 무엇인가요?")

    query = st.text_input("궁금한 내용을 입력하세요:")

    if query:
        with st.spinner("🤖 GPT가 문서를 분석하고 있습니다..."):
            try:
                result = qa_chain.run(query)
                st.markdown("#### 🧠 답변:")
                st.success(result)
            except Exception as e:
                st.error(f"❌ 오류 발생: {e}")
