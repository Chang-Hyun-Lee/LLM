import os
import streamlit as st
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SentenceSplitter

# 환경변수에서 OpenAI API 키 가져오기
import openai
openai.api_key = os.getenv("OPENAI_API_KEY")

# llama_index 설정
Settings.llm = OpenAI(temperature=0, model="gpt-4o-mini")
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=20)

st.title("💬 멀티턴 문서 기반 챗봇")

# 인덱스 생성 또는 불러오기
@st.cache_resource
def get_chat_engine():
    documents = SimpleDirectoryReader("data").load_data()
    index = VectorStoreIndex.from_documents(documents)
    return index.as_chat_engine(chat_mode="condense_question", verbose=True)

chat_engine = get_chat_engine()

# 세션 상태 초기화
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 사용자 질문 입력
user_input = st.chat_input("질문을 입력하세요")

# 메시지 렌더링
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 질문 처리
if user_input:
    # 사용자 메시지 출력
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 챗엔진으로부터 응답 생성
    with st.chat_message("assistant"):
        with st.spinner("생성 중..."):
            response = chat_engine.chat(user_input)
            st.markdown(response.response)
            st.session_state.chat_history.append({"role": "assistant", "content": response.response})
