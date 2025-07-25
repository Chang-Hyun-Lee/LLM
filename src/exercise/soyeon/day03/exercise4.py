#실습 #1. llama_index와 Streamlit을 사용하여 인덱스된 파일에 대해서 답변하는 어플리케이션을 작성하시오.
#실습 #2. llama_index와 Streamlit을 사용하여 인덱스된 파일에 대해서 답변하는 어플리케이션을 멀티턴으로 바꾸시오.
#실습 #3. llama_index와 Streamlit을 사용하여 파일을 업로드하고 업로드한 파일 전체에 대해서 설명하는 어플리케이션을 작성하시오.
#실습 #4. 실습 #3의 어플리케이션에서 파일을 리스트업하고 삭제할 수 있는 인터페이스를 작성하시오.

from llama_index.llms.openai import OpenAI
from llama_index.core import Settings,VectorStoreIndex, SimpleDirectoryReader
import streamlit as st
import os

Settings.llm = OpenAI(temperature=0, model="gpt-4o-mini")
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok = True)

# 파일 업로드 (위치 : sidebar)
uploaded_file = st.sidebar.file_uploader("파일 올리기", type=["pdf", 'txt', 'json'])
if uploaded_file:
    file_path = os.path.join(DATA_DIR, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    # 캐시 한 번 clear했다가 다시 작동됨
    st.cache_resource.clear()
    st.toast(f"{uploaded_file} 업로드 완료")

# data 디렉토리  파일 (위치 : sidebar)
file_list = os.listdir(DATA_DIR)
if file_list:
    for fname in file_list:
        col1, col2 = st.sidebar.columns([5, 1])
        with col1:
            st.sidebar.markdown(f" - {fname}")
        with col2:
            if st.button("삭제", key=fname):
                os.remove(os.path.join(DATA_DIR, fname))
                # 캐시 되서 파일 이름 사라짐
                st.cache_resource.clear()
                st.rerun()

@st.cache_resource
def index_data():
    # SimpleDerectoryReader 읽을 수 있는거 거의 다 읽음
    documents = SimpleDirectoryReader(DATA_DIR).load_data()
    return VectorStoreIndex.from_documents(documents)

index = index_data()
query_engine = index.as_query_engine()

# streamlit 

st.title("DATA Directory 읽어 와서 질문 받기")

user_input = st.chat_input("질문 기릿")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_input : 
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role" : "user" , "content" : user_input})

    with st.chat_message("assistant"):
        #spinner 넣으면 뱅글뱅글
        with st.spinner("GPT는 고민중 ~"):
            response = query_engine.query(user_input)
            st.markdown(response)

    st.session_state.messages.append({"role" : "assistant", "content" : response})
