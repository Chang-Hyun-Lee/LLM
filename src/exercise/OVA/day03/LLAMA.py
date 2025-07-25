import streamlit as st
import os
import shutil
from pathlib import Path
from datetime import datetime
import json
import traceback

# LlamaIndex 관련 imports
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.storage.storage_context import StorageContext
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import Settings

# ============== API 키 설정 ==============
API_KEY = "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"  # 실제 키로 교체하세요
# =========================================

# 페이지 설정
st.set_page_config(
    page_title="LlamaIndex 4개 실습 완전판",
    page_icon="🦙",
    layout="wide"
)

# 디렉토리 설정
PERSIST_DIR = "./storage"
DATA_DIR = "./uploaded_files"
METADATA_FILE = "./file_metadata.json"

# 디렉토리 생성
os.makedirs(PERSIST_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# LlamaIndex 설정
def setup_llama_index():
    try:
        Settings.llm = OpenAI(model="gpt-3.5-turbo", temperature=0.1, api_key=API_KEY)
        Settings.embed_model = OpenAIEmbedding(api_key=API_KEY)
        return True
    except Exception as e:
        st.error(f"❌ LlamaIndex 설정 실패: {e}")
        return False

# 문서 검증
def validate_documents(documents):
    if not documents:
        return False, "문서 목록이 비어있습니다."
    
    valid_docs = []
    for doc in documents:
        if hasattr(doc, 'text') and doc.text.strip():
            valid_docs.append(doc)
    
    if not valid_docs:
        return False, "유효한 텍스트 내용이 있는 문서가 없습니다."
    
    return True, valid_docs

# 견고한 인덱스 생성
def create_robust_index():
    try:
        if os.path.exists(DATA_DIR) and os.listdir(DATA_DIR):
            documents = SimpleDirectoryReader(input_dir=DATA_DIR).load_data()
            is_valid, result = validate_documents(documents)
            
            if is_valid:
                index = VectorStoreIndex.from_documents(result)
                st.success(f"✅ {len(result)}개 문서로 인덱스 생성 완료!")
                return index
            else:
                st.error(f"❌ 문서 검증 실패: {result}")
                return None
        else:
            st.info("📝 업로드된 파일이 없어 빈 인덱스를 생성합니다.")
            return VectorStoreIndex([])
    except Exception as e:
        st.error(f"❌ 인덱스 생성 중 오류: {e}")
        return None

# 안전한 질의
def safe_query(index, query_text):
    if index is None:
        return None, "인덱스가 생성되지 않았습니다."
    
    try:
        query_engine = index.as_query_engine(
            similarity_top_k=3,
            response_mode="compact"
        )
        response = query_engine.query(query_text)
        
        if response and hasattr(response, 'response') and response.response:
            return response, None
        else:
            return None, "응답이 생성되지 않았습니다."
    except Exception as e:
        return None, f"질의 처리 오류: {str(e)}"

# 파일 업로드
def upload_and_index_file(uploaded_file):
    try:
        file_path = os.path.join(DATA_DIR, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getvalue())
        
        documents = SimpleDirectoryReader(input_files=[file_path]).load_data()
        is_valid, result = validate_documents(documents)
        
        if not is_valid:
            os.remove(file_path)
            return False, f"문서 처리 실패: {result}"
        
        for doc in result:
            doc.metadata.update({
                "filename": uploaded_file.name,
                "upload_time": datetime.now().isoformat(),
                "file_size": uploaded_file.size
            })
        
        return True, result
    except Exception as e:
        return False, f"파일 업로드 실패: {str(e)}"

# 파일 목록
def get_uploaded_files():
    files = []
    if os.path.exists(DATA_DIR):
        for filename in os.listdir(DATA_DIR):
            file_path = os.path.join(DATA_DIR, filename)
            if os.path.isfile(file_path):
                files.append({
                    "name": filename,
                    "size": os.path.getsize(file_path),
                    "modified": datetime.fromtimestamp(os.path.getmtime(file_path))
                })
    return files

# 파일 삭제
def delete_file(filename):
    try:
        file_path = os.path.join(DATA_DIR, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        return True
    except Exception as e:
        st.error(f"파일 삭제 실패: {e}")
        return False

def main():
    st.title("🦙 LlamaIndex + Streamlit 완전한 4개 실습")
    st.markdown("**실습 #1~#4 모든 기능이 포함된 완성판입니다!**")
    
    # LlamaIndex 설정
    if not setup_llama_index():
        st.stop()
    
    # 사이드바
    with st.sidebar:
        st.header("🎯 실습 선택")
        exercise = st.selectbox("실습을 선택하세요:", [
            "실습 #1: 기본 Q&A",
            "실습 #2: 멀티턴 채팅", 
            "실습 #3: 파일 업로드 & 요약",
            "실습 #4: 파일 관리"
        ])
        
        st.markdown("---")
        
        # 파일 상태
        files = get_uploaded_files()
        st.metric("📄 업로드된 파일", len(files))
        
        # 전체 초기화
        if st.button("🗑️ 전체 초기화"):
            if st.checkbox("정말 삭제하시겠습니까?"):
                try:
                    if os.path.exists(DATA_DIR):
                        shutil.rmtree(DATA_DIR)
                        os.makedirs(DATA_DIR)
                    if os.path.exists(PERSIST_DIR):
                        shutil.rmtree(PERSIST_DIR)
                        os.makedirs(PERSIST_DIR)
                    if "chat_messages" in st.session_state:
                        del st.session_state.chat_messages
                    st.success("✅ 초기화 완료!")
                    st.rerun()
                except Exception as e:
                    st.error(f"초기화 실패: {e}")
    
    # 인덱스 생성
    with st.spinner("🔄 인덱스 준비 중..."):
        index = create_robust_index()
    
    # 실습별 실행
    if exercise == "실습 #1: 기본 Q&A":
        exercise_1(index)
    elif exercise == "실습 #2: 멀티턴 채팅":
        exercise_2(index)
    elif exercise == "실습 #3: 파일 업로드 & 요약":
        exercise_3(index)
    elif exercise == "실습 #4: 파일 관리":
        exercise_4(index)

# ==================== 실습 #1: 기본 Q&A ====================
def exercise_1(index):
    st.header("📝 실습 #1: 기본 Q&A")
    st.markdown("인덱스된 파일에 대해 질문하고 GPT를 통해 답변을 받습니다.")
    
    files = get_uploaded_files()
    if files:
        st.info(f"📚 현재 {len(files)}개 파일이 인덱스되어 있습니다.")
        with st.expander("📂 인덱스된 파일 목록"):
            for file in files:
                st.write(f"• {file['name']} ({file['size']:,} bytes)")
    else:
        st.warning("⚠️ 인덱스된 파일이 없습니다. 실습 #3에서 파일을 업로드해주세요.")
        return
    
    query = st.text_input(
        "💬 질문을 입력하세요:",
        placeholder="예: 업로드한 문서의 주요 내용은 무엇인가요?"
    )
    
    if st.button("🔍 질문하기", type="primary") and query:
        with st.spinner("🤔 답변을 생성하는 중..."):
            response, error = safe_query(index, query)
            
            if response:
                st.markdown("### 📋 답변")
                st.write(response.response)
                
                if hasattr(response, 'source_nodes') and response.source_nodes:
                    with st.expander("📚 참조된 문서"):
                        for i, node in enumerate(response.source_nodes, 1):
                            st.markdown(f"**참조 {i}:**")
                            if hasattr(node, 'metadata') and 'filename' in node.metadata:
                                st.write(f"**파일:** {node.metadata['filename']}")
                            st.text(node.text[:300] + "..." if len(node.text) > 300 else node.text)
                            st.markdown("---")
            else:
                st.error(f"❌ 질문 처리 실패: {error}")

# ==================== 실습 #2: 멀티턴 채팅 ====================
def exercise_2(index):
    st.header("💬 실습 #2: 멀티턴 채팅")
    st.markdown("이전 질문과 답변을 유지하며 대화형으로 응답합니다.")
    
    files = get_uploaded_files()
    if not files:
        st.warning("⚠️ 대화할 문서가 없습니다. 실습 #3에서 파일을 업로드해주세요.")
        return
    
    st.info(f"📚 {len(files)}개 파일과 대화할 수 있습니다.")
    
    # 채팅 기록 초기화
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    
    # 채팅 기록 표시
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # 사용자 입력
    if prompt := st.chat_input("메시지를 입력하세요..."):
        # 사용자 메시지 추가
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # AI 응답 생성
        with st.chat_message("assistant"):
            with st.spinner("답변 생성 중..."):
                response, error = safe_query(index, prompt)
                
                if response:
                    st.write(response.response)
                    # AI 응답 저장
                    st.session_state.chat_messages.append({"role": "assistant", "content": response.response})
                else:
                    error_msg = f"죄송합니다. 오류가 발생했습니다: {error}"
                    st.error(error_msg)
                    st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})
    
    # 채팅 초기화 버튼
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🗑️ 채팅 초기화"):
            st.session_state.chat_messages = []
            st.rerun()

