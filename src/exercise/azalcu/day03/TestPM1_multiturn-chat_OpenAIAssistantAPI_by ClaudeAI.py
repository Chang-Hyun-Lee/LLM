import streamlit as st
import openai
from openai import OpenAI
import time
import json

# 페이지 설정
st.set_page_config(
    page_title="AI 챗봇",
    page_icon="🤖",
    layout="wide"
)

# Assistant ID (미리 생성된 것)
ASSISTANT_ID = "asst_UIoILByMFhNJ0Q18C0m69eko"

# OpenAI 클라이언트 초기화 (캐시 함수는 순수 함수로 만들기)
@st.cache_resource
def init_openai_client(api_key):
    """OpenAI 클라이언트를 초기화합니다."""
    try:
        return OpenAI(api_key=api_key)
    except Exception as e:
        st.error(f"OpenAI 클라이언트 초기화 실패: {e}")
        return None

def create_thread(client):
    """새 스레드를 생성합니다."""
    try:
        thread = client.beta.threads.create()
        return thread.id
    except Exception as e:
        st.error(f"스레드 생성 실패: {e}")
        return None

def send_message(client, thread_id, message):
    """메시지를 스레드에 추가합니다."""
    try:
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        )
        return True
    except Exception as e:
        st.error(f"메시지 전송 실패: {e}")
        return False

def run_assistant_stream(client, thread_id, assistant_id):
    """Assistant를 실행하고 스트리밍으로 응답을 받습니다."""
    # 스트리밍 기능은 일시적으로 비활성화하고 일반 모드로 실행
    return run_assistant_normal(client, thread_id, assistant_id)

def run_assistant_normal(client, thread_id, assistant_id):
    """Assistant를 실행하고 일반적인 방식으로 응답을 받습니다."""
    try:
        # Run 생성
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )
        
        # Run 완료까지 대기
        with st.spinner("AI가 답변을 생성하고 있습니다..."):
            while run.status in ['queued', 'in_progress']:
                time.sleep(1)
                run = client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )
        
        if run.status == 'completed':
            # 최신 Assistant 메시지 가져오기 (더 안전한 방식)
            messages = client.beta.threads.messages.list(thread_id=thread_id)
            
            # Assistant 역할의 최신 메시지 찾기 (역순으로 검색)
            for message in reversed(messages.data):
                if message.role == "assistant" and message.content:
                    # content가 존재하고 text 타입인지 확인
                    for content in message.content:
                        if hasattr(content, 'text') and hasattr(content.text, 'value'):
                            return content.text.value
            
            st.warning("Assistant 응답을 찾을 수 없습니다.")
            return None
        else:
            st.error(f"Run 실행 실패: {run.status}")
            return None
            
    except Exception as e:
        st.error(f"Assistant 실행 실패: {e}")
        return None

def main():
    st.title("🤖 AI 챗봇")
    st.markdown("---")
    
    # 🔑 API 키 입력 (캐시 함수 밖에서 처리)
    # secrets.toml 파일이 없어도 오류가 나지 않도록 예외 처리
    try:
        api_key = st.secrets.get("OPENAI_API_KEY", None)
    except:
        api_key = None
    
    if not api_key:
        api_key = st.sidebar.text_input(
            "OpenAI API Key", 
            type="password",
            help="OpenAI API 키를 입력하세요",
            placeholder="sk-..."
        )
    
    # API 키가 없으면 안내 화면 표시
    if not api_key:
        # 사이드바 설정 (API 키 없을 때도 보이도록)
        with st.sidebar:
            st.header("⚙️ 설정")
            st.info("**Assistant ID:** " + ASSISTANT_ID)
            
        st.warning("⚠️ OpenAI API 키가 필요합니다. 사이드바에서 입력해주세요.")
        st.markdown("""
        ### 🔑 API 키 얻는 방법:
        1. [OpenAI Platform](https://platform.openai.com/api-keys)에 접속
        2. 로그인 후 'Create new secret key' 클릭  
        3. 생성된 키를 복사해서 사이드바에 입력
        
        ### 📝 또는 secrets.toml 파일 사용:
        ```toml
        # .streamlit/secrets.toml
        OPENAI_API_KEY = "your-api-key-here"
        ```
        """)
        return
    
    # 사이드바 설정
    with st.sidebar:
        st.header("⚙️ 설정")
        
        # API 키 상태 표시
        if api_key:
            st.success("✅ API 키 설정됨")
        
        # 스트리밍 옵션
        use_streaming = st.checkbox("스트리밍 사용", value=True)
        
        # 새 대화 시작 버튼
        if st.button("🔄 새 대화 시작"):
            for key in ['thread_id', 'messages']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
        
        # Assistant 정보
        st.info(f"**Assistant ID:** {ASSISTANT_ID}")
        
        # 대화 통계
        if 'messages' in st.session_state:
            message_count = len([msg for msg in st.session_state.messages if msg['role'] == 'user'])
            st.metric("총 메시지 수", message_count)
    
    # OpenAI 클라이언트 초기화 (API 키를 매개변수로 전달)
    client = init_openai_client(api_key)
    
    if client is None:
        st.error("OpenAI 클라이언트 초기화에 실패했습니다. API 키를 확인해주세요.")
        return
    
    # 세션 상태 초기화
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'thread_id' not in st.session_state:
        thread_id = create_thread(client)
        if thread_id:
            st.session_state.thread_id = thread_id
        else:
            st.error("스레드 생성에 실패했습니다. 페이지를 새로고침하거나 API 키를 확인해주세요.")
            st.stop()
    
    # 채팅 히스토리 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # 사용자 입력
    if prompt := st.chat_input("메시지를 입력하세요..."):
        # 사용자 메시지 표시
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # 세션에 사용자 메시지 추가
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # 스레드에 메시지 전송
        if send_message(client, st.session_state.thread_id, prompt):
            # Assistant 응답
            with st.chat_message("assistant"):
                # 현재는 스트리밍 기능을 비활성화하고 일반 모드만 사용
                if use_streaming:
                    st.info("스트리밍 모드 선택됨 (현재 일반 모드로 실행)")
                
                response = run_assistant_normal(client, st.session_state.thread_id, ASSISTANT_ID)
                
                if response:
                    # 세션에 Assistant 응답 추가
                    st.session_state.messages.append({"role": "assistant", "content": response})
                else:
                    st.error("응답을 받을 수 없습니다.")

if __name__ == "__main__":
    main()