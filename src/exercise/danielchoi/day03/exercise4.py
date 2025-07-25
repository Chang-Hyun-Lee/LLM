import os
import streamlit as st
import docx2txt
import tempfile
from pathlib import Path
import PyPDF2  # Changed from fitz to PyPDF2

from llama_index.core import VectorStoreIndex, Settings, Document
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SentenceSplitter

# OpenAI API 키 설정
os.environ["OPENAI_API_KEY"] = "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"

# llama_index 기본 설정
Settings.llm = OpenAI(model="gpt-4o-mini")
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=20)

# 파일 저장 디렉토리
UPLOAD_DIR = "uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

st.title("📚 문서 요약 앱 - 파일 업로드, 목록 및 삭제")

# --- 파일 업로드 섹션 ---
uploaded_file = st.file_uploader("📤 문서를 업로드하세요 (.txt, .pdf, .docx)", type=["txt", "pdf", "docx"])

if uploaded_file:
    file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())
    st.success(f"✅ '{uploaded_file.name}' 업로드 완료!")

# --- 업로드된 파일 목록 표시 및 삭제 ---
st.subheader("📁 업로드된 문서 목록")

files = os.listdir(UPLOAD_DIR)

if files:
    selected_file = st.selectbox("요약할 파일을 선택하세요", files)

    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("📄 이 파일 요약하기"):
            def load_file_text(file_path):
                mime_type = Path(file_path).suffix.lower()
                if mime_type == ".txt":
                    with open(file_path, "r", encoding="utf-8") as f:
                        return f.read()
                elif mime_type == ".pdf":
                    text = ""
                    with open(file_path, 'rb') as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                        for page in pdf_reader.pages:
                            text += page.extract_text()
                    return text
                elif mime_type == ".docx":
                    return docx2txt.process(file_path)
                return None

            file_text = load_file_text(os.path.join(UPLOAD_DIR, selected_file))
            if file_text:
                with st.spinner("요약 중..."):
                    document = Document(text=file_text)
                    index = VectorStoreIndex.from_documents([document])
                    query_engine = index.as_query_engine(response_mode="tree_summarize")
                    response = query_engine.query("이 문서를 전체적으로 요약해줘.")
                    st.markdown("### 📌 요약 결과")
                    st.write(response.response)
            else:
                st.error("파일을 읽을 수 없습니다.")

    with col2:
        if st.button("🗑️ 파일 삭제"):
            os.remove(os.path.join(UPLOAD_DIR, selected_file))
            st.warning(f"'{selected_file}' 파일이 삭제되었습니다.")
            st.experimental_rerun()
else:
    st.info("현재 업로드된 문서가 없습니다.")
