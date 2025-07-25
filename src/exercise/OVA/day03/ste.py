import streamlit as st
from openai import OpenAI
import os

# 🔑 OpenAI 클라이언트 초기화 (환경변수 사용 권장)
@st.cache_resource
def init_openai_client():
    api_key = os.getenv("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")
    if not api_key:
        st.error("⚠️ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        st.info("환경변수를 설정하거나 사이드바에서 API 키를 입력해주세요.")
        return None
    return OpenAI(api_key=api_key)

# 🔧 페이지 설정
st.set_page_config(
    page_title="멀티턴 챗봇",
    page_icon="🤖",
    layout="wide"
)

# 🎨 사이드바 설정
with st.sidebar:
    st.header("⚙️ 설정")
    
    # API 키 입력 (환경변수가 없을 때만)
    if not os.getenv("OPENAI_API_KEY"):
        api_key_input = st.text_input("OpenAI API 키", type="password", help="보안을 위해 환경변수 사용을 권장합니다.")
        if api_key_input:
            client = OpenAI(api_key=api_key_input)
        else:
            client = None
    else:
        client = init_openai_client()
    
    # 모델 선택
    model_options = ["gpt-4o", "gpt-4", "gpt-3.5-turbo"]
    selected_model = st.selectbox("모델 선택", model_options, index=0)
    
    # 시스템 메시지 커스터마이징
    system_message = st.text_area(
        "시스템 메시지",
        value="당신은 친절하고 도움이 되는 AI 어시스턴트입니다.",
        height=100
    )
    
    # 대화 초기화 버튼
    if st.button("🗑️ 대화 초기화", type="secondary", use_container_width=True):
        st.session_state.messages = [{"role": "system", "content": system_message}]
        st.rerun()

# 📱 메인 인터페이스
st.title("🤖 멀티턴 GPT 챗봇")
st.markdown("OpenAI API를 사용한 대화형 챗봇입니다.")

# 🔄 대화 기록 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": system_message}]

# API 클라이언트 확인
if client is None:
    st.warning("OpenAI API 키가 필요합니다. 사이드바에서 설정해주세요.")
    st.stop()

# 📝 채팅 컨테이너
chat_container = st.container()

# 💬 채팅 내역 표시
with chat_container:
    for msg in st.session_state.messages[1:]:  # system 메시지 제외
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.write(msg["content"])
        elif msg["role"] == "assistant":
            with st.chat_message("assistant"):
                st.write(msg["content"])

# 📥 사용자 입력 처리
if prompt := st.chat_input("메시지를 입력하세요..."):
    # 사용자 메시지 표시 및 저장
    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 챗봇 응답 생성 및 표시
    with st.chat_message("assistant"):
        with st.spinner("생각하는 중..."):
            try:
                response = client.chat.completions.create(
                    model=selected_model,
                    messages=st.session_state.messages,
                    temperature=0.7,
                    max_tokens=1000
                )
                bot_reply = response.choices[0].message.content
                st.write(bot_reply)
                
                # 챗봇 응답 저장
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                
            except Exception as e:
                error_msg = f"❌ API 호출 중 오류가 발생했습니다: {str(e)}"
                st.error(error_msg)
                
                # 사용자 메시지는 유지하되 오류 메시지는 저장하지 않음
                if "API key" in str(e).lower():
                    st.info("API 키를 확인해주세요.")
                elif "rate limit" in str(e).lower():
                    st.info("API 호출 한도를 초과했습니다. 잠시 후 다시 시도해주세요.")

# 📊 대화 통계 (선택사항)
if len(st.session_state.messages) > 1:
    with st.expander("📊 대화 통계"):
        user_messages = sum(1 for msg in st.session_state.messages if msg["role"] == "user")
        assistant_messages = sum(1 for msg in st.session_state.messages if msg["role"] == "assistant")
        total_chars = sum(len(msg["content"]) for msg in st.session_state.messages)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("사용자 메시지", user_messages)
        with col2:
            st.metric("AI 응답", assistant_messages)
        with col3:
            st.metric("총 문자 수", total_chars)

# 🔒 보안 정보
st.markdown("---")
st.info("🔒 **보안 팁**: API 키는 환경변수(`OPENAI_API_KEY`)로 설정하는 것이 안전합니다.")