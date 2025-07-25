# LangChain으로 만들어진 pdf 답변 어플리케이션을 streamlit으로 구현하시오.
# 예전에 만든 ingest.py로 인덱스하시오.(시간이 된다면) 파일 업로드 기능 추가

import streamlit as st
import os
import openai
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain.indexes import VectorstoreIndexCreator
from langchain.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import PDFPlumberLoader

@st.cache_resource
def load_index_from_pdf(pdf_path):
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    docs = text_splitter.split_documents(documents)

    embeddings = OpenAIEmbeddings()

    index = VectorstoreIndexCreator(
        vectorstore_cls=FAISS,
        embedding=embeddings,
        ).from_documents(docs)

    return index


path = os.path.expanduser("~/work/koshipa-llm-2025-1st/src/exercise/soyeon/day02/소나기.pdf")
index = load_index_from_pdf(path)


chat = ChatOpenAI(model_name='gpt-4o-mini', temperature=0)

# Streamlit 화면 구성
user_input = st.chat_input("질문 해주세요")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_input :
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role" : "user", "content" : user_input})

    with st.chat_message("assistant"):
        response = index.query(user_input, llm = chat)
        st.markdown(response)

    st.session_state.messages.append({"role" : "assistant", "content" : response})
