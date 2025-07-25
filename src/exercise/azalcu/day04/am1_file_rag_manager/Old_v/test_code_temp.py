# minimal_test.py - CSS와 복잡한 기능 없이 핵심만 테스트
import streamlit as st
import os

st.title("🧪 최소 기능 테스트")

# 1. 기본 streamlit 테스트
st.write("✅ Streamlit 기본 기능 작동")

# 2. 탭 테스트
tab1, tab2 = st.tabs(["테스트1", "테스트2"])

with tab1:
    st.write("탭1 내용")
    if st.button("버튼 테스트"):
        st.success("버튼 클릭됨!")

with tab2:
    st.write("탭2 내용")
    uploaded_file = st.file_uploader("파일 업로드 테스트")
    if uploaded_file:
        st.write(f"업로드된 파일: {uploaded_file.name}")

# 3. 사이드바 테스트
with st.sidebar:
    st.write("사이드바 테스트")
    test_input = st.text_input("텍스트 입력")
    if test_input:
        st.write(f"입력값: {test_input}")

# 4. llama-index import 테스트
st.markdown("---")
st.subheader("📦 Import 테스트")

try:
    from llama_index.core import SimpleDirectoryReader
    st.success("✅ SimpleDirectoryReader import 성공")
    
    from llama_index.llms.openai import OpenAI  
    st.success("✅ OpenAI LLM import 성공")
    
    from llama_index.embeddings.openai import OpenAIEmbedding
    st.success("✅ OpenAI Embedding import 성공")
    
    # 간단한 객체 생성 테스트
    try:
        llm = OpenAI(api_key="test-key")
        st.success("✅ OpenAI 객체 생성 성공")
    except Exception as e:
        st.warning(f"⚠️ OpenAI 객체 생성 실패: {e}")
        
except ImportError as e:
    st.error(f"❌ Import 실패: {e}")
except Exception as e:
    st.error(f"❌ 예상치 못한 오류: {e}")

st.markdown("---")
st.info("위 내용이 모두 보이면 Streamlit은 정상 작동하는 것입니다!")