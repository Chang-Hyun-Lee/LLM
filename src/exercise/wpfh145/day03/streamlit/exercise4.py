#실습 #1. llama_index와 Streamlit을 사용하여 인덱스된 파일에 대해서 답변하는 어플리케이션을 작성하시오.
#실습 #2. llama_index와 Streamlit을 사용하여 인덱스된 파일에 대해서 답변하는 어플리케이션을 멀티턴으로 바꾸시오.
#실습 #3. llama_index와 Streamlit을 사용하여 파일을 업로드하고 업로드한 파일 전체에 대해서 설명하는 어플리케이션을 작성하시오.
#실습 #4. 실습 #3의 어플리케이션에서 파일을 리스트업하고 삭제할 수 있는 인터페이스를 작성하시오.

import streamlit as st
from llama_index.core import VectorStoreIndex, Document, SimpleDirectoryReader
from PyPDF2 import PdfReader

uploaded_files = st.file_uploader("PDF 파일을 업로드하세요", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    documents = []
    for uploaded_file in uploaded_files:
        pdf_reader = PdfReader(uploaded_file)
        text = "\n".join([page.extract_text() or "" for page in pdf_reader.pages])
        documents.append(Document(text=text))
else:
    # 업로드된 파일이 없으면 data 폴더의 파일을 로드
    documents = SimpleDirectoryReader("data").load_data()
    index = VectorStoreIndex.from_documents(documents)

if uploaded_files:
    index = VectorStoreIndex.from_documents(documents)
    

# 처음 pdf 파일 요약 설명
def summary_documents():
        query_engine_sum = index.as_query_engine(response_mode="tree_summarize")
        response = query_engine_sum.query("해당 내용에 대해 전체적인 설명을 한글로 해줘")
        return response

st.write(summary_documents().response)



# 멀티턴 채팅
query_engine = index.as_query_engine()
if "messages" not in st.session_state:
    st.session_state["messages"] = []

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_input = st.chat_input("메시지를 입력하세요...")

if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    response = query_engine.query(f"{user_input}+한글로 말해줘")
    st.session_state["messages"].append({"role": "assistant", "content": response.response})
    with st.chat_message("assistant"):
        st.write(response.response)


# build_index 함수에서 documents -> _documents 로 변경
# @st.cache_resource
# def build_index(_documents):
   #  return VectorStoreIndex.from_documents(_documents)
