# advanced/practice3_advanced.py
import streamlit as st
import os
import sys
import hashlib
import mimetypes
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings, Document
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
import logging
import json
import pickle

# 공용 모듈 import
sys.path.append(str(Path(__file__).parent.parent / "shared"))

# 페이지 설정
st.set_page_config(
    page_title="고급 파일 업로드 & 분석",
    page_icon="📂",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileAnalysisSystem:
    """고급 파일 분석 시스템"""
    
    def __init__(self):
        self.api_key = None
        self.file_registry = {}  # 파일 메타데이터 레지스트리
        self.analysis_cache = {}  # 분석 결과 캐시
        self.processing_queue = []  # 처리 대기열
        self.base_upload_dir = Path("../uploads_advanced")
        self.base_upload_dir.mkdir(exist_ok=True)
        
        # 분석 메트릭
        self.analytics = {
            "total_files_processed": 0,
            "total_processing_time": 0,
            "analysis_history": [],
            "error_count": 0,
            "success_rate": 1.0
        }
    
    def initialize_system(self, api_key: str, model_name: str = "gpt-3.5-turbo") -> bool:
        """시스템 초기화"""
        try:
            self.api_key = api_key
            
            # LLM 설정
            Settings.llm = OpenAI(
                model=model_name,
                api_key=api_key,
                temperature=0.1,
                max_tokens=2000
            )
            Settings.embed_model = OpenAIEmbedding(api_key=api_key)
            
            # 기존 파일 레지스트리 로드
            self._load_file_registry()
            
            logger.info(f"File analysis system initialized with {model_name}")
            return True
        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            return False
    
    def _load_file_registry(self):
        """파일 레지스트리 로드"""
        registry_file = self.base_upload_dir / "file_registry.json"
        if registry_file.exists():
            try:
                with open(registry_file, 'r', encoding='utf-8') as f:
                    self.file_registry = json.load(f)
                logger.info(f"Loaded {len(self.file_registry)} files from registry")
            except Exception as e:
                logger.error(f"Failed to load file registry: {e}")
    
    def _save_file_registry(self):
        """파일 레지스트리 저장"""
        registry_file = self.base_upload_dir / "file_registry.json"
        try:
            with open(registry_file, 'w', encoding='utf-8') as f:
                json.dump(self.file_registry, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save file registry: {e}")
    
    def _calculate_file_hash(self, file_content: bytes) -> str:
        """파일 해시 계산 (중복 검사용)"""
        return hashlib.md5(file_content).hexdigest()
    
    def process_uploaded_files(self, uploaded_files: List) -> Dict[str, Any]:
        """업로드된 파일들을 배치 처리"""
        results = {
            "successful": [],
            "failed": [],
            "duplicates": [],
            "total_size": 0,
            "processing_time": 0
        }
        
        start_time = datetime.now()
        
        for uploaded_file in uploaded_files:
            try:
                # 파일 내용 읽기
                file_content = uploaded_file.getbuffer()
                file_hash = self._calculate_file_hash(file_content)
                
                # 중복 검사
                if self._is_duplicate_file(file_hash):
                    results["duplicates"].append(uploaded_file.name)
                    continue
                
                # 파일 저장
                file_info = self._save_uploaded_file(uploaded_file, file_content, file_hash)
                if file_info:
                    results["successful"].append(file_info)
                    results["total_size"] += file_info["size"]
                else:
                    results["failed"].append(uploaded_file.name)
                    
            except Exception as e:
                logger.error(f"Failed to process {uploaded_file.name}: {e}")
                results["failed"].append(uploaded_file.name)
        
        results["processing_time"] = (datetime.now() - start_time).total_seconds()
        
        # 레지스트리 저장
        self._save_file_registry()
        
        return results
    
    def _is_duplicate_file(self, file_hash: str) -> bool:
        """파일 중복 검사"""
        for file_info in self.file_registry.values():
            if file_info.get("hash") == file_hash:
                return True
        return False
    
    def _save_uploaded_file(self, uploaded_file, file_content: bytes, file_hash: str) -> Optional[Dict]:
        """개별 파일 저장 및 메타데이터 생성"""
        try:
            # 파일 경로 생성 (날짜별 폴더)
            date_folder = self.base_upload_dir / datetime.now().strftime("%Y%m%d")
            date_folder.mkdir(exist_ok=True)
            
            # 중복 이름 처리
            file_path = self._get_unique_file_path(date_folder, uploaded_file.name)
            
            # 파일 저장
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            # 메타데이터 생성
            file_info = {
                "filename": uploaded_file.name,
                "stored_path": str(file_path),
                "size": len(file_content),
                "hash": file_hash,
                "mime_type": uploaded_file.type or mimetypes.guess_type(uploaded_file.name)[0],
                "upload_timestamp": datetime.now().isoformat(),
                "status": "uploaded"
            }
            
            # 파일 레지스트리에 추가
            file_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_file.name}"
            self.file_registry[file_id] = file_info
            
            logger.info(f"Saved file: {uploaded_file.name}")
            return file_info
            
        except Exception as e:
            logger.error(f"Failed to save file {uploaded_file.name}: {e}")
            return None
    
    def _get_unique_file_path(self, directory: Path, filename: str) -> Path:
        """중복 파일명 처리"""
        base_path = directory / filename
        if not base_path.exists():
            return base_path
        
        name, ext = os.path.splitext(filename)
        counter = 1
        
        while True:
            new_path = directory / f"{name}_{counter}{ext}"
            if not new_path.exists():
                return new_path
            counter += 1
    
    def analyze_files_batch(self, file_ids: List[str]) -> Dict[str, Any]:
        """배치 파일 분석"""
        results = {
            "analyses": {},
            "summary": {},
            "processing_time": 0,
            "errors": []
        }
        
        start_time = datetime.now()
        
        # 병렬 처리로 분석 수행
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_file = {
                executor.submit(self._analyze_single_file, file_id): file_id 
                for file_id in file_ids
            }
            
            for future in future_to_file:
                file_id = future_to_file[future]
                try:
                    analysis_result = future.result(timeout=300)  # 5분 타임아웃
                    if analysis_result:
                        results["analyses"][file_id] = analysis_result
                except Exception as e:
                    error_msg = f"Analysis failed for {file_id}: {str(e)}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)
        
        # 전체 요약 생성
        if results["analyses"]:
            results["summary"] = self._generate_batch_summary(results["analyses"])
        
        results["processing_time"] = (datetime.now() - start_time).total_seconds()
        
        # 분석 이력 업데이트
        self._update_analytics(results)
        
        return results
    
    def _analyze_single_file(self, file_id: str) -> Optional[Dict]:
        """단일 파일 분석"""
        try:
            file_info = self.file_registry.get(file_id)
            if not file_info:
                return None
            
            # 캐시 확인
            cache_key = f"{file_id}_{file_info['hash']}"
            if cache_key in self.analysis_cache:
                return self.analysis_cache[cache_key]
            
            # 문서 로드
            documents = SimpleDirectoryReader(
                input_files=[file_info["stored_path"]]
            ).load_data()
            
            if not documents:
                return None
            
            # 인덱스 생성
            index = VectorStoreIndex.from_documents(documents)
            query_engine = index.as_query_engine()
            
            # 다양한 분석 수행
            analysis_result = {
                "file_info": file_info,
                "content_analysis": {},
                "metadata_analysis": {},
                "quality_metrics": {}
            }
            
            # 내용 분석
            analysis_queries = {
                "summary": "이 문서의 핵심 내용을 3-5줄로 요약해주세요.",
                "main_topics": "이 문서의 주요 주제나 키워드들을 나열해주세요.",
                "document_type": "이 문서의 유형을 분류해주세요 (예: 보고서, 논문, 매뉴얼, 계약서 등).",
                "language": "이 문서의 주요 언어는 무엇인가요?",
                "complexity": "이 문서의 내용 복잡도를 평가해주세요 (간단/보통/복잡).",
                "key_insights": "이 문서에서 가장 중요한 정보나 인사이트는 무엇인가요?"
            }
            
            for key, query in analysis_queries.items():
                try:
                    response = query_engine.query(query)
                    analysis_result["content_analysis"][key] = str(response)
                except Exception as e:
                    analysis_result["content_analysis"][key] = f"분석 실패: {str(e)}"
            
            # 메타데이터 분석
            doc = documents[0]
            analysis_result["metadata_analysis"] = {
                "character_count": len(doc.text),
                "word_count": len(doc.text.split()),
                "paragraph_count": len(doc.text.split('\n\n')),
                "readability_score": self._calculate_readability_score(doc.text)
            }
            
            # 품질 메트릭
            analysis_result["quality_metrics"] = {
                "completeness": self._assess_completeness(doc.text),
                "structure_quality": self._assess_structure(doc.text),
                "information_density": self._calculate_information_density(doc.text)
            }
            
            # 분석 완료 시간 기록
            analysis_result["analysis_timestamp"] = datetime.now().isoformat()
            
            # 캐시에 저장
            self.analysis_cache[cache_key] = analysis_result
            
            # 파일 상태 업데이트
            self.file_registry[file_id]["status"] = "analyzed"
            self.file_registry[file_id]["last_analysis"] = datetime.now().isoformat()
            
            logger.info(f"Analysis completed for file: {file_info['filename']}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Single file analysis failed for {file_id}: {e}")
            return None
    
    def _calculate_readability_score(self, text: str) -> float:
        """가독성 점수 계산 (간단한 버전)"""
        try:
            sentences = text.split('.')
            words = text.split()
            
            if len(sentences) == 0 or len(words) == 0:
                return 0.0
            
            avg_sentence_length = len(words) / len(sentences)
            # 간단한 가독성 점수 (낮을수록 읽기 쉬움)
            readability = min(100, avg_sentence_length * 2)
            return round(readability, 2)
        except:
            return 0.0
    
    def _assess_completeness(self, text: str) -> float:
        """문서 완성도 평가"""
        # 간단한 휴리스틱: 길이, 구조 요소 존재 여부
        score = 0.0
        
        if len(text) > 100:
            score += 0.3
        if len(text) > 1000:
            score += 0.3
        if any(marker in text.lower() for marker in ['결론', 'conclusion', '요약', 'summary']):
            score += 0.2
        if any(marker in text for marker in ['.', '!', '?']):
            score += 0.2
        
        return min(1.0, score)
    
    def _assess_structure(self, text: str) -> float:
        """문서 구조 품질 평가"""
        score = 0.0
        
        # 단락 구조
        paragraphs = text.split('\n\n')
        if len(paragraphs) > 1:
            score += 0.4
        
        # 제목 구조 (마크다운 스타일)
        if '#' in text:
            score += 0.3
        
        # 목록 구조
        if any(marker in text for marker in ['- ', '* ', '1. ', '2. ']):
            score += 0.3
        
        return min(1.0, score)
    
    def _calculate_information_density(self, text: str) -> float:
        """정보 밀도 계산"""
        try:
            words = text.split()
            unique_words = set(word.lower().strip('.,!?') for word in words)
            
            if len(words) == 0:
                return 0.0
            
            density = len(unique_words) / len(words)
            return round(density, 3)
        except:
            return 0.0
    
    def _generate_batch_summary(self, analyses: Dict) -> Dict:
        """배치 분석 요약 생성"""
        summary = {
            "total_files": len(analyses),
            "document_types": {},
            "languages": {},
            "complexity_distribution": {},
            "average_metrics": {},
            "insights": []
        }
        
        total_chars = 0
        total_words = 0
        readability_scores = []
        
        for analysis in analyses.values():
            content = analysis.get("content_analysis", {})
            metadata = analysis.get("metadata_analysis", {})
            
            # 문서 유형 분포
            doc_type = content.get("document_type", "알 수 없음")
            summary["document_types"][doc_type] = summary["document_types"].get(doc_type, 0) + 1
            
            # 언어 분포
            language = content.get("language", "알 수 없음")
            summary["languages"][language] = summary["languages"].get(language, 0) + 1
            
            # 복잡도 분포
            complexity = content.get("complexity", "알 수 없음")
            summary["complexity_distribution"][complexity] = summary["complexity_distribution"].get(complexity, 0) + 1
            
            # 메트릭 누적
            total_chars += metadata.get("character_count", 0)
            total_words += metadata.get("word_count", 0)
            readability_scores.append(metadata.get("readability_score", 0))
        
        # 평균 계산
        if len(analyses) > 0:
            summary["average_metrics"] = {
                "avg_characters": round(total_chars / len(analyses)),
                "avg_words": round(total_words / len(analyses)),
                "avg_readability": round(sum(readability_scores) / len(readability_scores), 2)
            }
        
        return summary
    
    def _update_analytics(self, results: Dict):
        """분석 통계 업데이트"""
        self.analytics["total_files_processed"] += len(results["analyses"])
        self.analytics["total_processing_time"] += results["processing_time"]
        self.analytics["error_count"] += len(results["errors"])
        
        # 성공률 계산
        total_attempts = self.analytics["total_files_processed"] + self.analytics["error_count"]
        if total_attempts > 0:
            self.analytics["success_rate"] = self.analytics["total_files_processed"] / total_attempts
        
        # 분석 이력에 추가
        self.analytics["analysis_history"].append({
            "timestamp": datetime.now().isoformat(),
            "files_processed": len(results["analyses"]),
            "processing_time": results["processing_time"],
            "errors": len(results["errors"])
        })

# 시스템 인스턴스
@st.cache_resource
def get_analysis_system():
    return FileAnalysisSystem()

def render_analytics_dashboard(system: FileAnalysisSystem):
    """분석 대시보드 렌더링"""
    st.subheader("📊 시스템 분석 대시보드")
    
    # 주요 메트릭
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 처리 파일", system.analytics["total_files_processed"])
    
    with col2:
        avg_time = system.analytics["total_processing_time"] / max(1, system.analytics["total_files_processed"])
        st.metric("평균 처리 시간", f"{avg_time:.2f}초")
    
    with col3:
        st.metric("성공률", f"{system.analytics['success_rate']*100:.1f}%")
    
    with col4:
        st.metric("등록된 파일", len(system.file_registry))
    
    # 처리 이력 차트
    if system.analytics["analysis_history"]:
        df_history = pd.DataFrame(system.analytics["analysis_history"])
        df_history['timestamp'] = pd.to_datetime(df_history['timestamp'])
        
        # 시간별 처리량 차트
        fig = px.line(df_history, x='timestamp', y='files_processed', 
                     title='시간별 파일 처리량')
        st.plotly_chart(fig, use_container_width=True)

def render_file_registry(system: FileAnalysisSystem):
    """파일 레지스트리 표시"""
    st.subheader("📁 파일 레지스트리")
    
    if not system.file_registry:
        st.info("등록된 파일이 없습니다.")
        return
    
    # 파일 목록을 DataFrame으로 변환
    file_data = []
    for file_id, file_info in system.file_registry.items():
        file_data.append({
            "ID": file_id,
            "파일명": file_info["filename"],
            "크기": f"{file_info['size']//1024}KB",
            "상태": file_info["status"],
            "업로드 시간": file_info["upload_timestamp"][:19].replace('T', ' '),
            "MIME 타입": file_info.get("mime_type", "알 수 없음")
        })
    
    df = pd.DataFrame(file_data)
    
    # 필터링 옵션
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.multiselect(
            "상태 필터",
            options=df["상태"].unique(),
            default=df["상태"].unique()
        )
    
    with col2:
        search_term = st.text_input("파일명 검색")
    
    # 필터 적용
    if status_filter:
        df = df[df["상태"].isin(status_filter)]
    
    if search_term:
        df = df[df["파일명"].str.contains(search_term, case=False, na=False)]
    
    # 테이블 표시
    st.dataframe(df, use_container_width=True)

def main():
    st.title("📂 고급 파일 업로드 & 분석 시스템")
    st.markdown("---")
    
    # 시스템 초기화
    analysis_system = get_analysis_system()
    
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
        
        # 모델 선택
        model_name = st.selectbox(
            "분석 모델",
            ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"]
        )
        
        # 시스템 초기화
        if st.button("🚀 시스템 초기화", type="primary"):
            if api_key:
                if analysis_system.initialize_system(api_key, model_name):
                    st.success("✅ 시스템 초기화 완료!")
                    st.session_state.system_ready = True
                else:
                    st.error("시스템 초기화 실패")
            else:
                st.warning("API 키를 입력해주세요.")
        
        # 파일 통계
        if analysis_system.file_registry:
            st.subheader("📊 파일 통계")
            total_files = len(analysis_system.file_registry)
            total_size = sum(info["size"] for info in analysis_system.file_registry.values())
            
            st.metric("총 파일 수", total_files)
            st.metric("총 크기", f"{total_size//1024//1024}MB")
    
    # 메인 컨텐츠
    if not api_key:
        st.warning("⚠️ OpenAI API 키가 필요합니다.")
        return
    
    if not getattr(st.session_state, 'system_ready', False):
        st.info("👈 사이드바에서 시스템을 초기화해주세요.")
        return
    
    # 탭 구성
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📤 파일 업로드", 
        "🔍 파일 분석", 
        "📊 분석 결과", 
        "📁 파일 관리",
        "📈 대시보드"
    ])
    
    with tab1:
        st.header("📤 배치 파일 업로드")
        
        # 파일 업로드
        uploaded_files = st.file_uploader(
            "분석할 파일들을 업로드하세요",
            type=['pdf', 'txt', 'docx', 'md', 'html'],
            accept_multiple_files=True,
            help="최대 10개 파일까지 동시 업로드 가능"
        )
        
        if uploaded_files:
            st.write(f"📁 선택된 파일: {len(uploaded_files)}개")
            
            # 파일 목록 표시
            for file in uploaded_files[:5]:  # 처음 5개만 표시
                st.write(f"- {file.name} ({file.size//1024}KB)")
            
            if len(uploaded_files) > 5:
                st.write(f"... 외 {len(uploaded_files)-5}개")
            
            if st.button("📥 파일 업로드 시작", type="primary"):
                with st.spinner("파일을 처리하는 중..."):
                    results = analysis_system.process_uploaded_files(uploaded_files)
                
                # 결과 표시
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.success(f"✅ 성공: {len(results['successful'])}개")
                
                with col2:
                    if results['failed']:
                        st.error(f"❌ 실패: {len(results['failed'])}개")
                
                with col3:
                    if results['duplicates']:
                        st.warning(f"🔄 중복: {len(results['duplicates'])}개")
                
                st.info(f"⏱️ 처리 시간: {results['processing_time']:.2f}초")
                
                # 실패한 파일들 표시
                if results['failed']:
                    with st.expander("❌ 실패한 파일들"):
                        for filename in results['failed']:
                            st.write(f"- {filename}")
    
    with tab2:
        st.header("🔍 파일 분석")
        
        if analysis_system.file_registry:
            # 분석할 파일 선택
            available_files = {
                file_id: info["filename"] 
                for file_id, info in analysis_system.file_registry.items()
            }
            
            selected_files = st.multiselect(
                "분석할 파일들을 선택하세요:",
                options=list(available_files.keys()),
                format_func=lambda x: available_files[x],
                help="여러 파일을 선택하여 배치 분석 가능"
            )
            
            if selected_files:
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🔍 선택된 파일 분석", type="primary"):
                        with st.spinner("파일들을 분석하는 중..."):
                            analysis_results = analysis_system.analyze_files_batch(selected_files)
                        
                        st.session_state.latest_analysis = analysis_results
                        st.success(f"✅ {len(analysis_results['analyses'])}개 파일 분석 완료!")
                        
                        if analysis_results['errors']:
                            st.error(f"❌ {len(analysis_results['errors'])}개 파일 분석 실패")
                
                with col2:
                    if st.button("📋 모든 파일 분석"):
                        all_file_ids = list(analysis_system.file_registry.keys())
                        with st.spinner("모든 파일을 분석하는 중..."):
                            analysis_results = analysis_system.analyze_files_batch(all_file_ids)
                        
                        st.session_state.latest_analysis = analysis_results
                        st.success("✅ 전체 파일 분석 완료!")
        else:
            st.info("분석할 파일이 없습니다. 먼저 파일을 업로드해주세요.")
    
    with tab3:
        st.header("📊 분석 결과")
        
        if hasattr(st.session_state, 'latest_analysis'):
            results = st.session_state.latest_analysis
            
            # 배치 요약
            if 'summary' in results:
                summary = results['summary']
                
                st.subheader("📋 배치 분석 요약")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("분석된 파일", summary['total_files'])
                
                with col2:
                    avg_chars = summary.get('average_metrics', {}).get('avg_characters', 0)
                    st.metric("평균 문자 수", f"{avg_chars:,}")
                
                with col3:
                    avg_readability = summary.get('average_metrics', {}).get('avg_readability', 0)
                    st.metric("평균 가독성 점수", f"{avg_readability}")
                
                # 분포 차트
                if summary.get('document_types'):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig = px.pie(
                            values=list(summary['document_types'].values()),
                            names=list(summary['document_types'].keys()),
                            title="문서 유형 분포"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        if summary.get('complexity_distribution'):
                            fig = px.bar(
                                x=list(summary['complexity_distribution'].keys()),
                                y=list(summary['complexity_distribution'].values()),
                                title="복잡도 분포"
                            )
                            st.plotly_chart(fig, use_container_width=True)
            
            # 개별 파일 분석 결과
            st.subheader("📄 개별 파일 분석")
            
            for file_id, analysis in results.get('analyses', {}).items():
                with st.expander(f"📄 {analysis['file_info']['filename']}", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**📝 내용 분석**")
                        content_analysis = analysis.get('content_analysis', {})
                        
                        if 'summary' in content_analysis:
                            st.write("**요약:**")
                            st.write(content_analysis['summary'])
                        
                        if 'main_topics' in content_analysis:
                            st.write("**주요 주제:**")
                            st.write(content_analysis['main_topics'])
                    
                    with col2:
                        st.write("**📊 메타데이터**")
                        metadata = analysis.get('metadata_analysis', {})
                        
                        for key, value in metadata.items():
                            st.write(f"**{key}:** {value}")
                        
                        st.write("**품질 메트릭**")
                        quality = analysis.get('quality_metrics', {})
                        for key, value in quality.items():
                            if isinstance(value, float):
                                st.progress(value, text=f"{key}: {value:.2f}")
        else:
            st.info("분석 결과가 없습니다. 파일 분석을 먼저 실행해주세요.")
    
    with tab4:
        render_file_registry(analysis_system)
    
    with tab5:
        render_analytics_dashboard(analysis_system)

if __name__ == "__main__":
    main()