import streamlit as st
from pathlib import Path
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.settings import Settings
import os

# 디버깅 로그 추가
print("Starting Streamlit app...")

# 페이지 설정
st.set_page_config(page_title="업로드 파일 기반 챗봇", layout="wide")

# 간단한 CSS 스타일링: 제목 높이 10% 수준, 상단에 바짝 붙임
st.markdown("""
<style>
    .main-header {
        padding: 0.5rem 0 0.5rem 0;
        margin: 0;
        text-align: left;
    }
    .main-header h1 {
        font-size: 2rem;
        margin: 0;
    }
    .stTabs [role="tab"] {
        font-size: 1.5rem !important;
        padding: 0.8rem 1.2rem;
    }
    .stTabs [role="tablist"] {
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# 메인 제목: 높이 최소화, 상단에 붙임
st.markdown("""
<div class="main-header">
    <h1>📄 업로드 파일 기반 챗봇</h1>
</div>
""", unsafe_allow_html=True)

# 사이드바: 설정
st.sidebar.header("⚙️ 설정")

# OpenAI API 키 입력
openai_api_key = st.sidebar.text_input("🔑 OpenAI API Key:", type="password", help="gpt-3.5-turbo 모델을 사용합니다")
if not openai_api_key:
    st.sidebar.error("⚠️ API 키를 입력하세요.")
    st.stop()

# LlamaIndex 설정
Settings.llm = OpenAI(api_key=openai_api_key, model="gpt-3.5-turbo")
Settings.embed_model = OpenAIEmbedding(api_key=openai_api_key)

# 지원 파일 형식 명시
st.sidebar.markdown("### 📄 지원 파일 형식")
st.sidebar.write("• `.pdf` - PDF 문서")
st.sidebar.caption("PDF 파일만 업로드 가능합니다.")

# 파일 업로드
uploaded_files = st.sidebar.file_uploader("📂 PDF 업로드", type="pdf", accept_multiple_files=True, help="PDF 파일을 선택하거나 드래그하여 업로드하세요")

# 디렉토리 설정
UPLOAD_DIR = Path("uploaded_files")
INDEX_DIR = Path("indexes")
UPLOAD_DIR.mkdir(exist_ok=True)
INDEX_DIR.mkdir(exist_ok=True)

# 파일 업로드 및 인덱싱
if uploaded_files:
    for file in uploaded_files:
        save_path = UPLOAD_DIR / file.name
        print(f"Saving file: {save_path}")
        with open(save_path, "wb") as f:
            f.write(file.getbuffer())
        with st.spinner(f"{file.name} 인덱싱 중..."):
            docs = SimpleDirectoryReader(input_files=[str(save_path)]).load_data()
            index = VectorStoreIndex.from_documents(docs)
            index.storage_context.persist(persist_dir=str(INDEX_DIR / file.name))
    st.sidebar.success("✅ 업로드 및 인덱싱 완료!")

# 탭 UI: 탭 제목 크기 키움
tab1, tab2, tab3 = st.tabs([
    "📁 <span style='font-size:1.5rem'>파일 업로드</span>",
    "🗂️ <span style='font-size:1.5rem'>파일 관리</span>",
    "🔍 <span style='font-size:1.5rem'>문서 분석</span>"
])

# 파일 업로드 탭
with tab1:
    st.markdown("### 📤 파일 업로드")
    st.info("🔹 좌측 사이드바를 통해 PDF 파일을 업로드하고 인덱싱할 수 있습니다.")
    if uploaded_files:
        st.markdown("#### 📋 업로드된 파일")
        for file in uploaded_files:
            st.write(f"📄 {file.name} ({file.size / 1024:.1f} KB)")

# 파일 관리 탭
with tab2:
    st.markdown("### 🗂️ 파일 관리")
    indexed_files = [f.name for f in UPLOAD_DIR.glob("*.pdf")]
    if indexed_files:
        st.markdown("#### 🔖 업로드된 파일 목록")
        for f in indexed_files:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"📄 {f}")
            with col2:
                if st.button("🗑️ 삭제", key=f"delete_{f}"):
                    (UPLOAD_DIR / f).unlink(missing_ok=True)
                    (INDEX_DIR / f).rmdir()
                    st.success(f"✅ {f} 삭제 완료!")
                    st.rerun()
    else:
        st.info("💡 아직 업로드된 파일이 없습니다.")

# 문서 분석 탭
with tab3:
    st.markdown("### 🔍 문서 분석")
    indexed_files = [f.name for f in UPLOAD_DIR.glob("*.pdf")]
    if not indexed_files:
        st.warning("⚠️ 먼저 PDF 파일을 업로드하고 인덱싱하세요.")
    else:
        selected_file = st.selectbox("📑 질문할 PDF 선택:", indexed_files, help="분석할 PDF 파일을 선택하세요")
        index_path = INDEX_DIR / selected_file
        if index_path.exists():
            with st.spinner("인덱스 로드 중..."):
                storage_context = StorageContext.from_defaults(persist_dir=str(index_path))
                index = load_index_from_storage(storage_context)
                query_engine = index.as_query_engine()
            question = st.text_input("❓ 문서에 대해 궁금한 점을 입력하세요:", help="문서 내용을 기반으로 질문하세요")
            if question:
                with st.spinner("답변 생성 중..."):
                    try:
                        response = query_engine.query(question)
                        st.markdown("### 🧠 답변")
                        st.write(str(response))
                    except Exception as e:
                        st.error(f"분석 중 오류 발생: {str(e)}")
        else:
            st.error(f"선택한 파일 {selected_file}의 인덱스가 없습니다.")

# 푸터
st.markdown("""
<div style="text-align: center; color: #666; margin-top: 1rem; padding: 0.5rem;">
    <p>🤖 <strong>업로드 파일 기반 챗봇</strong> v1.0</p>
    <p>📚 llama_index + Streamlit으로 구현 | 🎯 Python 학습용 프로젝트</p>
</div>
""", unsafe_allow_html=True)