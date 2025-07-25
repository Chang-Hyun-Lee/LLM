import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
import os

VECTORSTORE_PATH = "shower"  # 기존에 만든 ingest.py에서 저장한 경로

# 1) 저장된 벡터스토어 로드 함수
@st.cache_resource(show_spinner=False)
def load_vectorstore(path: str):
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)
    return vectorstore

# 2) 질문답변 체인 생성 함수
@st.cache_resource(show_spinner=False)
def create_qa_chain(_vectorstore):
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=_vectorstore.as_retriever())
    return qa_chain

# 3) 새 PDF 업로드시 인덱싱 함수
def index_pdf(file):
    # 3-1) PDF 임시 저장
    with open("temp.pdf", "wb") as f:
        f.write(file.getbuffer())

    # 3-2) 로드 및 분할
    loader = PyPDFLoader("temp.pdf")
    documents = loader.load()
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    docs = text_splitter.split_documents(documents)

    # 3-3) 임베딩 생성 및 벡터스토어 구축
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = FAISS.from_documents(docs, embeddings)

    # 3-4) 벡터스토어 저장 (덮어쓰기)
    vectorstore.save_local(VECTORSTORE_PATH)

    # 3-5) 임시파일 삭제
    os.remove("temp.pdf")

    return vectorstore

# 메인 앱
def main():
    st.title("📄 PDF 질문응답 앱 (LangChain + Streamlit)")

    # 사이드바: PDF 업로드 기능
    uploaded_file = st.sidebar.file_uploader("새 PDF 파일 업로드 (업로드 시 인덱싱 됩니다)", type=["pdf"])

    if uploaded_file is not None:
        st.sidebar.info("PDF 인덱싱 중... 잠시만 기다려주세요.")
        vectorstore = index_pdf(uploaded_file)
        st.sidebar.success("인덱싱 완료! 질문을 입력하세요.")
    else:
        # 기존 벡터스토어 로드
        vectorstore = load_vectorstore(VECTORSTORE_PATH)

    qa_chain = create_qa_chain(vectorstore)

    # 질문 입력창
    query = st.text_input("❓ 질문을 입력하세요:")

    if query:
        with st.spinner("답변 생성 중..."):
            answer = qa_chain.run(query)
        st.markdown("### 💬 답변:")
        st.write(answer)

if __name__ == "__main__":
    main()
