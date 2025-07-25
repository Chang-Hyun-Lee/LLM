##실습 #2: LangChain으로 만들어진 pdf 답변 어플리케이션을 streamlit으로 구현하시오. 예전에 만든 ingest.py로 인덱스하시오. (시간이 된다면) 파일 업로드 기능을 추가한다. 

import os
import streamlit as st
#File 가져오는 부분
import PyPDF2
# FAISS Vector화
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain.indexes import VectorstoreIndexCreator
from langchain.vectorstores import FAISS
# OPENAI 사용
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
temp_file_path = None
import tempfile
with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
    tmp_file.write(uploaded_pdf_file.getbuffer())
    temp_file_path = tmp_file.name


# 로컬 FAISS 벡터 데이터베이스 파일 저장
st.info(uploaded_pdf_file)
loader = PyPDFLoader(temp_file_path)
if loader is not None:
    st.info("loader not none")
else :
    st.info("loader none")

documents = loader.load()
if documents is not None:
    st.info("not none")
else :
    st.info(" none")
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
docs = text_splitter.split_documents(documents)

#embeddings = HuggingFaceEmbeddings()
embeddings = OpenAIEmbeddings()

index = VectorstoreIndexCreator(
    vectorstore_cls=FAISS,
    embedding=embeddings,
    ).from_loaders([loader])

# VECTORDB 파일 저장
index.vectorstore.save_local("shower")

# OPENAI 사용
openai.api_key = os.getenv("OPENAI_API_KEY")

# Retrive? 리트리버? 하여간 그 스텝 수행.
#embeddings = HuggingFaceEmbeddings()
embeddings = OpenAIEmbeddings()
# 로컬에 떨궈놓은 FAISS Vector DB 할당.
db = FAISS.load_local("shower", embeddings=embeddings, allow_dangerous_deserialization=True)

# RAG 기반 LLM 연결 메소드
def create_generator(text, db):
    content = "당신은 친절한 어시스턴트입니다. 주어진 데이터를 보고 사용자에 친절하게 대답하세요.\n" 
    content += "*" * 50
    docs = db.similarity_search(text)
    for doc in docs:
        content += doc.page_content + "\n"
        content += "*" * 50
    print(content)
    messages = [
        {
          "role": "system",
          "content": content
        },
        {
          "role": "user",
          "content": text
        },
    ]

    gen = openai.chat.completions.create(
      model="gpt-4o-mini",
      messages=messages,
      temperature=0.5,
      max_tokens=512,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0,
      stream=True
    )
    return gen

# Streamlit 앱 정의
def main():
    st.title("Multi-turn Chatbot with Streamlit and OpenAI")
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

        gen = create_generator(st.session_state.messages[-1]["content"], db)
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""        
            for chunk in gen:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content":full_response})

if __name__ == "__main__":
    main()
