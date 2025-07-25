import os
import streamlit as st
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.chat_engine import ContextChatEngine
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings

# 🌐 환경 변수 설정 (OPENAI API 키)
openai_api_key = os.getenv("OPENAI_API_KEY")
Settings.llm = OpenAI(model="gpt-4o", temperature=0)

# 📄 문서 로딩 및 벡터 인덱스 생성
@st.cache_resource
def load_index():
    documents = SimpleDirectoryReader("data").load_data()
    index = VectorStoreIndex.from_documents(documents)
    return index

# 🤖 RAG 기반 챗엔진 초기화
@st.cache_resource
def init_rag_chat_engine():
    index = load_index()
    chat_engine = index.as_chat_engine(
        chat_mode="context",
        memory=ChatMemoryBuffer(token_limit=3000)
    )
    return chat_engine

# 💬 Streamlit 챗봇 인터페이스
def main():
    st.set_page_config(page_title="RAG 기반 챗봇", page_icon="🧠")
    st.title("🧠 RAG 기반 GPT 챗봇")
    st.write("캠핑, 주식, 식당 관련 질문을 해보세요!")

    chat_engine = init_rag_chat_engine()

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("질문을 입력하세요")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.spinner("답변 생성 중..."):
            response = chat_engine.chat(user_input)
            answer = response.response

        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.markdown(answer)

if __name__ == "__main__":
    main()
