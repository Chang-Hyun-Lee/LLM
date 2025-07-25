import streamlit as st
import os
from datetime import datetime
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.core.schema import Document
from llama_index.core.node_parser import SentenceSplitter, TokenTextSplitter
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.prompts import PromptTemplate  # ✅ 추가된 import

# 페이지 설정
st.set_page_config(
    page_title="업로드파일기반의 챗봇", 
    page_icon="🤖", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ✅ 강제로 기본 메시지 표시 (디버깅용)
st.write("✅ Streamlit 앱이 정상 작동 중입니다!")

# 간단하고 안정적인 CSS 스타일링
st.markdown("""
<style>
    .file-card {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    .status-success {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 0.75rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    
    .status-warning {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 0.75rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    
    /* 탭 크기 대폭 확대 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 15px;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1.5rem;
        border-radius: 20px;
        border: 4px solid #dee2e6;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
        margin: 1rem 0;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 90px;
        padding: 1.5rem 3rem;
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border-radius: 15px;
        font-size: 22px;
        font-weight: 800;
        border: 4px solid #6c757d;
        transition: all 0.3s ease;
        color: #495057 !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        text-transform: uppercase;
        letter-spacing: 1px;
        min-width: 200px;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: 4px solid #667eea !important;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5) !important;
        transform: translateY(-5px) scale(1.02);
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%);
        border-color: #495057;
        transform: translateY(-3px) scale(1.01);
        box-shadow: 0 6px 15px rgba(0, 0, 0, 0.25);
        color: #212529 !important;
    }
    
    /* 탭 내용 구분선 */
    .stTabs [data-baseweb="tab-panel"] {
        background-color: #ffffff;
        border: 2px solid #e9ecef;
        border-radius: 12px;
        padding: 2rem;
        margin-top: 1rem;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
    }
</style>
""", unsafe_allow_html=True)

# 지원되는 파일 형식 정의
SUPPORTED_EXTENSIONS = {
    '.txt': 'text/plain',
    '.md': 'text/markdown',
    '.py': 'text/x-python',
    '.js': 'text/javascript',
    '.html': 'text/html',
    '.css': 'text/css',
    '.json': 'application/json',
    '.csv': 'text/csv',
    '.pdf': 'application/pdf',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.doc': 'application/msword'
}

# 데이터 디렉토리 설정
DATA_DIR = "./data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# ✅ 수정된 세션 상태 안전한 초기화
def init_session_state():
    """세션 상태 변수들을 안전하게 초기화"""
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = {}
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
    
    # ✅ 누락된 변수들 추가
    if 'selected_file_for_chat' not in st.session_state:
        st.session_state.selected_file_for_chat = ""
    if 'current_chat_language' not in st.session_state:
        st.session_state.current_chat_language = "한국어"
    if 'previous_file' not in st.session_state:
        st.session_state.previous_file = ""

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
        # 지원되는 파일 형식 확인
        if not is_supported_file(uploaded_file.name):
            return None, f"지원되지 않는 파일 형식입니다: {get_file_extension(uploaded_file.name)}"
        
        # 중복 방지를 위한 고유 파일명 생성
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
            'name': os.path.basename(file_path),
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime),
            'path': file_path,
            'extension': get_file_extension(file_path)
        }
    except Exception as e:
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
    st.session_state.selected_file_for_chat = ""  # ✅ 추가
    # 기타 채팅 관련 임시 변수들도 정리
    for key in list(st.session_state.keys()):
        if key.startswith('previous_') or key.startswith('current_chat_'):
            del st.session_state[key]

