# app.py
import streamlit as st
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.core.query_engine import RetrieverQueryEngine

st.set_page_config(page_title="PDF Q&A", layout="wide")

# 세션 상태 초기화
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 인덱스 로드
@st.cache_resource
def load_index():
    storage_context = StorageContext.from_defaults(persist_dir="index")
    return load_index_from_storage(storage_context)

index = load_index()
query_engine = RetrieverQueryEngine.from_args(index.as_retriever())

# UI
st.title("📄 PDF 기반 질의응답 챗봇")

user_input = st.chat_input("질문을 입력하세요")
if user_input:
    st.session_state.chat_history.append(("user", user_input))

    with st.spinner("답변 생성 중..."):

        #멀티턴(LLM에 전체 대화 기록을 함께 전달 (문맥 유지))
        full_context = "\n".join([f"{role}: {msg}" for role, msg in st.session_state.chat_history if role == "user" or role == "bot"])
        full_context += f"\nuser: {user_input}"

        response = query_engine.query(full_context)
        st.session_state.chat_history.append(("bot", str(response)))

# 대화 내역 표시
for role, msg in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(msg)
