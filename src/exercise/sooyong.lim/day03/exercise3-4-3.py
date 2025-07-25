import os
import streamlit as st
from llama_index.core import VectorStoreIndex, Settings, Document
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SentenceSplitter

from io import StringIO
import docx2txt
import tempfile

# OpenAI API 키
import openai
openai.api_key = os.getenv("OPENAI_API_KEY")

# LlamaIndex 설정
Settings.llm = OpenAI(temperature=0, model="gpt-4o-mini")
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=20)

st.title("📄 업로드한 문서 전체 요약")

# 파일 업로드
uploaded_file = st.file_uploader("문서를 업로드하세요 (.txt, .pdf, .docx)", type=["txt", "pdf", "docx"])

def load_file_text(uploaded_file):
    if uploaded_file.type == "text/plain":
        stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
        return stringio.read()
    elif uploaded_file.type == "application/pdf":
        import fitz  # PyMuPDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name
        text = ""
        with fitz.open(tmp_path) as doc:
            for page in doc:
                text += page.get_text()
        return text
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name
        return docx2txt.process(tmp_path)
    else:
        return None

if uploaded_file is not None:
    file_text = load_file_text(uploaded_file)

    if file_text:
        st.success("파일을 성공적으로 불러왔습니다.")

        # LlamaIndex 문서로 변환
        document = Document(text=file_text)

        # 인덱싱 및 요약
        index = VectorStoreIndex.from_documents([document])
        query_engine = index.as_query_engine(response_mode="tree_summarize")

        with st.spinner("요약 생성 중..."):
            response = query_engine.query("이 문서를 전체적으로 요약해줘.")
            st.subheader("📌 문서 요약")
            st.write(response.response)
    else:
        st.error("파일 내용을 불러올 수 없습니다.")
