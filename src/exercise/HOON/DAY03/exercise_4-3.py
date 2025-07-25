## 실습 #3. llama_index와 Streamlit을 사용하여 파일을 업로드하고 업로드한 파일 전체에 대해서 설명하는 어플리케이션을 작성하시오.
## 실습 #4. 실습 #3의 어플리케이션에서 파일을 리스트업하고 삭제할 수 있는 인터페이스를 작성하시오.

import os
import streamlit as st
#File 가져오는 부분
import PyPDF2
from langchain.document_loaders import PyPDFLoader
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
import openai



# File Upload
st.title("PDF 파일 업로드")
st.header("- Part : PDF 파일 업로드 (.pdf)")
uploaded_pdf_file = st.file_uploader(
    "PDF 파일을 업로드해 주세요",
    type=["pdf"], # PDF 파일만 허용
    key="pdf_uploader"
)

# File 읽기
if uploaded_pdf_file is not None:
    readerStream = PyPDF2.PdfReader(uploaded_pdf_file)
    if readerStream is not None:
        st.info("추출 완료")
    else :
        st.info("추출 실패")


# 메모리 저장 파일의 경로를 재 추출
import tempfile
    
temp_file_path = None
documents = None
with tempfile.TemporaryDirectory() as temp_dir:
    temp_pdf_path = os.path.join(temp_dir, uploaded_pdf_file.name)

    with open(temp_pdf_path, "wb") as f:
        f.write(uploaded_pdf_file.getvalue())
        documents = SimpleDirectoryReader(temp_dir).load_data()
#    st.success(f"PDF File 임시 폴더에 저장되었음. : {temp_pdf_path}")
#    st.success(f"PDF File 임시 폴더에 저장되었음. : {temp_dir}")
    

openai.api_key = os.getenv("OPENAI_API_KEY")

def using_llama(doc, query):
    documents = doc
    index = VectorStoreIndex.from_documents(documents)
    query_engine = index.as_query_engine()
    response = query_engine.query(query)
    return response


def main():
    st.title("RAG Chatbot with Streamlit and OpenAI")
    st.chat_input(placeholder="대화를 입력해주세요.", key="chat_input")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []        

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_input := st.session_state["chat_input"]:
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content":user_input})
        print(user_input)

        gen = using_llama(documents, user_input)
        print(gen)
        with st.chat_message("assistant"):
            st.markdown(gen)
            st.session_state.messages.append({"role": "assistant", "content":gen})
       
# 업로드한 파일 요약 설명
def main_2nd():
    st.title("RAG Summary with uploading pdf files")
    
    user_input = "해당 문서에 대해서 줄거리, 또는 내용을 한국어로 요약해서 설명해줘. 만약 모르는 내용이 있으면 모른다고 답변해."
    gen = using_llama(documents, user_input)
    st.success(f"{uploaded_pdf_file.name} 에 대한 설명입니다.")
    
    st.success(gen)

if __name__ == "__main__":
    #main()
    main_2nd()
