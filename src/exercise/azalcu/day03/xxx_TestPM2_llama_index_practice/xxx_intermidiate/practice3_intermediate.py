# intermediate/practice3_intermediate.py
import streamlit as st
import os
import tempfile
from datetime import datetime
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

st.set_page_config(page_title="파일 업로드 분석", page_icon="📂")
st.title("📂 중급: 파일 업로드 & 분석 시스템")

# 세션 상태 초기화
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = {}
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = {}

# 사이드바
with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.text_input("OpenAI API Key", type="password")
    
    # 업로드된 파일 정보
    st.header("📁 업로드된 파일")
    if st.session_state.uploaded_files:
        for filename, info in st.session_state.uploaded_files.items():
            st.text(f"📄 {filename}")
            st.caption(f"크기: {info['size']//1024}KB")
            st.caption(f"업로드: {info['upload_time']}")
    else:
        st.info("업로드된 파일이 없습니다.")

def save_uploaded_file(uploaded_file):
    """업로드된 파일을 임시 폴더에 저장"""
    # 임시 디렉토리 생성
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, uploaded_file.name)
    
    # 파일 저장
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # 메타데이터 저장
    file_info = {
        'path': file_path,
        'size': uploaded_file.size,
        'type': uploaded_file.type,
        'upload_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    st.session_state.uploaded_files[uploaded_file.name] = file_info
    return file_path

def analyze_file(file_path, api_key):
    """단일 파일 분석"""
    try:
        # LlamaIndex 설정
        Settings.llm = OpenAI(api_key=api_key)
        Settings.embed_model = OpenAIEmbedding(api_key=api_key)
        
        # 문서 로드
        documents = SimpleDirectoryReader(input_files=[file_path]).load_data()
        if not documents:
            return None, "문서를 읽을 수 없습니다."
        
        # 인덱스 생성
        index = VectorStoreIndex.from_documents(documents)
        query_engine = index.as_query_engine()
        
        # 다양한 분석 수행
        analyses = {}
        
        # 요약
        summary_response = query_engine.query("이 문서의 핵심 내용을 3-5줄로 요약해주세요.")
        analyses['summary'] = str(summary_response)
        
        # 주요 주제
        topics_response = query_engine.query("이 문서에서 다루는 주요 주제나 키워드들을 나열해주세요.")
        analyses['topics'] = str(topics_response)
        
        # 문서 유형
        type_response = query_engine.query("이 문서는 어떤 종류의 문서인가요? (예: 보고서, 논문, 매뉴얼 등)")
        analyses['document_type'] = str(type_response)
        
        return analyses, "분석 완료"
        
    except Exception as e:
        return None, f"분석 실패: {str(e)}"

# 메인 컨텐츠
tab1, tab2, tab3 = st.tabs(["📤 파일 업로드", "📊 분석 결과", "💬 질문하기"])

with tab1:
    st.header("📤 파일 업로드")
    
    # 파일 업로드
    uploaded_files = st.file_uploader(
        "분석할 파일들을 업로드하세요",
        type=['pdf', 'txt', 'docx', 'md'],
        accept_multiple_files=True,
        help="PDF, TXT, DOCX, MD 파일을 지원합니다"
    )
    
    if uploaded_files and api_key:
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📁 파일 저장", type="primary"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, uploaded_file in enumerate(uploaded_files):
                    if uploaded_file.name not in st.session_state.uploaded_files:
                        status_text.text(f"저장 중: {uploaded_file.name}")
                        save_uploaded_file(uploaded_file)
                        progress_bar.progress((i + 1) / len(uploaded_files))
                
                status_text.success("✅ 모든 파일 저장 완료!")
                st.rerun()
        
        with col2:
            if st.button("🔍 파일 분석", type="secondary"):
                if st.session_state.uploaded_files:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for i, (filename, info) in enumerate(st.session_state.uploaded_files.items()):
                        if filename not in st.session_state.analysis_results:
                            status_text.text(f"분석 중: {filename}")
                            
                            analysis, message = analyze_file(info['path'], api_key)
                            if analysis:
                                st.session_state.analysis_results[filename] = analysis
                            
                            progress_bar.progress((i + 1) / len(st.session_state.uploaded_files))
                    
                    status_text.success("✅ 모든 파일 분석 완료!")
                    st.rerun()
    
    elif not api_key:
        st.warning("분석을 위해 사이드바에서 API 키를 입력해주세요.")

with tab2:
    st.header("📊 분석 결과")
    
    if st.session_state.analysis_results:
        for filename, analysis in st.session_state.analysis_results.items():
            with st.expander(f"📄 {filename} 분석 결과", expanded=True):
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📝 요약")
                    st.write(analysis.get('summary', '요약 없음'))
                    
                    st.subheader("📋 문서 유형")
                    st.write(analysis.get('document_type', '분류 없음'))
                
                with col2:
                    st.subheader("🔑 주요 주제")
                    st.write(analysis.get('topics', '주제 없음'))
                
                st.divider()
    else:
        st.info("분석된 파일이 없습니다. 파일을 업로드하고 분석을 실행해주세요.")

with tab3:
    st.header("💬 파일에 대해 질문하기")
    
    if st.session_state.uploaded_files and api_key:
        # 전체 파일에 대한 통합 질문
        try:
            Settings.llm = OpenAI(api_key=api_key)
            Settings.embed_model = OpenAIEmbedding(api_key=api_key)
            
            # 모든 파일 로드
            all_file_paths = [info['path'] for info in st.session_state.uploaded_files.values()]
            all_documents = []
            
            for file_path in all_file_paths:
                docs = SimpleDirectoryReader(input_files=[file_path]).load_data()
                all_documents.extend(docs)
            
            # 통합 인덱스 생성
            index = VectorStoreIndex.from_documents(all_documents)
            query_engine = index.as_query_engine()
            
            st.success(f"✅ {len(all_documents)}개 문서가 준비되었습니다.")
            
            # 질문 입력
            question = st.text_input("모든 업로드된 파일에 대해 질문하세요:")
            
            if question:
                with st.spinner("답변을 생성하는 중..."):
                    response = query_engine.query(question)
                    st.write("### 📝 답변")
                    st.write(response)
                    
        except Exception as e:
            st.error(f"질문 처리 중 오류: {str(e)}")
    else:
        if not api_key:
            st.warning("API 키를 입력해주세요.")
        if not st.session_state.uploaded_files:
            st.info("먼저 파일을 업로드해주세요.")