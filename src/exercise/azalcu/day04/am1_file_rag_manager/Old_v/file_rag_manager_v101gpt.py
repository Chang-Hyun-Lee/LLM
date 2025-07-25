import streamlit as st
from pathlib import Path
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.settings import Settings
import os

# -------------------------------
# 1. 앱 설정 (제목 공간 최소화)
# -------------------------------
st.set_page_config(page_title="업로드 파일 기반 챗봇", layout="wide")

st.markdown(
    """
    <div style="padding: 0rem 0 0.2rem 0;">
        <h1 style='font-size: 2.2rem; margin-bottom: 0;'>📄 업로드 파일 기반 챗봇</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# -------------------------------
# 2. 사이드바: OpenAI API 키 + 파일 업로드
# -------------------------------
st.sidebar.header("설정")
openai_api_key = st.sidebar.text_input("🔑 OpenAI API Key:", type="password")
st.sidebar.caption("지원 형식: PDF")

if not openai_api_key:
    st.sidebar.warning("API 키를 입력하세요.")
    st.stop()

Settings.llm = OpenAI(api_key=openai_api_key, model="gpt-3.5-turbo")
Settings.embed_model = OpenAIEmbedding(api_key=openai_api_key)

# -------------------------------
# 3. 파일 업로드 및 인덱싱
# -------------------------------
UPLOAD_DIR = Path("uploaded_files")
INDEX_DIR = Path("indexes")
UPLOAD_DIR.mkdir(exist_ok=True)
INDEX_DIR.mkdir(exist_ok=True)

uploaded_files = st.sidebar.file_uploader("📂 PDF 업로드", type="pdf", accept_multiple_files=True)

if uploaded_files:
    for file in uploaded_files:
        save_path = UPLOAD_DIR / file.name
        with open(save_path, "wb") as f:
            f.write(file.getbuffer())

        docs = SimpleDirectoryReader(input_files=[str(save_path)]).load_data()
        index = VectorStoreIndex.from_documents(docs)
        index.storage_context.persist(persist_dir=str(INDEX_DIR / file.name))

    st.sidebar.success("✅ 업로드 및 인덱싱 완료!")

# -------------------------------
# 4. 탭 UI (크기 키운 탭 제목)
# -------------------------------
tab1, tab2, tab3 = st.tabs([
    "📁 <span style='font-size:1.2rem'>파일 업로드</span>",
    "🗂️ <span style='font-size:1.2rem'>파일 관리</span>",
    "🔍 <span style='font-size:1.2rem'>문서 분석</span>"
])

with tab1:
    st.write("좌측 사이드바를 통해 PDF 파일을 업로드하고 인덱싱할 수 있습니다.")

with tab2:
    indexed_files = [f.name for f in UPLOAD_DIR.glob("*.pdf")]
    if indexed_files:
        st.markdown("#### 🔖 업로드된 파일 목록")
        for f in indexed_files:
            st.write(f"📄 {f}")
    else:
        st.info("아직 업로드된 파일이 없습니다.")

with tab3:
    indexed_files = [f.name for f in UPLOAD_DIR.glob("*.pdf")]
    if not indexed_files:
        st.warning("먼저 PDF 파일을 업로드하고 인덱싱하세요.")
        st.stop()

    selected_file = st.selectbox("📑 질문할 PDF 선택:", indexed_files)
    index_path = INDEX_DIR / selected_file

    storage_context = StorageContext.from_defaults(persist_dir=str(index_path))
    index = load_index_from_storage(storage_context)
    query_engine = index.as_query_engine()

    question = st.text_input("❓ 문서에 대해 궁금한 점을 입력하세요:")

    if question:
        with st.spinner("답변 생성 중..."):
            response = query_engine.query(question)
            st.markdown("### 🧠 답변")
            st.write(str(response))
