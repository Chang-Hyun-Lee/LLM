# Day 3 실습: Streamlit PDF ChatGPT 웹 애플리케이션
# 실행 명령: streamlit run app.py

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
    page_title="PDF ChatGPT",
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
</style>
""", unsafe_allow_html=True)

class StreamlitPDFChatBot:
    def __init__(self):
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """세션 상태 초기화"""
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        if 'vectorstore' not in st.session_state:
            st.session_state.vectorstore = None
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
        """대화 체인 설정"""
        try:
            # LLM 설정
            llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0.7,
                api_key=api_key
            )
            
            # 메모리 설정
            memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
            
            # 대화형 검색 체인 생성
            if st.session_state.vectorstore:
                conversation_chain = ConversationalRetrievalChain.from_llm(
                    llm=llm,
                    retriever=st.session_state.vectorstore.as_retriever(
                        search_kwargs={"k": 3}
                    ),
                    memory=memory,
                    return_source_documents=True,
                    output_key="answer"  # 메모리에 저장할 키 명시
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
                st.session_state.vectorstore = vectorstore
                return True
            
        except Exception as e:
            st.error(f"파일 처리 오류: {str(e)}")
        
        return False
    
    def load_saved_vectorstore(self, load_path, api_key):
        """저장된 벡터 스토어 로드"""
        try:
            embeddings = OpenAIEmbeddings(api_key=api_key)
            vectorstore = FAISS.load_local(load_path, embeddings)
            st.session_state.vectorstore = vectorstore
            return True
        except Exception as e:
            st.error(f"벡터 스토어 로드 오류: {str(e)}")
            return False
    
    def get_response(self, question):
        """질문에 대한 답변 생성"""
        if not st.session_state.conversation_chain:
            return "먼저 PDF 파일을 업로드하고 처리해주세요."
        
        try:
            # 질문 처리
            result = st.session_state.conversation_chain({"question": question})
            
            # 답변과 출처 추출
            answer = result["answer"]
            source_documents = result.get("source_documents", [])
            
            # 출처 정보 추가
            if source_documents:
                sources = []
                for doc in source_documents:
                    page = doc.metadata.get('page', '알 수 없음')
                    sources.append(f"페이지 {page}")
                
                answer += f"\n\n📚 **출처**: {', '.join(set(sources))}"
            
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
                    
                    # 기존 벡터 스토어가 있으면 대화 체인 설정
                    if st.session_state.vectorstore and not st.session_state.conversation_chain:
                        self.setup_conversation_chain(api_key)
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
                            self.setup_conversation_chain(api_key)
                            st.success("✅ PDF 처리 완료!")
                            st.rerun()
                        else:
                            st.error("❌ PDF 처리 실패")
                    
                    st.session_state.processing = False
            
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
                        self.setup_conversation_chain(api_key)
                        st.success("✅ 인덱스 로드 완료!")
                        st.rerun()
            
            st.divider()
            
            # 상태 정보
            st.markdown('<p class="sidebar-header">📊 상태</p>', unsafe_allow_html=True)
            
            if st.session_state.vectorstore:
                st.success("✅ PDF가 로드되었습니다")
                if hasattr(st.session_state.vectorstore, 'index'):
                    doc_count = st.session_state.vectorstore.index.ntotal
                    st.info(f"📄 문서 청크: {doc_count}개")
            else:
                st.warning("⚠️ PDF를 업로드해주세요")
            
            if st.session_state.conversation_chain:
                st.success("✅ 챗봇이 준비되었습니다")
            else:
                st.warning("⚠️ 챗봇 설정 필요")
            
            # 대화 초기화 버튼
            if st.button("🗑️ 대화 초기화"):
                st.session_state.messages = []
                if st.session_state.conversation_chain:
                    st.session_state.conversation_chain.memory.clear()
                st.rerun()
    
    def render_main_content(self):
        """메인 콘텐츠 렌더링"""
        # 헤더
        st.markdown('<h1 class="main-header">🤖 PDF ChatGPT</h1>', unsafe_allow_html=True)
        st.markdown("---")
        
        # 시작 안내
        if not st.session_state.vectorstore:
            st.info("""
            👋 **환영합니다!** 
            
            이 애플리케이션을 사용하려면:
            1. 📝 왼쪽 사이드바에서 OpenAI API 키를 입력하세요
            2. 📁 PDF 파일을 업로드하고 처리하세요
            3. 💬 PDF 내용에 대해 질문하세요
            """)
            return
        
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
    chatbot = StreamlitPDFChatBot()
    chatbot.run()


if __name__ == "__main__":
    main()