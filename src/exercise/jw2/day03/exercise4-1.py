# 실습 #1. llama_index와 Streamlit을 사용하여 인덱스된 파일에 대해서 답변하는 어플리케이션을 작성하시오.
#실습 #2. llama_index와 Streamlit을 사용하여 인덱스된 파일에 대해서 답변하는 어플리케이션을 멀티턴으로 바꾸시오.
#실습 #3. llama_index와 Streamlit을 사용하여 파일을 업로드하고 업로드한 파일 전체에 대해서 설명하는 어플리케이션을 작성하시오.
#실습 #4. 실습 #3의 어플리케이션에서 파일을 리스트업하고 삭제할 수 있는 인터페이스를 작성하시오.

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, SummaryIndex


#response = query_engine.query("소년과 소녀는 어디에서 처음 만났나? 한국어로 대답해줘.")
#print(response)

import streamlit as st
import os
import openai

from tempfile import TemporaryDirectory

st.title("📄 문서 업로드")

# 여러 파일 업로드 가능 (PDF, TXT 등)
uploaded_files = st.file_uploader("문서를 업로드하세요", type=["pdf", "txt", "md"], accept_multiple_files=True)

documents = []

# 처음 데이터 불러와서 요약하는 부분
@st.cache_data
def data_open(files):
    if files:
        with st.spinner("문서를 처리 중입니다..."):
            with TemporaryDirectory() as tmpdir:
                for file in files:
                    file_path = os.path.join(tmpdir, file.name)
                    with open(file_path, "wb") as f:
                        f.write(file.read())

                documents = SimpleDirectoryReader(tmpdir).load_data()
                index = SummaryIndex.from_documents(documents)
                query_engine = index.as_query_engine()
                summary = query_engine.query("이 문서 전체를 요약해줘")
        return summary
    return None

summary = data_open(uploaded_files)

st.write("문서 미리보기:")
if summary:  # summary가 None이 아닐 때
    st.write(summary.response)
else:
    st.write("업로드된 문서가 없습니다.")

documents = SimpleDirectoryReader("data").load_data()
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()


openai.api_key = os.getenv("OPENAI_API_KEY")

if "messages" not in st.session_state:
    st.session_state["messages"] = []

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_input = st.chat_input("메시지를 입력하세요...")

response = query_engine.query(f"{user_input}+한글로 말해줘")

if user_input:
    
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)


    st.session_state["messages"].append({"role": "assistant", "content": response.response})
    with st.chat_message("assistant"):
        st.write(response.response)
