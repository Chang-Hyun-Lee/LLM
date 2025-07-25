# advanced/practice2_advanced.py
import streamlit as st
import os
import sys
import json
import pickle
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.chat_engine.types import ChatMode
import logging

# 공용 모듈 import
sys.path.append(str(Path(__file__).parent.parent / "shared"))

# 페이지 설정
st.set_page_config(
    page_title="고급 멀티턴 채팅",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedChatSystem:
    """고급 멀티턴 채팅 시스템"""
    
    def __init__(self):
        self.api_key = None
        self.index = None
        self.chat_engines = {}  # 다중 채팅 엔진 지원
        self.conversation_history = []
        self.system_metrics = {
            "total_questions": 0,
            "average_response_time": 0,
            "session_start": datetime.now()
        }
    
    def initialize_system(self, api_key: str, model_name: str = "gpt-3.5-turbo") -> bool:
        """시스템 초기화"""
        try:
            self.api_key = api_key
            
            # LLM 설정
            Settings.llm = OpenAI(
                model=model_name, 
                api_key=api_key,
                temperature=st.session_state.get('temperature', 0.1),
                max_tokens=st.session_state.get('max_tokens', 1000)
            )
            Settings.embed_model = OpenAIEmbedding(api_key=api_key)
            
            logger.info(f"System initialized with model: {model_name}")
            return True
        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            st.error(f"시스템 초기화 실패: {e}")
            return False
    
    def load_and_index_documents(self, docs_folder: str) -> tuple:
        """문서 로드 및 인덱싱"""
        try:
            if not os.path.exists(docs_folder):
                return False, f"폴더를 찾을 수 없습니다: {docs_folder}"
            
            # 문서 로드
            documents = SimpleDirectoryReader(docs_folder).load_data()
            if not documents:
                return False, "문서가 없습니다."
            
            # 문서 메타데이터 강화
            for i, doc in enumerate(documents):
                doc.metadata.update({
                    'doc_id': i,
                    'load_timestamp': datetime.now().isoformat(),
                    'char_count': len(doc.text),
                    'word_count': len(doc.text.split())
                })
            
            # 인덱스 생성
            from llama_index.core.node_parser import SentenceSplitter
            
            chunk_size = st.session_state.get('chunk_size', 1024)
            chunk_overlap = st.session_state.get('chunk_overlap', 50)
            
            splitter = SentenceSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            
            self.index = VectorStoreIndex.from_documents(
                documents,
                transformations=[splitter]
            )
            
            # 인덱스 정보 저장
            st.session_state.index_info = {
                'document_count': len(documents),
                'total_chars': sum(len(doc.text) for doc in documents),
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            logger.info(f"Indexed {len(documents)} documents")
            return True, f"성공적으로 {len(documents)}개 문서를 인덱싱했습니다."
            
        except Exception as e:
            logger.error(f"Document indexing failed: {e}")
            return False, f"인덱싱 실패: {str(e)}"
    
    def create_chat_engine(
        self, 
        engine_name: str,
        chat_mode: str = "context",
        memory_limit: int = 1500,
        system_prompt: str = None
    ) -> bool:
        """채팅 엔진 생성"""
        try:
            if not self.index:
                return False
            
            # 메모리 설정
            memory = ChatMemoryBuffer.from_defaults(token_limit=memory_limit)
            
            # 시스템 프롬프트 설정
            if not system_prompt:
                system_prompt = st.session_state.get('custom_system_prompt', self._default_system_prompt())
            
            # 채팅 모드 매핑
            mode_mapping = {
                "context": ChatMode.CONTEXT,
                "condense_question": ChatMode.CONDENSE_QUESTION,
                "react": ChatMode.REACT
            }
            
            # 채팅 엔진 생성
            self.chat_engines[engine_name] = self.index.as_chat_engine(
                chat_mode=mode_mapping.get(chat_mode, ChatMode.CONTEXT),
                memory=memory,
                system_prompt=system_prompt,
                similarity_top_k=st.session_state.get('similarity_top_k', 3)
            )
            
            logger.info(f"Created chat engine: {engine_name}")
            return True
            
        except Exception as e:
            logger.error(f"Chat engine creation failed: {e}")
            st.error(f"채팅 엔진 생성 실패: {e}")
            return False
    
    def _default_system_prompt(self) -> str:
        """기본 시스템 프롬프트"""
        return """당신은 문서 전문가입니다. 다음 지침을 따라주세요:

1. 문서 내용을 바탕으로 정확하고 상세한 답변을 제공하세요.
2. 문서에 없는 내용은 추측하지 말고 명확히 '문서에서 찾을 수 없음'을 표시하세요.
3. 이전 대화 맥락을 고려하여 일관성 있는 답변을 하세요.
4. 가능한 경우 구체적인 예시나 인용문을 포함하세요.
5. 사용자의 후속 질문에 대해 맥락을 유지하며 답변하세요."""
    
    def chat(self, message: str, engine_name: str = "default") -> tuple:
        """채팅 처리"""
        try:
            start_time = datetime.now()
            
            if engine_name not in self.chat_engines:
                return None, "채팅 엔진이 준비되지 않았습니다."
            
            # 채팅 엔진으로 응답 생성
            response = self.chat_engines[engine_name].chat(message)
            
            # 응답 시간 계산
            response_time = (datetime.now() - start_time).total_seconds()
            
            # 대화 기록 저장
            conversation_entry = {
                'timestamp': datetime.now().isoformat(),
                'user_message': message,
                'assistant_response': str(response),
                'response_time': response_time,
                'engine_used': engine_name
            }
            
            # 소스 정보 추가
            if hasattr(response, 'source_nodes') and response.source_nodes:
                conversation_entry['sources'] = [
                    {
                        'text': node.text[:200] + "...",
                        'score': getattr(node, 'score', 0),
                        'metadata': node.metadata
                    }
                    for node in response.source_nodes
                ]
            
            self.conversation_history.append(conversation_entry)
            
            # 메트릭 업데이트
            self._update_metrics(response_time)
            
            logger.info(f"Chat processed in {response_time:.2f}s")
            return conversation_entry, "성공"
            
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            return None, f"채팅 실패: {str(e)}"
    
    def _update_metrics(self, response_time: float):
        """메트릭 업데이트"""
        self.system_metrics["total_questions"] += 1
        
        # 평균 응답 시간 계산
        current_avg = self.system_metrics["average_response_time"]
        total_questions = self.system_metrics["total_questions"]
        
        new_avg = ((current_avg * (total_questions - 1)) + response_time) / total_questions
        self.system_metrics["average_response_time"] = new_avg
    
    def export_conversation(self) -> str:
        """대화 내용 JSON으로 내보내기"""
        try:
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'system_metrics': self.system_metrics,
                'conversation_history': self.conversation_history
            }
            return json.dumps(export_data, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return f"내보내기 실패: {str(e)}"
    
    def reset_conversation(self, engine_name: str = None):
        """대화 초기화"""
        if engine_name and engine_name in self.chat_engines:
            # 특정 엔진만 초기화
            del self.chat_engines[engine_name]
        else:
            # 전체 초기화
            self.chat_engines.clear()
            self.conversation_history.clear()
            self.system_metrics = {
                "total_questions": 0,
                "average_response_time": 0,
                "session_start": datetime.now()
            }

# 시스템 인스턴스
@st.cache_resource
def get_chat_system():
    return AdvancedChatSystem()

def main():
    st.title("💬 고급 멀티턴 대화 시스템")
    st.markdown("---")
    
    # 시스템 초기화
    chat_system = get_chat_system()
    
    # 세션 상태 초기화
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'current_engine' not in st.session_state:
        st.session_state.current_engine = "default"
    
    # 사이드바 설정
    with st.sidebar:
        st.header("⚙️ 시스템 설정")
        
        # API 키 입력
        try:
            api_key = st.secrets.get("OPENAI_API_KEY", None)
        except:
            api_key = None
        
        if not api_key:
            api_key = st.text_input("OpenAI API Key", type="password")
        
        # 모델 설정
        col1, col2 = st.columns(2)
        with col1:
            model_name = st.selectbox(
                "모델 선택",
                ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"],
                key="model_name"
            )
        
        with col2:
            temperature = st.slider("Temperature", 0.0, 1.0, 0.1, 0.1, key="temperature")
        
        max_tokens = st.slider("Max Tokens", 100, 2000, 1000, 100, key="max_tokens")
        
        # 문서 설정
        st.subheader("📁 문서 설정")
        docs_folder = st.text_input("문서 폴더", value="../docs")
        
        # 고급 설정
        with st.expander("🔧 고급 설정"):
            chunk_size = st.slider("청크 크기", 512, 2048, 1024, key="chunk_size")
            chunk_overlap = st.slider("청크 겹침", 0, 200, 50, key="chunk_overlap")
            similarity_top_k = st.slider("유사도 검색 수", 1, 10, 3, key="similarity_top_k")
        
        # 채팅 엔진 설정
        st.subheader("🤖 채팅 엔진")
        chat_mode = st.selectbox(
            "채팅 모드",
            ["context", "condense_question", "react"],
            help="context: 문맥 기반, condense_question: 질문 압축, react: 추론 기반"
        )
        
        memory_limit = st.slider("메모리 제한", 500, 3000, 1500)
        
        # 사용자 정의 시스템 프롬프트
        with st.expander("📝 시스템 프롬프트 설정"):
            custom_prompt = st.text_area(
                "사용자 정의 시스템 프롬프트",
                value="",
                height=150,
                help="비워두면 기본 프롬프트 사용",
                key="custom_system_prompt"
            )
        
        # 초기화 버튼
        if st.button("🚀 시스템 초기화", type="primary"):
            if api_key:
                if chat_system.initialize_system(api_key, model_name):
                    with st.spinner("문서를 인덱싱하는 중..."):
                        success, message = chat_system.load_and_index_documents(docs_folder)
                        
                        if success:
                            st.success(message)
                            
                            # 채팅 엔진 생성
                            if chat_system.create_chat_engine(
                                "default", 
                                chat_mode, 
                                memory_limit,
                                custom_prompt or None
                            ):
                                st.success("✅ 시스템 준비 완료!")
                                st.session_state.system_ready = True
                        else:
                            st.error(message)
            else:
                st.warning("API 키를 입력해주세요.")
        
        # 시스템 정보
        if hasattr(st.session_state, 'index_info'):
            st.subheader("📊 시스템 정보")
            info = st.session_state.index_info
            st.metric("문서 수", info['document_count'])
            st.metric("총 문자 수", f"{info['total_chars']:,}")
            st.caption(f"인덱싱: {info['created_at']}")
            
            # 대화 통계
            metrics = chat_system.system_metrics
            col1, col2 = st.columns(2)
            with col1:
                st.metric("총 질문 수", metrics['total_questions'])
            with col2:
                avg_time = metrics['average_response_time']
                st.metric("평균 응답시간", f"{avg_time:.2f}초")
        
        # 대화 관리
        st.subheader("🔄 대화 관리")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ 대화 초기화"):
                st.session_state.messages = []
                chat_system.reset_conversation()
                st.rerun()
        
        with col2:
            if st.button("💾 대화 내보내기"):
                if chat_system.conversation_history:
                    exported_data = chat_system.export_conversation()
                    st.download_button(
                        "📥 JSON 다운로드",
                        data=exported_data,
                        file_name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
    
    # 메인 컨텐츠
    if not api_key:
        st.warning("⚠️ OpenAI API 키가 필요합니다.")
        st.markdown("""
        ### 🔑 API 키 설정 후 다음 기능들을 사용할 수 있습니다:
        - **다중 채팅 모드**: Context, Condense Question, ReAct
        - **고급 메모리 관리**: 대화 맥락 유지
        - **실시간 메트릭**: 응답 시간, 질문 수 추적
        - **대화 내보내기**: JSON 형태로 대화 기록 저장
        - **사용자 정의 프롬프트**: AI 응답 스타일 커스터마이징
        """)
        return
    
    if not getattr(st.session_state, 'system_ready', False):
        st.info("👈 사이드바에서 시스템을 초기화해주세요.")
        
        # 기능 소개
        tab1, tab2, tab3 = st.tabs(["🚀 주요 기능", "🎯 채팅 모드", "📊 고급 기능"])
        
        with tab1:
            st.markdown("""
            ### 🌟 고급 멀티턴 대화 시스템의 특징:
            
            **💬 스마트 대화 관리**
            - 대화 맥락을 기억하며 일관성 있는 답변
            - 다양한 채팅 모드 지원
            - 실시간 응답 시간 모니터링
            
            **🧠 지능형 문서 이해**  
            - 문서 전체를 이해하고 연관성 분석
            - 정확한 소스 추적 및 인용
            - 청크 크기 최적화로 정확도 향상
            
            **🔧 커스터마이징**
            - 사용자 정의 시스템 프롬프트
            - 모델 선택 및 파라미터 조정
            - 메모리 크기 조절
            """)
        
        with tab2:
            st.markdown("""
            ### 🎯 채팅 모드 설명:
            
            **Context 모드**
            - 문서 맥락을 그대로 유지
            - 일반적인 질문답변에 적합
            - 빠른 응답 속도
            
            **Condense Question 모드**
            - 이전 대화를 고려해 질문을 재구성
            - 복잡한 연속 질문에 효과적
            - 대화 흐름 최적화
            
            **ReAct 모드**
            - 추론과 행동을 결합
            - 복잡한 문제 해결에 적합
            - 단계별 사고 과정 표시
            """)
        
        with tab3:
            st.markdown("""
            ### 📊 고급 기능들:
            
            **실시간 메트릭**
            - 총 질문 수 추적
            - 평균 응답 시간 계산
            - 시스템 성능 모니터링
            
            **대화 관리**
            - 대화 기록 JSON 내보내기
            - 선택적 대화 초기화
            - 시간대별 대화 분석
            
            **소스 추적**
            - 답변 출처 문서 표시
            - 유사도 점수 제공
            - 메타데이터 정보 포함
            """)
        
        return
    
    # 채팅 인터페이스
    st.markdown("### 💬 문서 기반 대화")
    
    # 채팅 히스토리 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # 소스 정보 표시 (Assistant 메시지의 경우)
            if message["role"] == "assistant" and "sources" in message:
                with st.expander("📄 참조 문서", expanded=False):
                    for i, source in enumerate(message["sources"]):
                        st.write(f"**소스 {i+1}** (유사도: {source['score']:.3f})")
                        st.write(source["text"])
                        if source["metadata"]:
                            st.caption(f"메타데이터: {source['metadata']}")
                        st.divider()
    
    # 사용자 입력
    if prompt := st.chat_input("메시지를 입력하세요..."):
        # 사용자 메시지 추가
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # AI 응답 생성
        with st.chat_message("assistant"):
            with st.spinner("답변을 생성하는 중..."):
                result, status = chat_system.chat(prompt, st.session_state.current_engine)
            
            if result:
                # 답변 표시
                st.markdown(result["assistant_response"])
                
                # 메시지에 소스 정보 포함해서 저장
                assistant_message = {
                    "role": "assistant", 
                    "content": result["assistant_response"]
                }
                
                if "sources" in result:
                    assistant_message["sources"] = result["sources"]
                    
                    # 소스 정보 표시
                    with st.expander("📄 참조 문서", expanded=False):
                        for i, source in enumerate(result["sources"]):
                            st.write(f"**소스 {i+1}** (유사도: {source['score']:.3f})")
                            st.write(source["text"])
                            if source["metadata"]:
                                st.caption(f"메타데이터: {source['metadata']}")
                            st.divider()
                
                st.session_state.messages.append(assistant_message)
                
                # 응답 시간 표시
                st.caption(f"⏱️ 응답 시간: {result['response_time']:.2f}초")
                
            else:
                error_msg = f"답변 생성 실패: {status}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

if __name__ == "__main__":
    main()