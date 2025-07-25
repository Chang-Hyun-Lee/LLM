# 완전한 다중 파일 PDF ChatGPT 웹 애플리케이션
# 실행 명령: streamlit run app_multi-file.py

import streamlit as st
import os
import tempfile
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import pickle

# ingest.py 모듈 임포트 (같은 디렉토리에 있어야 함)
from ingest import DocumentIngestor

# 페이지 설정
st.set_page_config(
    page_title="PDF ChatGPT Multi-File",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .bot-message {
        background-color: #f5f5f5;
        border-left: 4px solid #4caf50;
    }
    .sidebar-header {
        font-size: 1.2rem;
        font-weight: bold;
        color: #333;
        margin-bottom: 1rem;
    }
    .file-info {
        background-color: #f8f9fa;
        padding: 0.5rem;
        border-radius: 0.3rem;
        margin: 0.3rem 0;
    }
</style>
""", unsafe_allow_html=True)

class MultiFilePDFChatBot:
    def __init__(self):
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """세션 상태 초기화"""
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        if 'vectorstore' not in st.session_state:
            st.session_state.vectorstore = None
        if 'uploaded_files_data' not in st.session_state:
            st.session_state.uploaded_files_data = {}  # 파일명: {vectorstore, metadata}
        if 'selected_files' not in st.session_state:
            st.session_state.selected_files = []
        if 'conversation_chain' not in st.session_state:
            st.session_state.conversation_chain = None
        if 'api_key_valid' not in st.session_state:
            st.session_state.api_key_valid = False
        if 'processing' not in st.session_state:
            st.session_state.processing = False
    
    def validate_api_key(self, api_key):
        """OpenAI API 키 검증"""
        try:
            os.environ["OPENAI_API_KEY"] = api_key
            # 간단한 API 호출로 키 검증
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            client.models.list()
            return True
        except Exception:
            return False
    
    def setup_conversation_chain(self, api_key):
        """대화 체인 설정 - output_key 문제 완전 해결"""
        try:
            # LLM 설정
            llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0.7,
                api_key=api_key
            )
            
            # 메모리 설정 - output_key 명시
            memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                output_key="answer"  # 🔑 핵심: 메모리에 저장할 키 명시
            )
            
            # 대화형 검색 체인 생성 - output_key 명시
            if st.session_state.vectorstore:
                conversation_chain = ConversationalRetrievalChain.from_llm(
                    llm=llm,
                    retriever=st.session_state.vectorstore.as_retriever(
                        search_kwargs={"k": 3}
                    ),
                    memory=memory,
                    return_source_documents=True,
                    output_key="answer"  # 🔑 핵심: 출력 키 명시
                )
                st.session_state.conversation_chain = conversation_chain
                return True
        except Exception as e:
            st.error(f"대화 체인 설정 오류: {str(e)}")
        return False
    
    def process_uploaded_file(self, uploaded_file, api_key):
        """업로드된 파일 처리"""
        if uploaded_file is None:
            return False
        
        file_name = uploaded_file.name
        
        # 이미 처리된 파일인지 확인
        if file_name in st.session_state.uploaded_files_data:
            st.warning(f"'{file_name}' 파일은 이미 처리되었습니다.")
            return True
        
        try:
            # 임시 파일 생성
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            # 문서 인덱서 생성
            ingestor = DocumentIngestor(api_key)
            
            # PDF 인덱싱
            vectorstore = ingestor.ingest_pdf(tmp_file_path)
            
            # 임시 파일 삭제
            os.unlink(tmp_file_path)
            
            if vectorstore:
                # 파일 데이터 저장
                st.session_state.uploaded_files_data[file_name] = {
                    'vectorstore': vectorstore,
                    'pages': vectorstore.index.ntotal if hasattr(vectorstore, 'index') else 0,
                    'size': len(uploaded_file.getvalue()),
                    'upload_time': str(pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"))
                }
                
                # 자동으로 새 파일 선택
                if file_name not in st.session_state.selected_files:
                    st.session_state.selected_files.append(file_name)
                
                self.update_combined_vectorstore(api_key)
                return True
            
        except Exception as e:
            st.error(f"파일 처리 오류: {str(e)}")
        
        return False
    
    def update_combined_vectorstore(self, api_key):
        """선택된 파일들의 벡터스토어를 결합"""
        if not st.session_state.selected_files:
            st.session_state.vectorstore = None
            st.session_state.conversation_chain = None
            return
        
        try:
            # 선택된 파일들의 벡터스토어 가져오기
            selected_vectorstores = []
            for file_name in st.session_state.selected_files:
                if file_name in st.session_state.uploaded_files_data:
                    vectorstore = st.session_state.uploaded_files_data[file_name]['vectorstore']
                    selected_vectorstores.append(vectorstore)
            
            if not selected_vectorstores:
                st.session_state.vectorstore = None
                st.session_state.conversation_chain = None
                return
            
            # 첫 번째 벡터스토어를 기본으로 사용
            combined_vectorstore = selected_vectorstores[0]
            
            # 나머지 벡터스토어들을 결합
            if len(selected_vectorstores) > 1:
                for vs in selected_vectorstores[1:]:
                    try:
                        # FAISS 인덱스 결합
                        combined_vectorstore.merge_from(vs)
                    except Exception as merge_error:
                        st.warning(f"벡터스토어 결합 중 일부 오류: {merge_error}")
                        continue
            
            st.session_state.vectorstore = combined_vectorstore
            self.setup_conversation_chain(api_key)
            
        except Exception as e:
            st.error(f"벡터스토어 결합 오류: {str(e)}")
            st.session_state.vectorstore = None
    
    def load_saved_vectorstore(self, load_path, api_key):
        """저장된 벡터 스토어 로드"""
        try:
            embeddings = OpenAIEmbeddings(api_key=api_key)
            vectorstore = FAISS.load_local(load_path, embeddings)
            
            # 로드된 벡터스토어를 새 파일로 추가
            file_name = f"loaded_index_{len(st.session_state.uploaded_files_data) + 1}"
            st.session_state.uploaded_files_data[file_name] = {
                'vectorstore': vectorstore,
                'pages': vectorstore.index.ntotal if hasattr(vectorstore, 'index') else 0,
                'size': 0,  # 로드된 파일은 크기 알 수 없음
                'upload_time': 'Loaded from disk'
            }
            
            # 자동으로 선택
            if file_name not in st.session_state.selected_files:
                st.session_state.selected_files.append(file_name)
            
            self.update_combined_vectorstore(api_key)
            return True
        except Exception as e:
            st.error(f"벡터 스토어 로드 오류: {str(e)}")
            return False
    
    def get_response(self, question):
        """질문에 대한 답변 생성"""
        if not st.session_state.conversation_chain:
            return "먼저 PDF 파일을 업로드하고 선택해주세요."
        
        if not st.session_state.selected_files:
            return "활용할 PDF 파일을 선택해주세요."
        
        try:
            # 질문 처리
            result = st.session_state.conversation_chain({"question": question})
            
            # 답변과 출처 추출
            answer = result["answer"]
            source_documents = result.get("source_documents", [])
            
            # 출처 정보 추가 (파일명도 포함)
            if source_documents:
                sources = []
                for doc in source_documents:
                    page = doc.metadata.get('page', '알 수 없음')
                    source_file = doc.metadata.get('source', '알 수 없는 파일')
                    # 파일 경로에서 파일명만 추출
                    if '/' in source_file:
                        source_file = source_file.split('/')[-1]
                    sources.append(f"{source_file} 페이지 {page}")
                
                # 현재 활용 중인 파일 정보
                active_files = ', '.join(st.session_state.selected_files)
                answer += f"\n\n📚 **출처**: {', '.join(set(sources))}"
                answer += f"\n📁 **활용 파일**: {active_files}"
            
            return answer
            
        except Exception as e:
            return f"답변 생성 중 오류 발생: {str(e)}"
    
    def render_sidebar(self):
        """사이드바 렌더링"""
        with st.sidebar:
            st.markdown('<p class="sidebar-header">🔧 설정</p>', unsafe_allow_html=True)
            
            # OpenAI API 키 입력
            api_key = st.text_input(
                "OpenAI API 키",
                type="password",
                help="OpenAI API 키를 입력하세요"
            )
            
            if api_key:
                if self.validate_api_key(api_key):
                    st.success("✅ API 키가 유효합니다")
                    st.session_state.api_key_valid = True
                else:
                    st.error("❌ 유효하지 않은 API 키입니다")
                    st.session_state.api_key_valid = False
            
            st.divider()
            
            # 파일 업로드 섹션
            st.markdown('<p class="sidebar-header">📁 파일 업로드</p>', unsafe_allow_html=True)
            
            uploaded_file = st.file_uploader(
                "PDF 파일 선택",
                type="pdf",
                help="분석할 PDF 파일을 업로드하세요"
            )
            
            if uploaded_file and st.session_state.api_key_valid:
                if st.button("📄 PDF 처리하기", type="primary"):
                    st.session_state.processing = True
                    
                    with st.spinner("PDF를 처리하는 중..."):
                        if self.process_uploaded_file(uploaded_file, api_key):
                            st.success("✅ PDF 처리 완료!")
                            st.rerun()
                        else:
                            st.error("❌ PDF 처리 실패")
                    
                    st.session_state.processing = False
            
            st.divider()
            
            # 업로드된 파일 관리 섹션
            if st.session_state.uploaded_files_data:
                st.markdown('<p class="sidebar-header">📚 업로드된 파일</p>', unsafe_allow_html=True)
                
                # 파일 선택 (복수 선택 가능)
                file_options = list(st.session_state.uploaded_files_data.keys())
                selected_files = st.multiselect(
                    "활용할 파일 선택",
                    options=file_options,
                    default=st.session_state.selected_files,
                    help="질문에 사용할 PDF 파일들을 선택하세요"
                )
                
                # 선택 변경시 벡터스토어 업데이트
                if selected_files != st.session_state.selected_files:
                    st.session_state.selected_files = selected_files
                    if st.session_state.api_key_valid:
                        self.update_combined_vectorstore(api_key)
                        st.rerun()
                
                # 전체 선택/해제 버튼
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ 전체 선택"):
                        st.session_state.selected_files = file_options.copy()
                        if st.session_state.api_key_valid:
                            self.update_combined_vectorstore(api_key)
                        st.rerun()
                
                with col2:
                    if st.button("❌ 전체 해제"):
                        st.session_state.selected_files = []
                        if st.session_state.api_key_valid:
                            self.update_combined_vectorstore(api_key)
                        st.rerun()
                
                # 파일 정보 표시
                for file_name in file_options:
                    file_data = st.session_state.uploaded_files_data[file_name]
                    is_selected = file_name in st.session_state.selected_files
                    
                    with st.expander(f"{'✅' if is_selected else '⬜'} {file_name}", expanded=False):
                        st.markdown(f"""
                        <div class="file-info">
                        <strong>📄 청크 수:</strong> {file_data['pages']}개<br>
                        <strong>💾 파일 크기:</strong> {file_data['size']/1024:.1f} KB<br>
                        <strong>🕒 업로드 시간:</strong> {file_data.get('upload_time', '알 수 없음')}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # 파일 삭제 버튼
                        if st.button(f"🗑️ 삭제", key=f"delete_{file_name}"):
                            del st.session_state.uploaded_files_data[file_name]
                            if file_name in st.session_state.selected_files:
                                st.session_state.selected_files.remove(file_name)
                            if st.session_state.api_key_valid:
                                self.update_combined_vectorstore(api_key)
                            st.rerun()
                
                st.divider()
            
            # 저장된 인덱스 로드 섹션
            st.markdown('<p class="sidebar-header">💾 저장된 인덱스</p>', unsafe_allow_html=True)
            
            load_path = st.text_input(
                "인덱스 경로",
                placeholder="예: ./vectorstore",
                help="이전에 저장한 벡터 스토어 경로"
            )
            
            if load_path and st.session_state.api_key_valid:
                if st.button("📂 인덱스 로드"):
                    if self.load_saved_vectorstore(load_path, api_key):
                        st.success("✅ 인덱스 로드 완료!")
                        st.rerun()
            
            st.divider()
            
            # 상태 정보
            st.markdown('<p class="sidebar-header">📊 상태</p>', unsafe_allow_html=True)
            
            if st.session_state.uploaded_files_data:
                st.success(f"✅ {len(st.session_state.uploaded_files_data)}개 파일 업로드됨")
                if st.session_state.selected_files:
                    st.info(f"📁 {len(st.session_state.selected_files)}개 파일 선택됨")
                    total_chunks = sum([
                        st.session_state.uploaded_files_data[f]['pages'] 
                        for f in st.session_state.selected_files 
                        if f in st.session_state.uploaded_files_data
                    ])
                    st.info(f"📄 총 {total_chunks}개 청크 활용")
                else:
                    st.warning("⚠️ 파일을 선택해주세요")
            else:
                st.warning("⚠️ PDF를 업로드해주세요")
            
            if st.session_state.conversation_chain:
                st.success("✅ 챗봇이 준비되었습니다")
            else:
                st.warning("⚠️ 챗봇 설정 필요")
            
            st.divider()
            
            # 초기화 버튼들
            st.markdown('<p class="sidebar-header">🔄 초기화</p>', unsafe_allow_html=True)
            
            # 전체 초기화 버튼
            if st.button("🗑️ 전체 초기화", help="모든 파일과 대화를 삭제합니다"):
                st.session_state.messages = []
                st.session_state.uploaded_files_data = {}
                st.session_state.selected_files = []
                st.session_state.vectorstore = None
                st.session_state.conversation_chain = None
                st.success("전체 초기화 완료!")
                st.rerun()
            
            # 대화만 초기화 버튼
            if st.session_state.conversation_chain:
                if st.button("💬 대화만 초기화", help="대화 기록만 삭제합니다"):
                    st.session_state.messages = []
                    if st.session_state.conversation_chain:
                        st.session_state.conversation_chain.memory.clear()
                    st.success("대화 초기화 완료!")
                    st.rerun()
    
    def render_main_content(self):
        """메인 콘텐츠 렌더링"""
        # 헤더
        st.markdown('<h1 class="main-header">🤖 PDF ChatGPT Multi-File</h1>', unsafe_allow_html=True)
        st.markdown("---")
        
        # 시작 안내
        if not st.session_state.uploaded_files_data:
            st.info("""
            👋 **다중 파일 PDF ChatGPT에 오신 것을 환영합니다!** 
            
            이 애플리케이션 사용법:
            1. 📝 왼쪽 사이드바에서 **OpenAI API 키**를 입력하세요
            2. 📁 **PDF 파일들을 업로드**하고 처리하세요 (여러 파일 가능)
            3. 📚 질문에 **활용할 파일들을 선택**하세요 (복수 선택 가능)
            4. 💬 선택된 PDF 내용에 대해 **질문**하세요
            
            ✨ **특징:**
            - 🔄 여러 PDF 파일 동시 관리
            - 📂 파일별 개별 삭제/선택
            - 🔍 선택한 파일들을 통합해서 검색
            - 📚 출처 정보와 활용 파일 표시
            """)
            return
        
        # 선택된 파일이 없는 경우
        if not st.session_state.selected_files:
            st.warning("""
            ⚠️ **파일을 선택해주세요!**
            
            왼쪽 사이드바에서 질문에 활용할 PDF 파일들을 선택하세요.
            """)
            return
        
        # 현재 활용 중인 파일 표시
        if st.session_state.selected_files:
            with st.expander(f"📚 현재 활용 중인 파일 ({len(st.session_state.selected_files)}개)", expanded=False):
                cols = st.columns(min(len(st.session_state.selected_files), 3))
                for i, file_name in enumerate(st.session_state.selected_files):
                    with cols[i % 3]:
                        if file_name in st.session_state.uploaded_files_data:
                            file_data = st.session_state.uploaded_files_data[file_name]
                            st.markdown(f"""
                            **📄 {file_name}**
                            - 청크: {file_data['pages']}개
                            - 크기: {file_data['size']/1024:.1f} KB
                            """)
        
        # 채팅 메시지 표시
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # 채팅 입력
        if prompt := st.chat_input("PDF에 대해 질문하세요..."):
            # 사용자 메시지 추가
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # 봇 응답 생성
            with st.chat_message("assistant"):
                with st.spinner("답변을 생성하는 중..."):
                    response = self.get_response(prompt)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
    
    def run(self):
        """애플리케이션 실행"""
        self.render_sidebar()
        self.render_main_content()


def main():
    """메인 함수"""
    # pandas import 추가 (시간 표시용)
    try:
        import pandas as pd
        globals()['pd'] = pd
    except ImportError:
        st.warning("pandas가 설치되지 않았습니다. 시간 표시 기능이 제한됩니다.")
    
    chatbot = MultiFilePDFChatBot()
    chatbot.run()


if __name__ == "__main__":
    main()