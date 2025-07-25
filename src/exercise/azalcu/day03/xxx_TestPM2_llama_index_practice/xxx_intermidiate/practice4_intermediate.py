# intermediate/practice4_intermediate.py
import streamlit as st
import os
import shutil
import tempfile
from datetime import datetime
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

st.set_page_config(page_title="파일 관리 시스템", page_icon="🗂️", layout="wide")
st.title("🗂️ 중급: 파일 관리 & QA 시스템")

# 세션 상태 초기화
if 'file_storage' not in st.session_state:
    st.session_state.file_storage = {}
if 'temp_dir' not in st.session_state:
    st.session_state.temp_dir = tempfile.mkdtemp()

# 사이드바
with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.text_input("OpenAI API Key", type="password")
    
    # 통계
    file_count = len(st.session_state.file_storage)
    total_size = sum(info.get('size', 0) for info in st.session_state.file_storage.values())
    
    st.metric("파일 수", file_count)
    st.metric("총 크기", f"{total_size // 1024}KB" if total_size > 0 else "0KB")
    
    # 전체 초기화
    if st.button("🗑️ 전체 초기화", type="secondary"):
        if st.button("⚠️ 정말 모든 파일을 삭제하시겠습니까?"):
            # 파일 삭제
            for file_info in st.session_state.file_storage.values():
                if os.path.exists(file_info['path']):
                    os.remove(file_info['path'])
            
            # 세션 초기화
            st.session_state.file_storage = {}
            if 'index' in st.session_state:
                del st.session_state['index']
            
            st.success("전체 초기화 완료!")
            st.rerun()

def save_uploaded_file(uploaded_file):
    """파일을 저장하고 메타데이터 관리"""
    file_path = os.path.join(st.session_state.temp_dir, uploaded_file.name)
    
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
    
    st.session_state.file_storage[uploaded_file.name] = file_info
    return True

def delete_file(filename):
    """파일 삭제"""
    if filename in st.session_state.file_storage:
        file_path = st.session_state.file_storage[filename]['path']
        
        # 물리적 파일 삭제
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # 메타데이터에서 제거
        del st.session_state.file_storage[filename]
        
        # 인덱스 무효화
        if 'index' in st.session_state:
            del st.session_state['index']
        
        return True
    return False

@st.cache_resource
def create_unified_index(_file_paths, _api_key):
    """모든 파일에 대한 통합 인덱스 생성"""
    try:
        Settings.llm = OpenAI(api_key=_api_key)
        Settings.embed_model = OpenAIEmbedding(api_key=_api_key)
        
        all_documents = []
        for file_path in _file_paths:
            if os.path.exists(file_path):
                docs = SimpleDirectoryReader(input_files=[file_path]).load_data()
                # 파일명을 메타데이터에 추가
                for doc in docs:
                    doc.metadata['source_file'] = os.path.basename(file_path)
                all_documents.extend(docs)
        
        if all_documents:
            return VectorStoreIndex.from_documents(all_documents)
        return None
    except Exception as e:
        st.error(f"인덱스 생성 실패: {str(e)}")
        return None

# 메인 탭
tab1, tab2, tab3 = st.tabs(["📁 파일 관리", "🔍 검색 & QA", "📊 파일 분석"])

with tab1:
    st.header("📁 파일 관리")
    
    # 파일 업로드 섹션
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_files = st.file_uploader(
            "새 파일 업로드",
            type=['pdf', 'txt', 'docx', 'md'],
            accept_multiple_files=True
        )
    
    with col2:
        if uploaded_files and st.button("📥 파일 추가", type="primary"):
            added_count = 0
            for uploaded_file in uploaded_files:
                if uploaded_file.name not in st.session_state.file_storage:
                    save_uploaded_file(uploaded_file)
                    added_count += 1
            
            if added_count > 0:
                st.success(f"✅ {added_count}개 파일이 추가되었습니다!")
                # 인덱스 무효화
                if 'index' in st.session_state:
                    del st.session_state['index']
                st.rerun()
            else:
                st.warning("모든 파일이 이미 존재합니다.")
    
    # 파일 목록
    if st.session_state.file_storage:
        st.subheader("📋 저장된 파일 목록")
        
        # 정렬 옵션
        sort_option = st.selectbox(
            "정렬 기준:",
            ["이름순", "업로드 시간순", "크기순"]
        )
        
        # 파일 목록 정렬
        files = list(st.session_state.file_storage.items())
        if sort_option == "이름순":
            files.sort(key=lambda x: x[0])
        elif sort_option == "업로드 시간순":
            files.sort(key=lambda x: x[1]['upload_time'], reverse=True)
        elif sort_option == "크기순":
            files.sort(key=lambda x: x[1]['size'], reverse=True)
        
        # 파일 목록 표시
        for filename, file_info in files:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    st.write(f"📄 **{filename}**")
                    st.caption(f"업로드: {file_info['upload_time']}")
                
                with col2:
                    size_kb = file_info['size'] // 1024
                    st.write(f"{size_kb}KB")
                
                with col3:
                    file_type = file_info.get('type', 'Unknown')
                    st.write(file_type.split('/')[-1].upper() if file_type else 'TXT')
                
                with col4:
                    if st.button("🗑️", key=f"delete_{filename}", help="파일 삭제"):
                        if delete_file(filename):
                            st.success(f"✅ {filename} 삭제됨!")
                            st.rerun()
                
                st.divider()
    else:
        st.info("📁 저장된 파일이 없습니다. 위에서 파일을 업로드해주세요.")