def setup_llama_index():
    """LlamaIndex 설정 (API 키가 있을 때만)"""
    if not st.session_state.openai_api_key:
        return False, "OpenAI API 키가 설정되지 않았습니다."
    
    try:
        # API 키가 있을 때만 import (선택적 import)
        from llama_index.llms.openai import OpenAI
        from llama_index.embeddings.openai import OpenAIEmbedding
        
        os.environ["OPENAI_API_KEY"] = st.session_state.openai_api_key
        
        # LLM 및 임베딩 모델 설정
        Settings.llm = OpenAI(model="gpt-3.5-turbo", temperature=0.1)
        Settings.embed_model = OpenAIEmbedding()
        
        # 텍스트 분할 설정
        Settings.text_splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
        
        return True, "LlamaIndex 설정 완료"
    except ImportError:
        return False, "OpenAI 관련 패키지가 설치되지 않았습니다."
    except Exception as e:
        return False, f"LlamaIndex 설정 중 오류: {str(e)}"

def analyze_documents_basic():
    """기본 문서 분석 (API 키 불필요)"""
    try:
        # 저장된 파일 확인
        files = [f for f in os.listdir(DATA_DIR) if os.path.isfile(os.path.join(DATA_DIR, f))]
        if not files:
            return "분석할 문서가 없습니다. 먼저 파일을 업로드해주세요."
        
        # SimpleDirectoryReader로 문서 로드
        documents = SimpleDirectoryReader(DATA_DIR).load_data()
        
        if not documents:
            return "문서를 읽을 수 없습니다. 지원되는 형식(.txt, .md 등)인지 확인해주세요."
        
        # 문서 기본 정보
        result = f"📁 **기본 분석 결과**\n\n총 {len(documents)} 개의 문서를 분석했습니다.\n\n"
        
        for i, doc in enumerate(documents):
            result += f"**📄 문서 {i+1}:**\n"
            result += f"- 텍스트 길이: {len(doc.text):,} 문자\n"
            if hasattr(doc, 'metadata') and doc.metadata:
                result += f"- 메타데이터: {doc.metadata}\n"
            # 미리보기 (긴 텍스트는 줄임)
            preview = doc.text[:200].replace('\n', ' ')
            result += f"- 미리보기: {preview}...\n\n"
        
        return result
        
    except Exception as e:
        return f"문서 분석 중 오류 발생: {str(e)}"

def analyze_with_vector_index():
    """벡터 인덱스를 사용한 고급 분석 (API 키 필요)"""
    try:
        # LlamaIndex 설정
        setup_success, setup_message = setup_llama_index()
        if not setup_success:
            return f"❌ {setup_message}\n\n💡 사이드바에서 OpenAI API 키를 입력하고 다시 시도해주세요."
        
        # 문서 로드
        documents = SimpleDirectoryReader(DATA_DIR).load_data()
        
        if not documents:
            # 샘플 문서 생성
            doc = Document(text="이것은 생성형 AI 과정입니다. KOSA에서 주관합니다.")
            documents = [doc, Document(text="오늘은 llama_index에 대해서 학습합니다.")]
            st.info("업로드된 파일이 없어 샘플 문서로 분석합니다.")
        
        # 벡터 인덱스 생성
        with st.spinner("벡터 인덱스 생성 중..."):
            index = VectorStoreIndex.from_documents(documents)
        
        # 쿼리 엔진 생성
        query_engine = index.as_query_engine()
        
        # 분석 질문들
        questions = [
            "문서의 주요 내용을 요약해주세요. 한국어로 대답하세요.",
            "이 문서에서 가장 중요한 정보는 무엇인가요? 한국어로 대답하세요.",
            "문서에 언급된 기관이나 조직이 있나요? 한국어로 대답하세요."
        ]
        
        results = []
        for i, question in enumerate(questions):
            try:
                with st.spinner(f"질문 {i+1} 분석 중..."):
                    response = query_engine.query(question)
                results.append(f"**Q{i+1}: {question}**\n\nA: {response}\n\n")
            except Exception as e:
                results.append(f"**Q{i+1}: {question}**\n\nA: 오류 발생: {str(e)}\n\n")
        
        return "🤖 **AI 벡터 분석 결과:**\n\n" + "".join(results)
        
    except Exception as e:
        return f"AI 분석 중 오류 발생: {str(e)}"

