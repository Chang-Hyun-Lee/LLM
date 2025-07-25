# basic/practice2_basic.py
import streamlit as st
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

st.title("💬 기초: 멀티턴 대화")

# 세션 상태 초기화
if 'messages' not in st.session_state:
    st.session_state.messages = []

# API 키 입력
api_key = st.text_input("OpenAI API Key", type="password")

if api_key:
    # LlamaIndex 설정
    Settings.llm = OpenAI(api_key=api_key)
    Settings.embed_model = OpenAIEmbedding(api_key=api_key)
    
    # 문서 로드 및 채팅 엔진 생성
    documents = SimpleDirectoryReader("../docs").load_data()
    index = VectorStoreIndex.from_documents(documents)
    chat_engine = index.as_chat_engine()
    
    st.success(f"✅ {len(documents)}개 문서로 대화 준비 완료!")
    
    # 채팅 히스토리 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # 사용자 입력
    if prompt := st.chat_input("질문하세요..."):
        # 사용자 메시지 추가
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # AI 응답
        response = chat_engine.chat(prompt)
        st.session_state.messages.append({"role": "assistant", "content": str(response)})
        with st.chat_message("assistant"):
            st.markdown(str(response))
else:
    st.warning("API 키를 입력해주세요.")