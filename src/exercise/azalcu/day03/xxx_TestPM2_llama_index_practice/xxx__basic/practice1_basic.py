# basic/practice1_basic.py

import streamlit as st
from pathlib import Path
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

# Streamlit 페이지 설정
st.set_page_config(page_title="📚 기초: 문서 QA", page_icon="📖")

st.title("📚 기초: 문서 기반 Q&A")
st.markdown("업로드된 문서를 기반으로 자연어 질문에 답변합니다.")

# ✅ OpenAI API 키 입력
api_key = st.text_input("🔑 OpenAI API Key", type="password", help="https://platform.openai.com/account/api-keys 에서 키를 발급받을 수 있습니다.")

if not api_key:
    st.warning("먼저 OpenAI API 키를 입력해주세요.")
    st.stop()

# ✅ LlamaIndex 설정
try:
    Settings.llm = OpenAI(api_key=api_key)
    Settings.embed_model = OpenAIEmbedding(api_key=api_key)
except Exception as e:
    st.error(f"❌ OpenAI 설정 중 오류 발생: {e}")
    st.stop()

# ✅ 문서 로드
try:
    docs_path = Path(__file__).parent.parent / "docs"  # 상대경로 기반 절대경로
    documents = SimpleDirectoryReader(str(docs_path)).load_data()
    
    if not documents:
        st.warning("⚠️ docs 폴더에 문서가 없습니다. 텍스트 또는 PDF 문서를 추가해주세요.")
        st.stop()
    
    st.success(f"✅ {len(documents)}개 문서 로딩 완료!")
except Exception as e:
    st.error(f"❌ 문서 로딩 실패: {e}")
    st.stop()

# ✅ 인덱스 생성 및 QA 엔진 초기화
try:
    index = VectorStoreIndex.from_documents(documents)
    query_engine = index.as_query_engine()
except Exception as e:
    st.error(f"❌ 인덱스 생성 실패: {e}")
    st.stop()

# ✅ 질문 입력
question = st.text_input("❓ 질문을 입력하세요:")

if question:
    with st.spinner("답변 생성 중..."):
        try:
            response = query_engine.query(question)
            st.subheader("📎 답변")
            st.write(response)
        except Exception as e:
            st.error(f"❌ 답변 생성 중 오류 발생: {e}")
