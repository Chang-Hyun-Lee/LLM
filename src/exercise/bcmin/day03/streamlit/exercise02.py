import streamlit as st
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
import os

# 🔑 OpenAI API 키 설정
openai_api_key = os.getenv("OPENAI_API_KEY")

# 📝 Streamlit 앱 제목
st.title("📄 PDF 문서 질의응답 어플리케이션")

# 📁 벡터 DB 로딩
@st.cache_resource
def load_vectorstore():
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
    db = FAISS.load_local("shower1", embeddings=embeddings, allow_dangerous_deserialization=True)
    return db

# 🤖 챗 모델 + 검색 체인 설정
@st.cache_resource
def get_qa_chain():
    vectorstore = load_vectorstore()
    retriever = vectorstore.as_retriever()
    llm = ChatOpenAI(openai_api_key=openai_api_key, model="gpt-4o-mini")
    chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)
    return chain

chain = get_qa_chain()

# 🧑 사용자 입력 받기
query = st.text_input("📌 PDF에 대해 궁금한 점을 입력하세요:")

# 🔎 질문 처리
if query:
    with st.spinner("답변 생성 중..."):
        answer = chain.run(query)
    st.markdown(f"### 🤖 답변\n{answer}")
