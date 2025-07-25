# advanced/practice1_advanced.py
import streamlit as st
import os
import sys
from pathlib import Path
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
import logging
from datetime import datetime

# 공용 모듈 import
sys.path.append(str(Path(__file__).parent.parent / "shared"))

# 페이지 설정
st.set_page_config(
    page_title="고급 문서 QA",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentQASystem:
    """고급 문서 QA 시스템 클래스"""
    
    def __init__(self):
        self.api_key = None
        self.index = None
        self.query_engine = None
        self.docs_info = {"count": 0, "total_size": 0, "last_updated": None}
    
    def initialize_llama_index(self, api_key: str) -> bool:
        """LlamaIndex 초기화"""
        try:
            self.api_key = api_key
            
            # LLM 설정 (모델 선택 가능)
            model_name = st.session_state.get('model_name', 'gpt-3.5-turbo')
            Settings.llm = OpenAI(model=model_name, api_key=api_key, temperature=0.1)
            Settings.embed_model = OpenAIEmbedding(api_key=api_key)
            
            logger.info(f"LlamaIndex initialized with model: {model_name}")
            return True
        except Exception as e:
            logger.error(f"LlamaIndex initialization failed: {e}")
            st.error(f"초기화 실패: {e}")
            return False
    
    def load_documents(self, docs_folder: str, file_extensions: list = None) -> tuple:
        """문서 로드 및 검증"""
        try:
            if not os.path.exists(docs_folder):
                return None, f"폴더를 찾을 수 없습니다: {docs_folder}"
            
            # 파일 필터링
            if file_extensions:
                reader = SimpleDirectoryReader(
                    docs_folder,
                    required_exts=file_extensions
                )
            else:
                reader = SimpleDirectoryReader(docs_folder)
            
            documents = reader.load_data()
            
            if not documents:
                return None, f"지원되는 문서가 없습니다: {docs_folder}"
            
            # 문서 정보 수집
            total_size = sum(len(doc.text) for doc in documents)
            self.docs_info = {
                "count": len(documents),
                "total_size": total_size,
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            logger.info(f"Loaded {len(documents)} documents, total size: {total_size}")
            return documents, f"성공적으로 {len(documents)}개 문서를 로드했습니다."
            
        except Exception as e:
            logger.error(f"Document loading failed: {e}")
            return None, f"문서 로드 실패: {e}"
    
    def create_index(self, documents) -> bool:
        """인덱스 생성"""
        try:
            # 청크 설정
            chunk_size = st.session_state.get('chunk_size', 1024)
            chunk_overlap = st.session_state.get('chunk_overlap', 50)
            
            from llama_index.core.node_parser import SentenceSplitter
            splitter = SentenceSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            
            # 인덱스 생성
            self.index = VectorStoreIndex.from_documents(
                documents,
                transformations=[splitter]
            )
            
            # 쿼리 엔진 설정
            similarity_top_k = st.session_state.get('similarity_top_k', 3)
            self.query_engine = self.index.as_query_engine(
                similarity_top_k=similarity_top_k,
                response_mode="tree_summarize"
            )
            
            logger.info("Index and query engine created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Index creation failed: {e}")
            st.error(f"인덱스 생성 실패: {e}")
            return False
    
    def query(self, question: str) -> tuple:
        """질문 처리"""
        try:
            if not self.query_engine:
                return None, "시스템이 초기화되지 않았습니다."
            
            response = self.query_engine.query(question)
            
            # 응답 정보 수집
            response_info = {
                "answer": str(response),
                "sources": []
            }
            
            if hasattr(response, 'source_nodes') and response.source_nodes:
                for node in response.source_nodes:
                    source_info = {
                        "text": node.text[:300] + "...",
                        "score": getattr(node, 'score', 0),
                        "metadata": node.metadata
                    }
                    response_info["sources"].append(source_info)
            
            logger.info(f"Query processed: {question[:50]}...")
            return response_info, "성공"
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return None, f"질문 처리 실패: {e}"

# QA 시스템 인스턴스
@st.cache_resource
def get_qa_system():
    return DocumentQASystem()

def main():
    st.title("📚 고급 문서 QA 시스템")
    st.markdown("---")
    
    # 시스템 초기화
    qa_system = get_qa_system()
    
    # 사이드바 설정
    with st.sidebar:
        st.header("⚙️ 시스템 설정")
        
        # API 키 입력
        try:
            api_key = st.secrets.get("OPENAI_API_KEY", None)
        except:
            api_key = None
        
        if not api_key:
            api_key = st.text_input(
                "OpenAI API Key",
                type="password",
                help="OpenAI API 키를 입력하세요"
            )
        
        # 모델 선택
        model_name = st.selectbox(
            "LLM 모델 선택",
            ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"],
            key="model_name"
        )
        
        # 문서 설정
        st.subheader("📁 문서 설정")
        docs_folder = st.text_input(
            "문서 폴더 경로",
            value="../docs",
            help="분석할 문서들이 있는 폴더"
        )
        
        # 파일 확장자 필터
        st.write("지원할 파일 형식:")
        col1, col2 = st.columns(2)
        with col1:
            pdf_support = st.checkbox("PDF", value=True)
            txt_support = st.checkbox("TXT", value=True)
        with col2:
            docx_support = st.checkbox("DOCX", value=True)
            md_support = st.checkbox("MD", value=True)
        
        file_extensions = []
        if pdf_support: file_extensions.append(".pdf")
        if txt_support: file_extensions.append(".txt")
        if docx_support: file_extensions.append(".docx")
        if md_support: file_extensions.append(".md")
        
        # 고급 설정
        with st.expander("🔧 고급 설정"):
            chunk_size = st.slider("청크 크기", 512, 2048, 1024, key="chunk_size")
            chunk_overlap = st.slider("청크 겹침", 0, 200, 50, key="chunk_overlap")
            similarity_top_k = st.slider("유사도 검색 수", 1, 10, 3, key="similarity_top_k")
        
        # 문서 로드 버튼
        if st.button("📁 문서 로드 & 인덱싱", type="primary"):
            if api_key:
                if qa_system.initialize_llama_index(api_key):
                    with st.spinner("문서를 로드하고 인덱싱하는 중..."):
                        # 문서 로드
                        documents, load_message = qa_system.load_documents(docs_folder, file_extensions)
                        
                        if documents:
                            st.success(load_message)
                            
                            # 인덱스 생성
                            if qa_system.create_index(documents):
                                st.success("✅ 인덱싱 완료!")
                                st.session_state.system_ready = True
                            else:
                                st.error("인덱싱 실패")
                        else:
                            st.error(load_message)
            else:
                st.warning("API 키를 입력해주세요.")
        
        # 시스템 정보
        if qa_system.docs_info["count"] > 0:
            st.subheader("📊 시스템 정보")
            st.metric("문서 수", qa_system.docs_info["count"])
            st.metric("총 텍스트 크기", f"{qa_system.docs_info['total_size']:,} 문자")
            st.caption(f"마지막 업데이트: {qa_system.docs_info['last_updated']}")
    
    # 메인 컨텐츠
    if not api_key:
        st.warning("⚠️ OpenAI API 키가 필요합니다.")
        st.markdown("""
        ### 🔑 API 키 설정 방법:
        1. [OpenAI Platform](https://platform.openai.com/api-keys)에서 API 키 생성
        2. 사이드바에 API 키 입력
        3. 문서 폴더 설정 후 '문서 로드 & 인덱싱' 클릭
        """)
        return
    
    if not getattr(st.session_state, 'system_ready', False):
        st.info("👈 사이드바에서 문서를 로드하고 인덱싱해주세요.")
        st.markdown("""
        ### 📋 시스템 특징:
        - **다중 모델 지원**: GPT-3.5, GPT-4 등 선택 가능
        - **고급 청킹**: 문서를 최적 크기로 분할
        - **유사도 검색**: 관련도 높은 문서 청크 우선 검색
        - **소스 추적**: 답변의 출처 문서 표시
        - **성능 최적화**: 캐싱 및 효율적 인덱싱
        
        ### 📁 지원 파일 형식:
        - PDF (.pdf) - Adobe PDF 문서
        - 텍스트 (.txt) - 평문 텍스트
        - Word (.docx) - Microsoft Word 문서  
        - Markdown (.md) - 마크다운 문서
        """)
        return
    
    # 질문 답변 섹션
    st.markdown("### 💬 문서에 대해 질문하세요")
    
    # 미리 정의된 질문 버튼들
    st.markdown("**💡 예시 질문:**")
    col1, col2, col3, col4 = st.columns(4)
    
    example_questions = [
        "문서의 주요 내용은?",
        "핵심 키워드는?", 
        "결론이나 요약은?",
        "가장 중요한 정보는?"
    ]
    
    for i, (col, question) in enumerate(zip([col1, col2, col3, col4], example_questions)):
        with col:
            if st.button(question, key=f"example_{i}"):
                st.session_state.example_question = question
    
    # 질문 입력
    question = st.text_area(
        "질문을 입력하세요:",
        value=getattr(st.session_state, 'example_question', ''),
        placeholder="예: 이 문서에서 가장 중요한 개념은 무엇인가요?",
        height=100,
        key="main_question"
    )
    
    # 질문 처리
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔍 질문하기", type="primary", disabled=not question):
            process_question = True
        else:
            process_question = False
    
    with col2:
        if st.button("🗑️ 질문 지우기"):
            st.session_state.example_question = ""
            st.session_state.main_question = ""
            st.rerun()
    
    if process_question and question:
        with st.spinner("답변을 생성하는 중..."):
            response_info, status = qa_system.query(question)
        
        if response_info:
            # 답변 표시
            st.markdown("### 📝 답변")
            st.write(response_info["answer"])
            
            # 소스 정보 표시
            if response_info["sources"]:
                st.markdown("### 📄 참조 문서")
                
                for i, source in enumerate(response_info["sources"]):
                    with st.expander(f"소스 {i+1} (유사도: {source['score']:.3f})", expanded=False):
                        st.write("**내용:**")
                        st.write(source["text"])
                        
                        if source["metadata"]:
                            st.write("**메타데이터:**")
                            st.json(source["metadata"])
            
            # 질문 기록 (선택사항)
            if 'question_history' not in st.session_state:
                st.session_state.question_history = []
            
            st.session_state.question_history.append({
                "question": question,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "answer_length": len(response_info["answer"])
            })
            
            # 최근 질문 기록 표시
            if len(st.session_state.question_history) > 1:
                with st.expander("🕒 최근 질문 기록"):
                    for i, record in enumerate(reversed(st.session_state.question_history[-5:])):
                        st.write(f"**{record['timestamp']}:** {record['question']}")
                        st.caption(f"답변 길이: {record['answer_length']}자")
                        if i < 4: st.divider()
        else:
            st.error(status)

if __name__ == "__main__":
    main()