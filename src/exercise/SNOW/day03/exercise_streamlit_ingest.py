import streamlit as st
import tempfile

from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA

# 세션 상태 기반 QA 체인 초기화
if "qa_chain" not in st.session_state:
    st.session_state.qa_chain = None
    st.session_state.chat_history = []

# 타이틀 표시
st.title("📄 GPT-4o PDF 챗봇")
st.caption("PDF를 업로드하면 해당 내용을 기반으로 GPT-4o가 질문에 응답합니다.")

# PDF 업로드
uploaded_file = st.file_uploader("📎 PDF 파일을 업로드하세요", type="pdf")

# PDF 처리
if uploaded_file and st.session_state.qa_chain is None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        pdf_path = tmp_file.name

    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_documents(documents)

    embedding_model = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(chunks, embedding_model)

    retriever = vectorstore.as_retriever()
    llm = ChatOpenAI(model_name="gpt-4o")

    st.session_state.qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)
    st.success("✅ PDF 로딩 완료! 질문을 입력해 주세요.")

# 챗봇 인터페이스
if st.session_state.qa_chain:
    for chat in st.session_state.chat_history:
        with st.chat_message("user"):
            st.markdown(chat["user"])
        with st.chat_message("assistant"):
            st.markdown(chat["bot"])

    user_input = st.chat_input("💬 질문을 입력하세요")
    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)

        response = st.session_state.qa_chain.run(user_input)

        with st.chat_message("assistant"):
            st.markdown(response)

        st.session_state.chat_history.append({
            "user": user_input,
            "bot": response
        })