with tab2:
    st.header("🔍 검색 & QA")
    
    if api_key and st.session_state.file_storage:
        # 인덱스 생성/사용
        if 'index' not in st.session_state:
            with st.spinner("검색 인덱스를 생성하는 중..."):
                file_paths = [info['path'] for info in st.session_state.file_storage.values()]
                index = create_unified_index(file_paths, api_key)
                if index:
                    st.session_state.index = index
                    st.success("✅ 검색 인덱스 생성 완료!")
                else:
                    st.error("인덱스 생성 실패")
                    st.stop()
        
        # 검색 타입 선택
        search_type = st.radio(
            "검색 유형:",
            ["일반 질문", "키워드 검색", "문서 요약"],
            horizontal=True
        )
        
        if search_type == "일반 질문":
            question = st.text_input("질문을 입력하세요:")
            if question:
                try:
                    with st.spinner("답변을 찾는 중..."):
                        query_engine = st.session_state.index.as_query_engine()
                        response = query_engine.query(question)
                    
                    st.write("### 📝 답변")
                    st.write(response)
                    
                    # 소스 정보
                    if hasattr(response, 'source_nodes') and response.source_nodes:
                        with st.expander("📄 참조 파일"):
                            for node in response.source_nodes:
                                source_file = node.metadata.get('source_file', 'Unknown')
                                st.write(f"**파일:** {source_file}")
                                st.write(f"**내용:** {node.text[:200]}...")
                                st.divider()
                
                except Exception as e:
                    st.error(f"검색 실패: {str(e)}")
        
        elif search_type == "키워드 검색":
            keyword = st.text_input("검색할 키워드:")
            if keyword:
                try:
                    query_engine = st.session_state.index.as_query_engine()
                    response = query_engine.query(f"'{keyword}'에 대해 모든 관련 정보를 찾아주세요.")
                    
                    st.write("### 🔍 검색 결과")
                    st.write(response)
                
                except Exception as e:
                    st.error(f"검색 실패: {str(e)}")
        
        elif search_type == "문서 요약":
            if st.button("📊 전체 문서 요약"):
                try:
                    with st.spinner("전체 문서를 요약하는 중..."):
                        query_engine = st.session_state.index.as_query_engine()
                        response = query_engine.query(
                            "모든 문서의 내용을 종합하여 주요 내용과 핵심 포인트를 요약해주세요."
                        )
                    
                    st.write("### 📋 전체 문서 요약")
                    st.write(response)
                
                except Exception as e:
                    st.error(f"요약 실패: {str(e)}")
    
    else:
        if not api_key:
            st.warning("검색을 위해 API 키를 입력해주세요.")
        if not st.session_state.file_storage:
            st.info("검색할 파일이 없습니다. 먼저 파일을 업로드해주세요.")

with tab3:
    st.header("📊 파일 분석")
    
    if st.session_state.file_storage:
        # 개별 파일 분석
        selected_file = st.selectbox(
            "분석할 파일 선택:",
            list(st.session_state.file_storage.keys())
        )
        
        if selected_file and api_key:
            if st.button(f"🔍 {selected_file} 분석"):
                try:
                    with st.spinner(f"{selected_file}을 분석하는 중..."):
                        file_path = st.session_state.file_storage[selected_file]['path']
                        
                        # 단일 파일 인덱스 생성
                        Settings.llm = OpenAI(api_key=api_key)
                        Settings.embed_model = OpenAIEmbedding(api_key=api_key)
                        
                        documents = SimpleDirectoryReader(input_files=[file_path]).load_data()
                        index = VectorStoreIndex.from_documents(documents)
                        query_engine = index.as_query_engine()
                        
                        # 다양한 분석
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("📝 문서 요약")
                            summary = query_engine.query("이 문서의 내용을 간단히 요약해주세요.")
                            st.write(summary)
                            
                            st.subheader("📋 문서 유형")
                            doc_type = query_engine.query("이 문서는 어떤 종류의 문서인가요?")
                            st.write(doc_type)
                        
                        with col2:
                            st.subheader("🔑 키워드")
                            keywords = query_engine.query("이 문서의 주요 키워드나 주제를 나열해주세요.")
                            st.write(keywords)
                            
                            st.subheader("📊 중요도")
                            importance = query_engine.query("이 문서에서 가장 중요한 내용은 무엇인가요?")
                            st.write(importance)
                
                except Exception as e:
                    st.error(f"분석 실패: {str(e)}")
    else:
        st.info("분석할 파일이 없습니다.")