# ==================== 실습 #3: 파일 업로드 & 요약 ====================
def exercise_3(index):
    st.header("📁 실습 #3: 파일 업로드 & 자동 요약")
    st.markdown("PDF나 텍스트 파일을 업로드하여 자동 인덱싱하고 요약을 생성합니다.")
    
    uploaded_files = st.file_uploader(
        "📤 파일을 업로드하세요",
        type=['pdf', 'txt', 'md', 'docx'],
        accept_multiple_files=True,
        help="PDF, TXT, MD, DOCX 파일을 지원합니다."
    )
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            with st.expander(f"📄 {uploaded_file.name}", expanded=True):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**파일명:** {uploaded_file.name}")
                    st.write(f"**크기:** {uploaded_file.size:,} bytes")
                    st.write(f"**타입:** {uploaded_file.type}")
                
                with col2:
                    if st.button(f"📥 인덱싱 & 요약", key=f"upload_{uploaded_file.name}"):
                        with st.spinner(f"'{uploaded_file.name}' 처리 중..."):
                            success, result = upload_and_index_file(uploaded_file)
                            
                            if success:
                                st.success(f"✅ '{uploaded_file.name}' 업로드 완료!")
                                
                                # 자동 요약 생성
                                try:
                                    new_index = create_robust_index()
                                    if new_index:
                                        summary_response, error = safe_query(
                                            new_index, 
                                            f"'{uploaded_file.name}' 파일의 내용을 자세히 요약해주세요. 주요 내용과 핵심 포인트를 포함해주세요."
                                        )
                                        
                                        if summary_response:
                                            st.markdown("### 📄 자동 생성 요약")
                                            st.write(summary_response.response)
                                            
                                            # 문서 미리보기
                                            if result:
                                                with st.expander("📖 문서 내용 미리보기"):
                                                    for i, doc in enumerate(result[:3]):
                                                        st.markdown(f"**섹션 {i+1}:**")
                                                        preview_text = doc.text[:500] + "..." if len(doc.text) > 500 else doc.text
                                                        st.text(preview_text)
                                                        if i < len(result) - 1:
                                                            st.markdown("---")
                                        else:
                                            st.warning(f"요약 생성 실패: {error}")
                                    
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"요약 생성 실패: {e}")
                            else:
                                st.error(f"❌ '{uploaded_file.name}' 업로드 실패: {result}")

