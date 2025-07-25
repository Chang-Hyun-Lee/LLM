import streamlit as st
import os
from datetime import datetime
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.core.schema import Document
from llama_index.core.node_parser import SentenceSplitter, TokenTextSplitter
from llama_index.core.ingestion import IngestionPipeline

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
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.8rem 1rem;
        border-radius: 10px;
        margin: 0.5rem 0 1rem 0;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        position: sticky;
        top: 0;
        z-index: 100;
    }
    
    .main-header h1 {
        margin: 0.3rem 0;
        font-size: 1.8rem;
        font-weight: 600;
    }
    
    .main-header p {
        margin: 0.2rem 0;
        font-size: 0.9rem;
        opacity: 0.9;
    }
    
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
    
    /* 탭 가시성 대폭 개선 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1rem;
        border-radius: 15px;
        border: 3px solid #dee2e6;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 70px;
        padding: 1.2rem 2.5rem;
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border-radius: 12px;
        font-size: 18px;
        font-weight: 700;
        border: 3px solid #6c757d;
        transition: all 0.3s ease;
        color: #495057 !important;
        box-shadow: 0 3px 6px rgba(0, 0, 0, 0.15);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: 3px solid #667eea !important;
        box-shadow: 0 6px 15px rgba(102, 126, 234, 0.4) !important;
        transform: translateY(-3px);
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%);
        border-color: #495057;
        transform: translateY(-2px);
        box-shadow: 0 5px 12px rgba(0, 0, 0, 0.2);
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

# 세션 상태 초기화
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = {}
if 'openai_api_key' not in st.session_state:
    st.session_state.openai_api_key = ""

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

# ✅ 메인 헤더 (조건 없이 무조건 표시)
st.markdown("""
<div class="main-header">
    <h1>🤖 업로드파일기반의 챗봇</h1>
    <p>llama_index와 Streamlit으로 만든 지능형 문서 관리 시스템</p>
</div>
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
    
    # 지원 파일 형식 안내
    st.markdown("### 📄 지원 파일 형식")
    with st.expander("지원되는 형식 보기"):
        for ext, desc in SUPPORTED_EXTENSIONS.items():
            st.write(f"• `{ext}` - {desc}")
    
    st.markdown("---")
    
    # 분석 모드 선택
    st.markdown("### 📊 분석 모드")
    analysis_mode = st.selectbox(
        "분석 방법을 선택하세요",
        ["기본 분석", "AI 벡터 분석", "Pipeline 분석"],
        help="기본 분석: 파일 정보만, AI 벡터 분석: OpenAI API 필요, Pipeline 분석: 고급 텍스트 처리"
    )
    
    st.markdown("---")
    
    # 통계 정보
    st.markdown("### 📈 통계")
    files = [f for f in os.listdir(DATA_DIR) if os.path.isfile(os.path.join(DATA_DIR, f))]
    st.metric("저장된 파일", len(files))
    
    if files:
        total_size = sum(os.path.getsize(os.path.join(DATA_DIR, f)) for f in files)
        st.metric("총 용량", f"{total_size / 1024:.1f} KB")

# ✅ 메인 영역 - 탭 구성 (조건 없이 무조건 표시)
st.write("✅ 탭 생성 테스트")
tab1, tab2, tab3 = st.tabs(["📤 파일 업로드", "📂 파일 관리", "🔍 문서 분석"])

# 파일 업로드 탭
with tab1:
    st.markdown("### 📤 파일 업로드")
    st.write("✅ 파일 업로드 탭이 정상 표시되었습니다!")
    
    # 지원 형식 안내
    st.info("🔹 **현재 지원되는 파일 형식:** .txt, .md, .py, .js, .html, .css, .json, .csv, .pdf, .docx, .doc")
    
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
    st.write("✅ 파일 관리 탭이 정상 표시되었습니다!")
    
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

# 문서 분석 탭
with tab3:
    st.markdown("### 🔍 문서 분석")
    st.write("✅ 문서 분석 탭이 정상 표시되었습니다!")
    
    # 분석 모드 정보 표시
    if analysis_mode == "기본 분석":
        st.info("🔹 **기본 분석:** 업로드된 파일의 기본 정보와 내용을 분석합니다. (API 키 불필요)")
    elif analysis_mode == "AI 벡터 분석":
        st.info("🔹 **AI 벡터 분석:** OpenAI API를 사용하여 문서 내용을 지능적으로 분석합니다.")
        if not st.session_state.openai_api_key:
            st.warning("⚠️ AI 분석을 위해서는 사이드바에서 OpenAI API 키를 입력해주세요.")
    else:  # Pipeline 분석
        st.info("🔹 **Pipeline 분석:** 고급 텍스트 처리 파이프라인을 사용하여 문서를 세밀하게 분석합니다. (API 키 불필요)")
    
    # ✅ 분석 버튼은 조건 없이 무조건 표시
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if st.button("🚀 분석 시작", type="primary"):
            
            # 분석 실행
            if analysis_mode == "기본 분석":
                result = analyze_documents_basic()
            elif analysis_mode == "AI 벡터 분석":
                result = analyze_with_vector_index()
            else:  # Pipeline 분석
                result = analyze_with_ingestion_pipeline()
            
            # 결과 저장
            st.session_state.analysis_results[analysis_mode] = result
            st.success(f"✅ {analysis_mode} 완료!")
    
    # 분석 결과 표시
    if analysis_mode in st.session_state.analysis_results:
        st.markdown("#### 📊 분석 결과")
        
        # 결과를 expandable 컨테이너에 표시
        with st.expander(f"🔍 {analysis_mode} 결과 보기", expanded=True):
            st.markdown(st.session_state.analysis_results[analysis_mode])
        
        # 결과 다운로드 버튼
        result_text = st.session_state.analysis_results[analysis_mode]
        st.download_button(
            label="📥 분석 결과 다운로드",
            data=result_text,
            file_name=f"analysis_result_{analysis_mode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )

# 푸터
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; margin-top: 2rem; padding: 1rem;">
    <p>🤖 <strong>업로드파일기반의 챗봇</strong> v2.1 (PDF 지원 버전)</p>
    <p>📚 llama_index + Streamlit으로 구현</p>
    <p><small>💡 <code>streamlit run app.py</code> 명령어로 실행하세요</small></p>
</div>
""", unsafe_allow_html=True)

st.write("✅ 페이지 맨 끝까지 정상 렌더링 완료!")