def analyze_with_ingestion_pipeline():
    """Ingestion Pipeline을 사용한 분석 (API 키 불필요)"""
    try:
        documents = SimpleDirectoryReader(DATA_DIR).load_data()
        
        if not documents:
            return "분석할 문서가 없습니다. 먼저 파일을 업로드해주세요."
        
        # Ingestion Pipeline 생성
        with st.spinner("Pipeline 처리 중..."):
            pipeline = IngestionPipeline(transformations=[TokenTextSplitter(chunk_size=256)])
            nodes = pipeline.run(documents=documents)
        
        # 결과 정리
        result = f"🔧 **Ingestion Pipeline 분석 결과:**\n\n"
        result += f"- 총 노드 수: {len(nodes)}\n"
        result += f"- 문서 처리 완료: {len(documents)}개\n\n"
        
        result += "**노드 미리보기:**\n\n"
        for i, node in enumerate(nodes[:3]):  # 처음 3개만 표시
            result += f"**📄 노드 {i+1}:**\n"
            result += f"- ID: {node.id_[:20]}...\n"
            result += f"- 텍스트 길이: {len(node.text)} 문자\n"
            preview = node.text[:100].replace('\n', ' ')
            result += f"- 미리보기: {preview}...\n\n"
        
        if len(nodes) > 3:
            result += f"... 외 {len(nodes) - 3}개의 노드가 더 있습니다.\n\n"
        
        return result
        
    except Exception as e:
        return f"Pipeline 분석 중 오류 발생: {str(e)}"

# ✅ 메인 헤더 (최소 크기, 상단 완전 밀착)
st.markdown("""
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            padding: 0.3rem 0.5rem; 
            margin: 0; 
            text-align: center;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            height: 50px;
            display: flex;
            align-items: center;
            justify-content: center;">
    <h4 style="margin: 0; font-size: 1.1rem; font-weight: 600;">🤖 업로드파일기반의 챗봇</h4>
</div>
<div style="height: 60px;"></div>
""", unsafe_allow_html=True)

