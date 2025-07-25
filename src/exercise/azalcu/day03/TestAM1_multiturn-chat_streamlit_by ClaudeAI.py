import streamlit as st
from openai import OpenAI
import os
from typing import Generator

# 페이지 설정
st.set_page_config(
    page_title="멀티턴 ChatGPT 챗봇",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일링
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #2E86AB;
        margin-bottom: 2rem;
    }
    .chat-container {
        max-height: 600px;
        overflow-y: auto;
        padding: 1rem;
        border-radius: 10px;
        background-color: #f8f9fa;
    }
    .stChatMessage {
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

class StreamlitChatBot:
    """Streamlit용 ChatBot 클래스"""
    
    def __init__(self):
        self.client = None
        
    def initialize_client(self, api_key: str):
        """OpenAI 클라이언트 초기화"""
        try:
            self.client = OpenAI(api_key=api_key)
            return True
        except Exception as e:
            st.error(f"API 키 설정 오류: {str(e)}")
            return False
    
    def get_response_streaming(self, messages: list) -> Generator[str, None, None]:
        """스트리밍 방식으로 ChatGPT 응답 생성"""
        if not self.client:
            yield "❌ OpenAI 클라이언트가 초기화되지 않았습니다."
            return
            
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                stream=True,
                max_tokens=1000,
                temperature=0.7
            )
            
            full_response = ""
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield full_response
                    
        except Exception as e:
            yield f"❌ 오류가 발생했습니다: {str(e)}"

# ChatBot 인스턴스 초기화
if 'chatbot' not in st.session_state:
    st.session_state.chatbot = StreamlitChatBot()

# 세션 상태 초기화
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'api_key_set' not in st.session_state:
    st.session_state.api_key_set = False

# 메인 헤더
st.markdown('<h1 class="main-header">🤖 멀티턴 ChatGPT 챗봇</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #666;">ChatGPT와 연속적인 대화를 나눠보세요! (Streamlit + 스트리밍)</p>', unsafe_allow_html=True)

# 사이드바 - 설정 패널
with st.sidebar:
    st.header("⚙️ 설정")
    
    # API 키 입력
    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        placeholder="sk-...",
        help="OpenAI API 키를 입력하세요"
    )
    
    if api_key and not st.session_state.api_key_set:
        if st.session_state.chatbot.initialize_client(api_key):
            st.session_state.api_key_set = True
            st.success("✅ API 키가 설정되었습니다!")
        else:
            st.session_state.api_key_set = False
    
    st.divider()
    
    # 대화 설정
    st.subheader("💬 대화 설정")
    
    # 대화 초기화 버튼
    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.success("대화가 초기화되었습니다!")
        st.rerun()
    
    # 통계 정보
    st.divider()
    st.subheader("📊 대화 통계")
    st.info(f"💬 총 메시지 수: {len(st.session_state.messages)}")
    
    if st.session_state.messages:
        user_msgs = len([m for m in st.session_state.messages if m["role"] == "user"])
        assistant_msgs = len([m for m in st.session_state.messages if m["role"] == "assistant"])
        st.info(f"👤 사용자: {user_msgs}개")
        st.info(f"🤖 ChatGPT: {assistant_msgs}개")

# 메인 채팅 영역
col1, col2, col3 = st.columns([1, 8, 1])

with col2:
    # API 키 확인
    if not st.session_state.api_key_set:
        st.warning("⚠️ 먼저 사이드바에서 OpenAI API 키를 입력해주세요!")
        st.info("💡 OpenAI API 키는 https://platform.openai.com/api-keys 에서 발급받을 수 있습니다.")
    else:
        # 채팅 히스토리 표시
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # 사용자 입력
        if prompt := st.chat_input("ChatGPT에게 메시지를 입력하세요..."):
            # 사용자 메시지 추가
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # 사용자 메시지 표시
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # ChatGPT 응답 생성 및 표시
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                
                # 스트리밍 응답 생성
                response_generator = st.session_state.chatbot.get_response_streaming(
                    st.session_state.messages
                )
                
                # 스트리밍으로 응답 표시
                full_response = ""
                for partial_response in response_generator:
                    full_response = partial_response
                    response_placeholder.markdown(partial_response + "▌")
                
                # 최종 응답 표시 (커서 제거)
                response_placeholder.markdown(full_response)
                
                # 응답을 세션 상태에 추가
                st.session_state.messages.append({"role": "assistant", "content": full_response})

# 하단 정보 패널
st.divider()

# 확장 가능한 사용법 안내
with st.expander("📖 사용법 및 기능 안내"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🚀 주요 기능
        - **멀티턴 대화**: 이전 대화 맥락을 기억
        - **실시간 스트리밍**: 응답 생성 과정을 실시간 확인
        - **대화 기록 관리**: 언제든 대화 초기화 가능
        - **통계 정보**: 대화 현황을 한눈에 확인
        
        ### 💡 사용 팁
        - 구체적이고 명확한 질문을 하면 더 좋은 답변을 받을 수 있습니다
        - 이전 대화 내용을 참조하여 연속적인 질문 가능
        - 주제를 바꾸고 싶으면 '대화 초기화' 사용
        """)
    
    with col2:
        st.markdown("""
        ### ⚙️ 설정 방법
        1. **API 키 발급**: OpenAI 웹사이트에서 API 키 생성
        2. **키 입력**: 사이드바의 설정 패널에 API 키 입력
        3. **대화 시작**: 하단 채팅 입력창에 메시지 작성
        4. **응답 확인**: 실시간으로 생성되는 응답 확인
        
        ### ⚠️ 주의사항
        - OpenAI API 키가 반드시 필요합니다
        - 인터넷 연결이 필요합니다
        - API 사용량에 따라 요금이 부과됩니다
        - API 키는 안전하게 보관하세요
        """)

# 푸터
st.markdown("---")
st.markdown(
    '<p style="text-align: center; color: #888; font-size: 0.8rem;">💻 Streamlit으로 구현된 멀티턴 ChatGPT 챗봇 | 코시파교육 Day3 실습</p>',
    unsafe_allow_html=True
)

if __name__ == "__main__":
    import subprocess
    import sys
    import os
    
    # 현재 파일을 streamlit으로 실행
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            __file__, 
            "--server.address", "0.0.0.0",
            "--server.port", "8501",
            "--browser.serverAddress", "localhost"
        ])
    except KeyboardInterrupt:
        print("Streamlit 서버가 종료되었습니다.")