# ==================== 실습 #4: 파일 관리 ====================
def exercise_4(index):
    st.header("🗂️ 실습 #4: 파일 관리")
    st.markdown("업로드된 파일들을 관리하고 삭제할 수 있습니다.")
    
    # 새 파일 업로드 섹션
    with st.expander("📤 새 파일 업로드", expanded=False):
        new_file = st.file_uploader(
            "파일 선택",
            type=['pdf', 'txt', 'md', 'docx'],
            key="new_file_upload"
        )
        
        if new_file:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"선택된 파일: **{new_file.name}** ({new_file.size:,} bytes)")
            with col2:
                if st.button("📥 업로드", key="upload_new_file"):
                    success, result = upload_and_index_file(new_file)
                    if success:
                        st.success("업로드 완료!")
                        st.rerun()
                    else:
                        st.error(f"업로드 실패: {result}")
    
    # 현재 파일 목록
    st.markdown("### 📋 업로드된 파일 목록")
    files = get_uploaded_files()
    
    if not files:
        st.info("📂 업로드된 파일이 없습니다.")
        st.markdown("실습 #3에서 파일을 업로드하거나 위의 '새 파일 업로드'를 사용하세요.")
    else:
        for i, file_info in enumerate(files):
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.write(f"**📄 {file_info['name']}**")
                st.caption(f"크기: {file_info['size']:,} bytes")
            
            with col2:
                st.caption(f"수정: {file_info['modified'].strftime('%Y-%m-%d %H:%M')}")
            
            with col3:
                if st.button("🗑️", key=f"delete_{i}", help=f"'{file_info['name']}' 삭제"):
                    if delete_file(file_info['name']):
                        st.success(f"'{file_info['name']}' 삭제 완료!")
                        st.rerun()
                    else:
                        st.error("삭제 실패")
            
            st.markdown("---")
    
    # 문서 검색 섹션
    if files:
        st.markdown("### 💬 업로드된 문서에 질문하기")
        
        col1, col2 = st.columns([4, 1])
        with col1:
            query = st.text_input(
                "질문:",
                placeholder="업로드된 문서들에 대해 질문하세요...",
                key="file_management_query"
            )
        with col2:
            search_button = st.button("🔍 검색", key="search_docs")
        
        if search_button and query:
            with st.spinner("답변 생성 중..."):
                response, error = safe_query(index, query)
                
                if response:
                    st.markdown("#### 📝 답변")
                    st.write(response.response)
                    
                    if hasattr(response, 'source_nodes') and response.source_nodes:
                        with st.expander("📚 참조된 문서 세부정보"):
                            for i, node in enumerate(response.source_nodes, 1):
                                st.markdown(f"**참조 {i}:**")
                                if hasattr(node, 'metadata') and 'filename' in node.metadata:
                                    st.write(f"**파일:** {node.metadata['filename']}")
                                text_content = node.text[:300] + "..." if len(node.text) > 300 else node.text
                                st.text(text_content)
                                st.markdown("---")
                else:
                    st.error(f"❌ 검색 실패: {error}")

if __name__ == "__main__":
    main()