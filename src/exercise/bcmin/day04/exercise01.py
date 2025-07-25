import streamlit as st
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core import Document

uploaded_file = st.file_uploader("파일을 업로드하세요", type=["txt"]) #, "pdf", "docx"])
if uploaded_file is not None:
#     st.write("파일 이름:", uploaded_file.name)
#     st.write("파일 크기:", uploaded_file.size)
#     st.write("파일 타입:", uploaded_file.type)
     content = uploaded_file.read()
#     st.write("파일 내용:", content.decode("utf-8"))

if uploaded_file:
    
    documents = [Document(text=content.decode("utf-8"), metadata={"filename": uploaded_file.name})]
    #documents = [Document(text=content, metadata={"filename": uploaded_file.name})]

    index = VectorStoreIndex.from_documents(documents)
    query_engine = index.as_query_engine()
    query = st.text_input("문서에 대해 궁금한 점을 입력하세요:")

    if query:
        response = query_engine.query(query)
        st.write("답변:", response.response)