# ✅ 사이드바 (조건 없이 무조건 표시)
with st.sidebar:
    st.markdown("### ⚙️ 설정")
    
    # OpenAI API 키 입력 (선택사항)
    st.markdown("**OpenAI API 키 (AI 분석용 - 선택사항):**")
    api_key = st.text_input("API 키를 입력하세요", type="password", 
                           value=st.session_state.openai_api_key,
                           help="AI 벡터 분석을 사용하려면 필요합니다")
    if api_key:
        st.session_state.openai_api_key = api_key
        st.success("✅ API 키가 설정되었습니다")
    else:
        st.info("💡 API 키 없이도 기본 분석과 파이프라인 분석이 가능합니다")
    
    st.markdown("---")
    
    # 언어 설정 추가
    st.markdown("### 🌍 언어 설정")
    language_options = {
        "한국어": "한국어로 답변해주세요. 모든 응답은 한국어로 작성하고, 자연스럽고 정확한 한국어 표현을 사용해주세요.",
        "English": "Please respond in English. Use clear and natural English expressions.",
        "中文": "请用中文回答。使用自然流畅的中文表达。",
        "日本語": "日本語で回答してください。自然で正確な日本語表現を使用してください。",
        "Español": "Por favor responde en español. Usa expresiones claras y naturales en español.",
        "Français": "Veuillez répondre en français. Utilisez des expressions françaises claires et naturelles."
    }
    
    selected_language = st.selectbox(
        "채팅 언어를 선택하세요:",
        list(language_options.keys()),
        index=0,  # 기본값: 한국어
        help="AI가 선택한 언어로 답변합니다"
    )
    
    # 언어가 변경되면 채팅 기록 초기화 옵션
    current_language = st.session_state.get('current_language', '한국어')
    if selected_language != current_language:
        st.session_state.current_language = selected_language
        st.warning(f"🌍 언어가 {selected_language}로 변경되었습니다. 새로운 대화를 시작하시겠어요?")
        if st.button("🔄 새 대화 시작", type="secondary"):
            clear_chat_state()
            st.success(f"✅ {selected_language}로 새 대화가 시작되었습니다!")
            st.rerun()
    
    st.markdown("---")
    
    # 지원 파일 형식 안내 - PDF 대형 표시
    st.markdown("### 📄 지원 파일 형식")
    st.markdown("""
    <div style="background: #e7f3ff; border: 2px solid #2196F3; border-radius: 10px; padding: 1rem; margin: 0.5rem 0;">
        <h4 style="color: #1976D2; margin: 0 0 0.5rem 0;">✅ 현재 지원되는 형식:</h4>
        <ul style="margin: 0; padding-left: 1.5rem;">
            <li style="font-size: 16px; font-weight: bold; color: #d32f2f;">📑 <strong>PDF 파일</strong> (.pdf)</li>
            <li style="font-size: 14px; color: #1976D2;">📝 Word 문서 (.docx, .doc)</li>
            <li style="font-size: 14px; color: #1976D2;">📄 텍스트 파일 (.txt, .md)</li>
            <li style="font-size: 14px; color: #1976D2;">💻 코드 파일 (.py, .js, .html, .css)</li>
            <li style="font-size: 14px; color: #1976D2;">📊 데이터 파일 (.json, .csv)</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 통계 정보
    st.markdown("### 📈 통계")
    files = [f for f in os.listdir(DATA_DIR) if os.path.isfile(os.path.join(DATA_DIR, f))]
    st.metric("저장된 파일", len(files))
    
    if files:
        total_size = sum(os.path.getsize(os.path.join(DATA_DIR, f)) for f in files)
        st.metric("총 용량", f"{total_size / 1024:.1f} KB")
    
    # 챗봇 통계
    if st.session_state.get('chat_history', []):
        st.metric("💬 대화 수", len(st.session_state.chat_history))
        selected_file_for_chat = st.session_state.get('selected_file_for_chat', '')
        if selected_file_for_chat:
            st.metric("📄 현재 문서", selected_file_for_chat)

# ✅ 메인 영역 - 탭 구성 (조건 없이 무조건 표시)
tab1, tab2, tab3 = st.tabs(["📤 파일 업로드", "📂 파일 관리", "💬 AI 챗봇"])

# 파일 업로드 탭
with tab1:
    st.markdown("### 📤 파일 업로드")
    
    # 지원 형식 안내
    st.markdown("""
    <div style="background: #e8f5e8; border-left: 5px solid #4caf50; padding: 1rem; margin: 1rem 0; border-radius: 5px;">
        <h4 style="color: #2e7d32; margin: 0;">🎯 <strong>PDF 파일 완벽 지원!</strong></h4>
        <p style="margin: 0.5rem 0; color: #388e3c;">
            📑 PDF, 📝 Word, 📄 텍스트, 💻 코드, 📊 데이터 파일 모두 업로드 가능
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 파일 업로드
    uploaded_files = st.file_uploader(
        "파일을 선택하거나 드래그해서 업로드하세요",
        accept_multiple_files=True,
        help="여러 파일을 동시에 업로드할 수 있습니다"
    )
    
    if uploaded_files:
        st.markdown("#### 📋 업로드된 파일 목록")
        
        for uploaded_file in uploaded_files:
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.write(f"📄 **{uploaded_file.name}**")
                st.write(f"📊 크기: {uploaded_file.size / 1024:.1f} KB")
            
            with col2:
                ext = get_file_extension(uploaded_file.name)
                if is_supported_file(uploaded_file.name):
                    st.success(f"✅ {ext}")
                else:
                    st.error(f"❌ {ext}")
            
            with col3:
                if st.button(f"💾 저장", key=f"save_{uploaded_file.name}"):
                    file_path, message = save_uploaded_file(uploaded_file)
                    if file_path:
                        st.success("✅ 저장 완료!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(message)

# 파일 관리 탭
with tab2:
    st.markdown("### 📂 파일 관리")
    
    # 저장된 파일 목록
    files = [f for f in os.listdir(DATA_DIR) if os.path.isfile(os.path.join(DATA_DIR, f))]
    
    if not files:
        st.info("💡 저장된 파일이 없습니다. '파일 업로드' 탭에서 파일을 업로드해주세요.")
    else:
        # 컨트롤 버튼들
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("🗑️ 모든 파일 삭제", type="secondary"):
                for file in files:
                    delete_file(os.path.join(DATA_DIR, file))
                st.success("🎉 모든 파일이 삭제되었습니다!")
                st.rerun()
        
        st.markdown("#### 📋 저장된 파일 목록")
        
        # 파일 목록을 카드 형태로 표시
        for i, file in enumerate(files):
            file_path = os.path.join(DATA_DIR, file)
            file_info = get_file_info(file_path)
            
            if file_info:
                with st.container():
                    st.markdown(f"""
                    <div class="file-card">
                        <h4>📄 {file_info['name']}</h4>
                        <p><strong>📊 크기:</strong> {file_info['size'] / 1024:.1f} KB</p>
                        <p><strong>🏷️ 형식:</strong> {file_info['extension']}</p>
                        <p><strong>📅 수정일:</strong> {file_info['modified'].strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        if st.button(f"🗑️ 삭제", key=f"delete_{file}", type="secondary"):
                            if delete_file(file_path):
                                st.success(f"✅ {file} 삭제 완료!")
                                st.rerun()

# AI 챗봇 탭
with tab3:
    st.markdown("### 💬 AI 챗봇")
    
    # 파일 선택
    files = [f for f in os.listdir(DATA_DIR) if os.path.isfile(os.path.join(DATA_DIR, f))]
    
    if not files:
        st.warning("⚠️ 먼저 파일을 업로드해주세요.")
        st.info("💡 '파일 업로드' 탭에서 PDF, Word, 텍스트 파일 등을 업로드하세요.")
    else:
        # 파일 선택 UI
        col1, col2 = st.columns([3, 1])
        
        with col1:
            selected_file = st.selectbox(
                "📄 대화할 문서를 선택하세요:",
                files,
                key="chat_file_selector"
            )
        
        with col2:
            if st.button("🗑️ 채팅 초기화", type="secondary"):
                clear_chat_state()
                st.success("채팅 기록이 초기화되었습니다!")
                st.rerun()
        
        # 선택된 파일이나 언어가 변경되었을 때 처리
        if (selected_file != st.session_state.selected_file_for_chat or 
            selected_language != st.session_state.get('current_chat_language', selected_language)):
            
            st.session_state.selected_file_for_chat = selected_file
            st.session_state.current_chat_language = selected_language
            st.session_state.query_engine = None  # 언어나 파일 변경 시 엔진 재생성
            
            if selected_file != st.session_state.get('previous_file', ''):
                st.session_state.chat_history = []  # 파일 변경 시에만 히스토리 초기화
                st.info(f"📄 **{selected_file}**에 대한 새로운 대화를 시작합니다.")
                st.session_state.previous_file = selected_file
        
        # OpenAI API 키 확인
        if not st.session_state.openai_api_key:
            st.warning("⚠️ AI 챗봇을 사용하려면 사이드바에서 OpenAI API 키를 입력해주세요.")
        else:
            # 쿼리 엔진 초기화 (한 번만)
            if st.session_state.query_engine is None:
                try:
                    with st.spinner(f"📄 {selected_file} 분석 중..."):
                        # LlamaIndex 설정
                        setup_success, setup_message = setup_llama_index()
                        if setup_success:
                            # 문서 로드
                            file_path = os.path.join(DATA_DIR, selected_file)
                            documents = SimpleDirectoryReader(input_files=[file_path]).load_data()
                            
                            if documents:
                                # 벡터 인덱스 생성
                                index = VectorStoreIndex.from_documents(documents)
                                
                                # 언어별 강화된 시스템 프롬프트 설정
                                language_instructions = {
                                    "한국어": "반드시 한국어로만 답변하세요. 자연스럽고 정확한 한국어를 사용하고, 문어체로 답변해주세요. 영어나 다른 언어는 절대 사용하지 마세요.",
                                    "English": "You must respond only in English. Use clear, natural, and accurate English expressions. Do not use Korean or any other language.",
                                    "中文": "你必须只用中文回答。使用清晰、自然、准确的中文表达。不要使用韩语或任何其他语言。",
                                    "日本語": "日本語のみで回答してください。明確で自然な日本語表現を使用してください。韓国語や他の言語は使用しないでください。",
                                    "Español": "Debes responder solo en español. Usa expresiones claras, naturales y precisas en español. No uses coreano ni ningún otro idioma.",
                                    "Français": "Vous devez répondre uniquement en français. Utilisez des expressions françaises claires, naturelles et précises. N'utilisez pas le coréen ou toute autre langue."
                                }
                                
                                language_instruction = language_instructions.get(selected_language, language_instructions["한국어"])
                                
                                # 강화된 프롬프트 템플릿
                                qa_template = PromptTemplate(
                                    "Context information is below.\n"
                                    "---------------------\n"
                                    "{context_str}\n"
                                    "---------------------\n"
                                    f"IMPORTANT LANGUAGE INSTRUCTION: {language_instruction}\n"
                                    "Based on the context information above and following the language instruction strictly, "
                                    "answer the following question: {query_str}\n"
                                    "Remember: Your entire response must be in the specified language only.\n"
                                    "Answer: "
                                )
                                
                                st.session_state.query_engine = index.as_query_engine(
                                    text_qa_template=qa_template
                                )
                                st.success(f"✅ {selected_file} 분석 완료! 이제 {selected_language}로 대화하세요.")
                            else:
                                st.error("문서를 읽을 수 없습니다. 파일 형식을 확인해주세요.")
                        else:
                            st.error(f"설정 오류: {setup_message}")
                except Exception as e:
                    st.error(f"문서 로드 중 오류: {str(e)}")
            
            # 챗봇 인터페이스
            if st.session_state.query_engine is not None:
                # 채팅 히스토리 표시
                st.markdown("#### 💬 대화 기록")
                
                # 채팅 컨테이너 (스크롤 가능)
                chat_container = st.container()
                
                with chat_container:
                    chat_history = st.session_state.get('chat_history', [])
                    if not chat_history:
                        # 언어별 환영 메시지
                        welcome_messages = {
                            "한국어": {
                                "title": "🤖 안녕하세요!",
                                "content": f"**{selected_file}**에 대해 무엇이든 물어보세요.<br>예: \"이 문서의 주요 내용은?\", \"핵심 포인트는?\", \"요약해줘\""
                            },
                            "English": {
                                "title": "🤖 Hello!",
                                "content": f"Ask me anything about **{selected_file}**.<br>Examples: \"What's the main content?\", \"Key points?\", \"Summarize this\""
                            },
                            "中文": {
                                "title": "🤖 您好！",
                                "content": f"请随时询问关于**{selected_file}**的任何问题。<br>例如：\"主要内容是什么？\"、\"关键点？\"、\"总结一下\""
                            },
                            "日本語": {
                                "title": "🤖 こんにちは！",
                                "content": f"**{selected_file}**について何でも質問してください。<br>例：\"主な内容は？\"、\"重要なポイントは？\"、\"要約して\""
                            },
                            "Español": {
                                "title": "🤖 ¡Hola!",
                                "content": f"Pregúntame lo que quieras sobre **{selected_file}**.<br>Ejemplos: \"¿Cuál es el contenido principal?\", \"¿Puntos clave?\", \"Resúmelo\""
                            },
                            "Français": {
                                "title": "🤖 Bonjour !",
                                "content": f"Demandez-moi tout ce que vous voulez sur **{selected_file}**.<br>Exemples: \"Quel est le contenu principal ?\", \"Points clés ?\", \"Résumez\""
                            }
                        }
                        
                        message = welcome_messages.get(selected_language, welcome_messages["한국어"])
                        
                        st.markdown(f"""
                        <div style="background: #f0f8ff; border: 2px dashed #4a90e2; border-radius: 10px; padding: 1.5rem; text-align: center; margin: 1rem 0;">
                            <h4 style="color: #4a90e2; margin: 0;">{message['title']}</h4>
                            <p style="margin: 0.5rem 0; color: #666;">
                                {message['content']}
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # 채팅 기록 표시
                    for i, chat in enumerate(chat_history):
                        # 사용자 메시지
                        st.markdown(f"""
                        <div style="background: #e3f2fd; border-left: 4px solid #2196f3; padding: 1rem; margin: 0.5rem 0; border-radius: 0 10px 10px 0;">
                            <strong>👤 You:</strong><br>{chat['user']}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # AI 응답
                        st.markdown(f"""
                        <div style="background: #f1f8e9; border-left: 4px solid #4caf50; padding: 1rem; margin: 0.5rem 0; border-radius: 0 10px 10px 0;">
                            <strong>🤖 AI:</strong><br>{chat['ai']}
                        </div>
                        """, unsafe_allow_html=True)
                
                # 메시지 입력
                st.markdown("#### ✍️ 메시지 입력")
                
                col1, col2 = st.columns([4, 1])
                
                # 언어별 placeholder
                placeholders = {
                    "한국어": "예: 이 문서의 핵심 내용은 무엇인가요?",
                    "English": "e.g., What are the key points of this document?",
                    "中文": "例如：这个文档的核心内容是什么？",
                    "日本語": "例：この文書の重要な内容は何ですか？",
                    "Español": "ej: ¿Cuáles son los puntos clave de este documento?",
                    "Français": "ex: Quels sont les points clés de ce document ?"
                }
                
                with col1:
                    user_input = st.text_input(
                        "메시지를 입력하세요:" if selected_language == "한국어" else "Enter your message:",
                        placeholder=placeholders.get(selected_language, placeholders["한국어"]),
                        key="chat_input"
                    )
                
                with col2:
                    send_labels = {
                        "한국어": "📤 전송",
                        "English": "📤 Send", 
                        "中文": "📤 发送",
                        "日本語": "📤 送信",
                        "Español": "📤 Enviar",
                        "Français": "📤 Envoyer"
                    }
                    send_button = st.button(
                        send_labels.get(selected_language, "📤 전송"), 
                        type="primary", 
                        use_container_width=True
                    )
                
                # 빠른 질문 버튼들 (언어별)
                quick_question_titles = {
                    "한국어": "#### 💡 빠른 질문",
                    "English": "#### 💡 Quick Questions",
                    "中文": "#### 💡 快速提问", 
                    "日本語": "#### 💡 クイック質問",
                    "Español": "#### 💡 Preguntas Rápidas",
                    "Français": "#### 💡 Questions Rapides"
                }
                
                st.markdown(quick_question_titles.get(selected_language, "#### 💡 빠른 질문"))
                
                quick_questions_by_lang = {
                    "한국어": ["📋 요약해줘", "🔍 핵심 포인트는?", "❓ 주요 내용은?", "💡 중요한 점은?"],
                    "English": ["📋 Summarize", "🔍 Key points?", "❓ Main content?", "💡 Important parts?"],
                    "中文": ["📋 总结一下", "🔍 关键点？", "❓ 主要内容？", "💡 重要部分？"],
                    "日本語": ["📋 要約して", "🔍 重要ポイント？", "❓ 主な内容？", "💡 大切な点？"],
                    "Español": ["📋 Resumir", "🔍 Puntos clave?", "❓ Contenido principal?", "💡 Partes importantes?"],
                    "Français": ["📋 Résumer", "🔍 Points clés?", "❓ Contenu principal?", "💡 Points importants?"]
                }
                
                quick_questions = quick_questions_by_lang.get(selected_language, quick_questions_by_lang["한국어"])
                
                col1, col2, col3, col4 = st.columns(4)
                
                for i, (col, question) in enumerate(zip([col1, col2, col3, col4], quick_questions)):
                    with col:
                        if st.button(question, key=f"quick_{i}_{selected_language}", use_container_width=True):
                            # 이모지 제거하고 실제 질문으로 변환
                            actual_questions = {
                                "한국어": [
                                    "문서를 요약해주세요",
                                    "핵심 포인트는 무엇인가요?",
                                    "주요 내용은 무엇인가요?",
                                    "가장 중요한 점은 무엇인가요?"
                                ],
                                "English": [
                                    "Please summarize this document",
                                    "What are the key points?",
                                    "What is the main content?",
                                    "What are the most important parts?"
                                ],
                                "中文": [
                                    "请总结这个文档",
                                    "关键点是什么？",
                                    "主要内容是什么？",
                                    "最重要的部分是什么？"
                                ],
                                "日本語": [
                                    "この文書を要約してください",
                                    "重要なポイントは何ですか？",
                                    "主な内容は何ですか？",
                                    "最も大切な点は何ですか？"
                                ],
                                "Español": [
                                    "Por favor resume este documento",
                                    "¿Cuáles son los puntos clave?",
                                    "¿Cuál es el contenido principal?",
                                    "¿Cuáles son las partes más importantes?"
                                ],
                                "Français": [
                                    "Veuillez résumer ce document",
                                    "Quels sont les points clés?",
                                    "Quel est le contenu principal?",
                                    "Quelles sont les parties les plus importantes?"
                                ]
                            }
                            
                            actual_question_list = actual_questions.get(selected_language, actual_questions["한국어"])
                            user_input = actual_question_list[i]
                            
                            # 즉시 처리
                            with st.spinner("🤖 AI가 답변을 생성하고 있습니다..."):
                                try:
                                    # AI 응답 생성
                                    response = st.session_state.query_engine.query(user_input)
                                    
                                    # 채팅 히스토리에 추가
                                    if 'chat_history' not in st.session_state:
                                        st.session_state.chat_history = []
                                    st.session_state.chat_history.append({
                                        'user': user_input,
                                        'ai': str(response),
                                        'timestamp': datetime.now().strftime('%H:%M:%S')
                                    })
                                    
                                    # 즉시 리프레시
                                    st.rerun()
                                    
                                except Exception as e:
                                    st.error(f"답변 생성 중 오류가 발생했습니다: {str(e)}")
                
                # 메시지 처리 (중복 방지 개선)
                if send_button and user_input.strip():
                    with st.spinner("🤖 AI가 답변을 생성하고 있습니다..."):
                        try:
                            # AI 응답 생성
                            response = st.session_state.query_engine.query(user_input.strip())
                            
                            # 중복 방지: 이미 같은 질문이 있는지 확인
                            chat_history = st.session_state.get('chat_history', [])
                            is_duplicate = False
                            if chat_history:
                                last_chat = chat_history[-1]
                                if last_chat['user'] == user_input.strip():
                                    is_duplicate = True
                            
                            if not is_duplicate:
                                # 채팅 히스토리에 추가
                                if 'chat_history' not in st.session_state:
                                    st.session_state.chat_history = []
                                st.session_state.chat_history.append({
                                    'user': user_input.strip(),
                                    'ai': str(response),
                                    'timestamp': datetime.now().strftime('%H:%M:%S')
                                })
                            
                            # 입력창 초기화를 위해 rerun
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"답변 생성 중 오류가 발생했습니다: {str(e)}")
                
                # 채팅 통계
                chat_history = st.session_state.get('chat_history', [])
                if chat_history:
                    st.markdown("---")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("💬 대화 수", len(chat_history))
                    with col2:
                        st.metric("📄 문서", selected_file)
                    with col3:
                        if chat_history:
                            last_time = chat_history[-1]['timestamp']
                            st.metric("🕐 최근 대화", last_time)

# 푸터
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; margin-top: 2rem; padding: 1rem;">
    <p>🤖 <strong>업로드파일기반의 챗봇</strong> v2.1 (PDF 지원 버전)</p>
    <p>📚 llama_index + Streamlit으로 구현</p>
    <p><small>💡 <code>streamlit run app.py</code> 명령어로 실행하세요</small></p>
</div>
""", unsafe_allow_html=True)