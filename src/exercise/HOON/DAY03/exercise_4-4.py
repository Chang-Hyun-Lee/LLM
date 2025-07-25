## 실습 #4. 실습 #3의 어플리케이션에서 파일을 리스트업하고 삭제할 수 있는 인터페이스를 작성하시오.
# 미완성 코드 시간없어서 못함.

import os
import streamlit as st
#File 가져오는 부분
import PyPDF2
from langchain.document_loaders import PyPDFLoader
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
import openai

if "uploaded_file_list" not in st.session_state:
    st.session_state.uploaded_file_list = []


# File Upload
st.title("PDF 파일 업로드")
st.header("- Part : PDF 파일 업로드 (.pdf)")
uploaded_pdf_files = st.file_uploader(
    "PDF 파일을 업로드해 주세요",
    type=["pdf"], # PDF 파일만 허용
    key="pdf_uploader",
    accept_multiple_files=True
)

# File 읽기
if uploaded_pdf_files is not None:
    for uploaded_file in uploaded_pdf_files:
        file_info = {
            "name" : uploaded_file.name,
            "type" : uploaded_file.type,
            "size" : uploaded_file.size
        }

        if file_info not in st.session_state.uploaded_file_list:
            st.session_state.uploaded_file_list.append(file_info)
            print("success" + file_info)

            
st.success("업로드된 파일 목록")

