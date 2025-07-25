# intermediate/practice1_intermediate.py
import streamlit as st
import os
import tempfile
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings, Document
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

# 페이지 설정
st.set_page_config(page_title="문서 QA", page_icon="📚", layout="wide")
st.title("📚 중급: 문서 QA 시스템")

# 사이드바
with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.text_input("OpenAI API Key", type="password")
    
    st.header("📤 파일 업로드")
    uploaded_files = st.file_uploader(
        "문서를 업로드하세요",
        accept_multiple_files=True,
        type=['pdf', 'txt', 'docx', 'doc', 'md'],
        help="PDF, TXT, DOCX, DOC, MD 파일을 지원합니다"
    )
    
    if st.button("🔄 새로고침"):
        st.cache_data.clear()
        st.rerun()

# 업로드된 파일들을 Document 객체로 변환
@st.cache_data
def process_uploaded_files(uploaded_files):
    if not uploaded_files:
        return None, "업로드된 파일이 없습니다."
    
    documents = []
    processed_files = []
    
    try:
        # 임시 디렉토리 생성
        with tempfile.TemporaryDirectory() as temp_dir:
            # 업로드된 파일들을 임시 디렉토리에 저장
            for uploaded_file in uploaded_files:
                file_path = os.path.join(temp_dir, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                processed_files.append(uploaded_file.name)
            
            # SimpleDirectoryReader로 문서 로드
            reader = SimpleDirectoryReader(temp_dir)
            documents = reader.load_data()
        
        if not documents:
            return None, "문서를 읽을 수 없습니다."
        
        return documents, f"성공적으로 {len(documents)}개 문서를 처리했습니다: {', '.join(processed_files)}"
    
    except Exception as e:
        return None, f"파일 처리 실패: {str(e)}"

# 인덱스 생성 함수 (캐시 적용)
@st.cache_resource
def create_index(documents, _api_key):
    try:
        Settings.llm = OpenAI(api_key=_api_key)
        Settings.embed_model = OpenAIEmbedding(api_key=_api_key)
        return VectorStoreIndex.from_documents(documents)
    except Exception as e:
        st.error(f"인덱스 생성 실패: {str(e)}")
        return None

# 메인 영역을 두 개 컬럼으로 분할
col1, col2 = st.columns([1, 2])

with col1:
    st.header("📋 업로드된 파일")
    if uploaded_files:
        for i, file in enumerate(uploaded_files, 1):
            file_size = len(file.getbuffer()) / 1024  # KB
            st.write(f"**{i}. {file.name}**")
            st.write(f"   📁 크기: {file_size:.1f} KB")
            st.write(f"   📄 타입: {file.type}")
    else:
        st.info("👈 사이드바에서 파일을 업로드하세요")

with col2:
    st.header("💬 질문 & 답변")
    
    if api_key and uploaded_files:
        # 파일 처리
        with st.spinner("업로드된 파일을 처리하는 중..."):
            documents, message = process_uploaded_files(uploaded_files)
        
        if documents:
            st.success(message)
            
            # 인덱스 생성
            with st.spinner("AI 인덱스를 생성하는 중..."):
                index = create_index(documents, api_key)
            
            if index:
                st.success("✅ 준비 완료! 이제 질문하세요")
                
                # 질문 입력
                question = st.text_area(
                    "문서에 대한 질문을 입력하세요:", 
                    placeholder="예: 이 문서의 주요 내용은 무엇인가요?\n문서에서 가장 중요한 포인트는?\n특정 주제에 대해 설명해주세요.",
                    height=100
                )
                
                if st.button("🤖 답변 생성", type="primary"):
                    if question:
                        try:
                            with st.spinner("AI가 답변을 생성하는 중..."):
                                query_engine = index.as_query_engine()
                                response = query_engine.query(question)
                            
                            st.write("### 📝 AI 답변")
                            st.write(response)
                            
                            # 소스 정보 표시
                            if hasattr(response, 'source_nodes') and response.source_nodes:
                                with st.expander("📄 참조된 문서 부분"):
                                    for i, node in enumerate(response.source_nodes):
                                        st.write(f"**참조 {i+1}:**")
                                        st.write(f"```\n{node.text[:300]}...\n```")
                                        if hasattr(node, 'score'):
                                            st.write(f"*관련도: {node.score:.3f}*")
                                        st.write("---")
                                        
                        except Exception as e:
                            st.error(f"답변 생성 중 오류: {str(e)}")
                    else:
                        st.warning("질문을 입력해주세요!")
        else:
            st.error(message)
    
    elif not api_key:
        st.warning("⚠️ 사이드바에서 OpenAI API 키를 입력해주세요.")
        
        st.markdown("""
        ### 🔑 API 키 얻는 방법:
        1. [OpenAI Platform](https://platform.openai.com/api-keys) 접속
        2. 'Create new secret key' 클릭
        3. 생성된 키를 사이드바에 입력
        """)
    
    elif not uploaded_files:
        st.info("📤 사이드바에서 문서를 업로드해주세요.")
        
        st.markdown("""
        ### 📋 사용 방법:
        1. **API 키 입력**: OpenAI API 키를 사이드바에 입력
        2. **파일 업로드**: PDF, TXT, DOCX 등의 문서 업로드
        3. **질문 입력**: 문서 내용에 대한 질문 작성
        4. **답변 확인**: AI가 문서를 바탕으로 답변 제공
        
        ### 💡 지원 파일 형식:
        - 📄 PDF 파일
        - 📝 텍스트 파일 (TXT, MD)
        - 📊 워드 문서 (DOCX, DOC)
        """)

# 하단에 추가 정보
st.markdown("---")

# 예시 질문들
with st.expander("💡 질문 예시"):
    st.markdown("""
    **일반적인 질문:**
    - 이 문서의 주요 내용을 요약해주세요
    - 가장 중요한 포인트는 무엇인가요?
    - 핵심 키워드를 찾아주세요
    
    **구체적인 질문:**
    - [특정 주제]에 대해 어떻게 설명하고 있나요?
    - 문서에서 언급된 숫자/데이터를 알려주세요
    - 결론이나 권장사항은 무엇인가요?
    
    **분석적인 질문:**
    - 문서의 장단점을 분석해주세요
    - 다른 관점에서는 어떻게 볼 수 있을까요?
    - 실무에 어떻게 적용할 수 있을까요?
    """)

# 디버깅 정보
with st.expander("🔧 시스템 정보"):
    st.write(f"업로드된 파일 수: {len(uploaded_files) if uploaded_files else 0}")
    st.write(f"API 키 입력됨: {'✅' if api_key else '❌'}")
    
    # 패키지 버전 확인
    try:
        import llama_index
        st.write(f"llama-index: ✅ v{llama_index.__version__}")
    except:
        st.write("llama-index: ❌ 설치 필요")
    
    try:
        import openai
        st.write(f"openai: ✅ v{openai.__version__}")
    except:
        st.write("openai: ❌ 설치 필요")