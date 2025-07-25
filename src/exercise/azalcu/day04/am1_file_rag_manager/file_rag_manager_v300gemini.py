import streamlit as st
import os
from datetime import datetime
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings, Document
from llama_index.core.schema import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.prompts import PromptTemplate

# 페이지 설정
st.set_page_config(
    page_title="업로드파일 기반의 챗봇",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 간단하고 안정적인 CSS 스타일링
st.markdown("""
<style>
    /* 생략: 기존 CSS와 동일 */
    .file-card {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0, 0,0, 0.05);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 15px;
        padding: 1rem;
        border-radius: 20px;
        margin: 1rem 0;
    }
    .stTabs [data-baseweb="tab"] {
        height: 60px;
        padding: 1rem 2rem;
        border-radius: 15px;
        font-size: 18px;
        font-weight: 700;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)


# 지원되는 파일 형식 정의
SUPPORTED_EXTENSIONS = {
    '.txt': 'text/plain', '.md': 'text/markdown', '.py': 'text/x-python',
    '.js': 'text/javascript', '.html': 'text/html', '.css': 'text/css',
    '.json': 'application/json', '.csv': 'text/csv', '.pdf': 'application/pdf',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.doc': 'application/msword'
}

# 데이터 디렉토리 설정
DATA_DIR = "./data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# 세션 상태 안전한 초기화
def init_session_state():
    """세션 상태 변수들을 안전하게 초기화"""
    if 'openai_api_key' not in st.session_state:
        st.session_state.openai_api_key = ""
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'selected_files_for_chat' not in st.session_state:
        st.session_state.selected_files_for_chat = []
    if 'query_engine' not in st.session_state:
        st.session_state.query_engine = None
    if 'current_language' not in st.session_state:
        st.session_state.current_language = "한국어"
    if 'current_chat_language' not in st.session_state:
        st.session_state.current_chat_language = "한국어"
    if 'previous_files' not in st.session_state:
        st.session_state.previous_files = []

# 세션 상태 초기화 실행
init_session_state()

def get_file_extension(filename):
    """파일 확장자 추출"""
    return os.path.splitext(filename)[1].lower()

def is_supported_file(filename):
    """지원되는 파일 형식인지 확인"""
    return get_file_extension(filename) in SUPPORTED_EXTENSIONS

def generate_unique_filename(filename):
    """중복 방지를 위한 고유 파일명 생성"""
    name, ext = os.path.splitext(filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{name}_{timestamp}{ext}"

def save_uploaded_file(uploaded_file):
    """업로드된 파일을 data 디렉토리에 저장"""
    try:
        if not is_supported_file(uploaded_file.name):
            return None, f"지원되지 않는 파일 형식입니다: {get_file_extension(uploaded_file.name)}"
        unique_filename = generate_unique_filename(uploaded_file.name)
        file_path = os.path.join(DATA_DIR, unique_filename)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return file_path, f"파일이 성공적으로 저장되었습니다: {unique_filename}"
    except Exception as e:
        return None, f"파일 저장 중 오류 발생: {str(e)}"

def get_file_info(file_path):
    """파일 정보 가져오기"""
    try:
        stat = os.stat(file_path)
        return {
            'name': os.path.basename(file_path), 'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime), 'path': file_path,
            'extension': get_file_extension(file_path)
        }
    except Exception:
        return None

def delete_file(file_path):
    """파일 삭제"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        st.error(f"파일 삭제 중 오류 발생: {str(e)}")
        return False

def clear_chat_state():
    """채팅 관련 세션 상태 안전하게 초기화"""
    st.session_state.chat_history = []
    st.session_state.query_engine = None
    st.session_state.selected_files_for_chat = []

def setup_llama_index():
    """LlamaIndex 설정 (API 키가 있을 때만)"""
    if not st.session_state.openai_api_key:
        return False, "OpenAI API 키가 설정되지 않았습니다."
    try:
        from llama_index.llms.openai import OpenAI
        from llama_index.embeddings.openai import OpenAIEmbedding
        os.environ["OPENAI_API_KEY"] = st.session_state.openai_api_key
        Settings.llm = OpenAI(model="gpt-3.5-turbo", temperature=0.1)
        Settings.embed_model = OpenAIEmbedding()
        Settings.text_splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
        return True, "LlamaIndex 설정 완료"
    except ImportError:
        return False, "OpenAI 관련 패키지가 설치되지 않았습니다."
    except Exception as e:
        return False, f"LlamaIndex 설정 중 오류: {str(e)}"


# 메인 헤더
st.markdown("""
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 0.5rem 1rem; text-align: center; position: fixed; top: 0; left: 0; right: 0; z-index: 1000; display: flex; align-items: center; justify-content: center; height: 50px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
    <h4 style="margin: 0; font-size: 1.2rem; font-weight: 600;">🤖 업로드파일 기반의 챗봇</h4>
</div>
<div style="height: 60px;"></div>
""", unsafe_allow_html=True)

# 사이드바
with st.sidebar:
    st.markdown("### ⚙️ 설정")
    api_key = st.text_input("OpenAI API 키를 입력하세요", type="password",
                           value=st.session_state.openai_api_key,
                           help="AI 챗봇을 사용하려면 API 키가 필요합니다.")
    if api_key:
        st.session_state.openai_api_key = api_key
        st.success("✅ API 키가 설정되었습니다.")

    st.markdown("---")
    st.markdown("### 🌍 언어 설정")
    language_options = {
        "한국어": "한국어로 답변해주세요.", "English": "Please respond in English.",
        "中文": "请用中文回答。", "日本語": "日本語で回答してください。",
    }
    selected_language = st.selectbox(
        "채팅 언어를 선택하세요:", list(language_options.keys()),
        index=list(language_options.keys()).index(st.session_state.current_language)
    )
    if selected_language != st.session_state.current_language:
        st.session_state.current_language = selected_language
        st.warning(f"🌍 언어가 {selected_language}로 변경되었습니다. 새 대화를 시작합니다.")
        clear_chat_state()
        st.rerun()

    st.markdown("---")
    st.markdown("### 📄 지원 파일 형식")
    st.info("PDF, DOCX, TXT, MD 등 다양한 텍스트 기반 파일을 지원합니다.")

    st.markdown("---")
    st.markdown("### 📈 통계")
    files = [f for f in os.listdir(DATA_DIR) if os.path.isfile(os.path.join(DATA_DIR, f))]
    st.metric("저장된 파일", f"{len(files)} 개")
    if 'chat_history' in st.session_state and st.session_state.chat_history:
        st.metric("💬 총 대화 수", f"{len(st.session_state.chat_history)} 건")

# 메인 영역 - 탭 구성
tab1, tab2, tab3 = st.tabs(["📤 파일 업로드", "📂 파일 관리", "💬 AI 챗봇"])

with tab1:
    st.markdown("### 📤 파일 업로드")
    st.info("대화하고 싶은 문서를 업로드하세요. PDF, DOCX, TXT 파일 등을 지원합니다.")
    uploaded_files = st.file_uploader(
        "파일을 선택하거나 드래그해서 업로드하세요",
        accept_multiple_files=True,
        help="여러 파일을 동시에 업로드할 수 있습니다."
    )
    if uploaded_files:
        for uploaded_file in uploaded_files:
            if st.button(f"💾 '{uploaded_file.name}' 저장", key=f"save_{uploaded_file.name}"):
                file_path, message = save_uploaded_file(uploaded_file)
                if file_path:
                    st.success(f"✅ '{os.path.basename(file_path)}' 저장 완료!")
                else:
                    st.error(f"❌ 저장 실패: {message}")

with tab2:
    st.markdown("### 📂 파일 관리")
    files = [f for f in os.listdir(DATA_DIR) if os.path.isfile(os.path.join(DATA_DIR, f))]
    if not files:
        st.info("💡 저장된 파일이 없습니다. '파일 업로드' 탭에서 파일을 추가해주세요.")
    else:
        if st.button("🗑️ 모든 파일 삭제", type="secondary"):
            for file in files:
                delete_file(os.path.join(DATA_DIR, file))
            clear_chat_state() # 파일 삭제 시 채팅 상태도 초기화
            st.success("🎉 모든 파일이 삭제되었습니다!")
            st.rerun()

        st.markdown("---")
        for file in files:
            file_info = get_file_info(os.path.join(DATA_DIR, file))
            if file_info:
                with st.container():
                    st.markdown(f"""
                    <div class="file-card">
                        <h5>📄 {file_info['name']}</h5>
                        <span><strong>크기:</strong> {file_info['size'] / 1024:.1f} KB</span> |
                        <span><strong>수정일:</strong> {file_info['modified'].strftime('%Y-%m-%d %H:%M')}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"🗑️ 삭제", key=f"delete_{file}", type="secondary"):
                        if delete_file(file_info['path']):
                            st.success(f"✅ '{file}' 삭제 완료!")
                            st.rerun()

with tab3:
    st.markdown("### 💬 AI 챗봇")
    files = [f for f in os.listdir(DATA_DIR) if os.path.isfile(os.path.join(DATA_DIR, f))]

    if not files:
        st.warning("⚠️ 먼저 파일을 업로드해주세요. '파일 업로드' 탭에서 문서를 추가할 수 있습니다.")
    else:
        # ✅ 변경: st.selectbox -> st.multiselect로 변경하여 다중 선택 가능
        selected_files = st.multiselect(
            "📄 대화할 문서들을 선택하세요 (여러 개 선택 가능):",
            files,
            default=st.session_state.selected_files_for_chat,
            key="chat_file_selector"
        )
        
        # 선택된 파일 목록이나 언어가 변경되었는지 확인
        if (sorted(selected_files) != sorted(st.session_state.selected_files_for_chat) or
            selected_language != st.session_state.current_chat_language):
            
            st.session_state.selected_files_for_chat = selected_files
            st.session_state.current_chat_language = selected_language
            st.session_state.query_engine = None  # 엔진 재생성 필요
            
            # 파일 목록이 변경될 때만 채팅 기록 초기화
            if sorted(selected_files) != sorted(st.session_state.get('previous_files', [])):
                st.session_state.chat_history = []
                st.session_state.previous_files = selected_files
                if selected_files:
                    st.info(f"📄 **{', '.join(selected_files)}** 문서로 새 대화를 시작합니다.")

        if not st.session_state.openai_api_key:
            st.warning("⚠️ AI 챗봇을 사용하려면 사이드바에서 OpenAI API 키를 입력해주세요.")
        elif not selected_files:
            st.info("💡 위 목록에서 대화할 문서를 한 개 이상 선택해주세요.")
        else:
            # 쿼리 엔진 초기화
            if st.session_state.query_engine is None:
                try:
                    with st.spinner(f"📄 {', '.join(selected_files)} 분석 중... 잠시만 기다려주세요."):
                        setup_success, setup_message = setup_llama_index()
                        if setup_success:
                            # ✅ 변경: 선택된 모든 파일 경로를 리스트로 전달
                            input_file_paths = [os.path.join(DATA_DIR, f) for f in selected_files]
                            documents = SimpleDirectoryReader(input_files=input_file_paths).load_data()

                            if documents:
                                index = VectorStoreIndex.from_documents(documents)
                                
                                language_instruction = language_options.get(selected_language, "한국어로 답변해주세요.")
                                qa_template = PromptTemplate(
                                    "Context information is below.\n"
                                    "---------------------\n"
                                    "{context_str}\n"
                                    "---------------------\n"
                                    f"IMPORTANT LANGUAGE INSTRUCTION: {language_instruction}\n"
                                    "Based on the context information above, answer the following question: {query_str}\n"
                                    "Answer: "
                                )
                                
                                st.session_state.query_engine = index.as_query_engine(text_qa_template=qa_template)
                                st.success(f"✅ 분석 완료! 이제 {selected_language}로 대화할 수 있습니다.")
                            else:
                                st.error("문서를 읽을 수 없습니다. 파일 형식을 확인해주세요.")
                        else:
                            st.error(f"설정 오류: {setup_message}")
                except Exception as e:
                    st.error(f"문서 분석 중 오류 발생: {str(e)}")

            # 챗봇 인터페이스
            if st.session_state.query_engine:
                # 채팅 기록 표시
                for chat in st.session_state.chat_history:
                    with st.chat_message("user", avatar="👤"):
                        st.markdown(chat['user'])
                    with st.chat_message("assistant", avatar="🤖"):
                        st.markdown(chat['ai'])

                # ✅ 변경: st.form을 사용하여 Enter 키로 입력 제출 기능 구현
                with st.form(key='chat_form', clear_on_submit=True):
                    user_input = st.text_input(
                        "질문을 입력하세요:",
                        placeholder=f"{', '.join(selected_files)}에 대해 질문해보세요...",
                        key="chat_input"
                    )
                    submit_button = st.form_submit_button(
                        label="📤 전송", 
                        type="primary"
                    )

                if submit_button and user_input:
                    with st.spinner("🤖 AI가 답변을 생성하고 있습니다..."):
                        try:
                            response = st.session_state.query_engine.query(user_input.strip())
                            st.session_state.chat_history.append({
                                'user': user_input.strip(),
                                'ai': str(response)
                            })
                            st.rerun() # 입력 폼 비우고 즉시 다시 그리기
                        except Exception as e:
                            st.error(f"답변 생성 중 오류가 발생했습니다: {str(e)}")

# 푸터
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #888; margin-top: 2rem; padding: 1rem;">
    <p>🤖 <strong>업로드파일 기반의 챗봇 v2.2</strong> (다중문서 & Enter키 지원)</p>
</div>
""", unsafe_allow_html=True)