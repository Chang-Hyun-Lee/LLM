# intermediate/practice2_intermediate.py
import streamlit as st
import os
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.memory import ChatMemoryBuffer

st.set_page_config(page_title="멀티턴 채팅", page_icon="💬")
st.title("💬 중급: 멀티턴 대화 시스템")

# 세션 상태 초기화
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'chat_engine' not in st.session_state:
    st.session_state.chat_engine = None

# 사이드바
with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.text_input("OpenAI API Key", type="password")
    docs_folder = st.text_input("문서 폴더", value="../docs")
    
    # 메모리 설정
    memory_limit = st.slider("메모리 토큰 제한", 500, 3000, 1500)
    
    # 시스템 메시지 설정
    system_message = st.text_area(
        "시스템 메시지",
        value="당신은 문서 내용을 바탕으로 질문에 답하는 도우미입니다. 정확하고 도움이 되는 답변을 제공하세요.",
        height=100
    )
    
    if st.button("🔄 대화 초기화"):
        st.session_state.messages = []
        st.session_state.chat_engine = None
        st.rerun()
    
    # 대화 통계
    if st.session_state.messages:
        user_count = len([m for m in st.session_state.messages if m['role'] == 'user'])
        st.metric("대화 횟수", user_count)

@st.cache_resource
def setup_chat_engine(docs_folder, _api_key, memory_limit, system_message):
    try:
        # LlamaIndex 설정
        Settings.llm = OpenAI(api_key=_api_key)
        Settings.embed_model = OpenAIEmbedding(api_key=_api_key)
        
        # 문서 로드
        if not os.path.exists(docs_folder):
            return None, f"폴더를 찾을 수 없습니다: {docs_folder}"
        
        documents = SimpleDirectoryReader(docs_folder).load_data()
        if not documents:
            return None, "문서가 없습니다."
        
        # 인덱스 생성
        index = VectorStoreIndex.from_documents(documents)
        
        # 메모리 설정
        memory = ChatMemoryBuffer.from_defaults(token_limit=memory_limit)
        
        # 채팅 엔진 생성
        chat_engine = index.as_chat_engine(
            chat_mode="context",
            memory=memory,
            system_prompt=system_message
        )
        
        return chat_engine, f"✅ {len(documents)}개 문서로 채팅 준비 완료!"
        
    except Exception as e:
        return None, f"설정 실패: {str(e)}"

if api_key:
    # 채팅 엔진 설정
    if st.session_state.chat_engine is None:
        with st.spinner("채팅 시스템을 준비하는 중..."):
            chat_engine, message = setup_chat_engine(docs_folder, api_key, memory_limit, system_message)
        
        if chat_engine:
            st.session_state.chat_engine = chat_engine
            st.success(message)
        else:
            st.error(message)
            st.stop()
    
    # 채팅 히스토리 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # 사용자 입력
    if prompt := st.chat_input("메시지를 입력하세요..."):
        # 사용자 메시지 추가
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # AI 응답 생성
        with st.chat_message("assistant"):
            try:
                with st.spinner("답변을 생성하는 중..."):
                    response = st.session_state.chat_engine.chat(prompt)
                    answer = str(response)
                
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
                # 소스 정보 표시 (있다면)
                if hasattr(response, 'source_nodes') and response.source_nodes:
                    with st.expander("📄 참조 문서"):
                        for i, node in enumerate(response.source_nodes[:2]):  # 최대 2개만
                            st.caption(f"**소스 {i+1}:** {node.text[:150]}...")
                            
            except Exception as e:
                error_msg = f"답변 생성 중 오류: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
else:
    st.warning("⚠️ 사이드바에서 OpenAI API 키를 입력해주세요.")
    
    # 사용 방법 안내
    st.markdown("""
    ### 💡 사용 방법:
    1. **API 키 입력**: 사이드바에서 OpenAI API 키 설정
    2. **문서 준비**: `../docs` 폴더에 문서 파일들 저장
    3. **대화 시작**: 아래 입력창에서 자유롭게 질문
    4. **연속 대화**: 이전 대화 내용을 기억하며 답변
    
    ### 🔧 고급 설정:
    - **메모리 제한**: 대화 기록 유지 범위 조절
    - **시스템 메시지**: AI의 응답 스타일 조정
    """)