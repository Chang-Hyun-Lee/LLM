# advanced/practice4_advanced.py
import streamlit as st
import os
import sys
import json
import pickle
import shutil
import zipfile
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from concurrent.futures import ThreadPoolExecutor
import schedule
import threading
import time

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings, StorageContext, load_index_from_storage
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.memory import ChatMemoryBuffer
import logging

# 공용 모듈 import
sys.path.append(str(Path(__file__).parent.parent / "shared"))

# 페이지 설정
st.set_page_config(
    page_title="고급 파일 관리 & QA",
    page_icon="🗂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnterpriseFileManager:
    """엔터프라이즈급 파일 관리 시스템"""
    
    def __init__(self):
        self.base_dir = Path("../file_management_enterprise")
        self.base_dir.mkdir(exist_ok=True)
        
        # 하위 디렉토리 구조
        self.files_dir = self.base_dir / "files"
        self.indices_dir = self.base_dir / "indices"
        self.backups_dir = self.base_dir / "backups"
        self.logs_dir = self.base_dir / "logs"
        self.exports_dir = self.base_dir / "exports"
        
        for dir_path in [self.files_dir, self.indices_dir, self.backups_dir, self.logs_dir, self.exports_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # 데이터베이스 초기화
        self.db_path = self.base_dir / "file_management.db"
        self._init_database()
        
        # 시스템 설정
        self.api_key = None
        self.unified_index = None
        self.chat_engines = {}
        
        # 태깅 시스템
        self.tag_system = TagSystem(self.db_path)
        
        # 워크플로우 매니저
        self.workflow_manager = WorkflowManager(self)
        
        # 성능 모니터
        self.performance_monitor = PerformanceMonitor()
    
    def _init_database(self):
        """SQLite 데이터베이스 초기화"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 파일 메타데이터 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    file_path TEXT UNIQUE NOT NULL,
                    file_hash TEXT,
                    size INTEGER,
                    mime_type TEXT,
                    upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'uploaded',
                    version INTEGER DEFAULT 1,
                    parent_id INTEGER,
                    metadata TEXT,
                    FOREIGN KEY (parent_id) REFERENCES files (id)
                )
            ''')
            
            # 태그 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    color TEXT DEFAULT '#007acc',
                    description TEXT
                )
            ''')
            
            # 파일-태그 관계 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS file_tags (
                    file_id INTEGER,
                    tag_id INTEGER,
                    PRIMARY KEY (file_id, tag_id),
                    FOREIGN KEY (file_id) REFERENCES files (id),
                    FOREIGN KEY (tag_id) REFERENCES tags (id)
                )
            ''')
            
            # 워크플로우 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS workflows (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    trigger_type TEXT,
                    trigger_config TEXT,
                    action_type TEXT,
                    action_config TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 활동 로그 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    file_id INTEGER,
                    user_id TEXT,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (file_id) REFERENCES files (id)
                )
            ''')
            
            conn.commit()
    
    def initialize_system(self, api_key: str, model_name: str = "gpt-3.5-turbo") -> bool:
        """시스템 초기화"""
        try:
            self.api_key = api_key
            
            # LlamaIndex 설정
            Settings.llm = OpenAI(model=model_name, api_key=api_key, temperature=0.1)
            Settings.embed_model = OpenAIEmbedding(api_key=api_key)
            
            # 기존 인덱스 로드 시도
            self._load_unified_index()
            
            logger.info(f"Enterprise file manager initialized with {model_name}")
            return True
        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            return False
    
    def _load_unified_index(self):
        """통합 인덱스 로드"""
        index_path = self.indices_dir / "unified_index"
        if index_path.exists():
            try:
                storage_context = StorageContext.from_defaults(persist_dir=str(index_path))
                self.unified_index = load_index_from_storage(storage_context)
                logger.info("Loaded existing unified index")
            except Exception as e:
                logger.warning(f"Failed to load existing index: {e}")
    
    def add_file(self, uploaded_file, tags: List[str] = None, metadata: Dict = None) -> Tuple[bool, str]:
        """파일 추가"""
        try:
            # 파일 저장
            file_content = uploaded_file.getbuffer()
            file_hash = self._calculate_hash(file_content)
            
            # 중복 검사
            if self._is_duplicate(file_hash):
                return False, "중복된 파일입니다."
            
            # 파일 저장 경로 생성
            file_path = self._get_unique_path(uploaded_file.name)
            
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            # 데이터베이스에 메타데이터 저장
            file_id = self._save_file_metadata(
                filename=uploaded_file.name,
                file_path=str(file_path),
                file_hash=file_hash,
                size=uploaded_file.size,
                mime_type=uploaded_file.type,
                metadata=metadata
            )
            
            # 태그 추가
            if tags:
                self.tag_system.add_tags_to_file(file_id, tags)
            
            # 활동 로그
            self._log_activity("file_upload", file_id, details=f"Uploaded {uploaded_file.name}")
            
            # 인덱스 업데이트 (백그라운드에서)
            self._schedule_index_update()
            
            logger.info(f"File added: {uploaded_file.name}")
            return True, f"파일이 성공적으로 추가되었습니다. ID: {file_id}"
            
        except Exception as e:
            logger.error(f"Failed to add file: {e}")
            return False, f"파일 추가 실패: {str(e)}"
    
    def _calculate_hash(self, content: bytes) -> str:
        """파일 해시 계산"""
        import hashlib
        return hashlib.sha256(content).hexdigest()
    
    def _is_duplicate(self, file_hash: str) -> bool:
        """중복 파일 검사"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM files WHERE file_hash = ?", (file_hash,))
            return cursor.fetchone() is not None
    
    def _get_unique_path(self, filename: str) -> Path:
        """고유한 파일 경로 생성"""
        base_path = self.files_dir / filename
        
        if not base_path.exists():
            return base_path
        
        name, ext = os.path.splitext(filename)
        counter = 1
        
        while True:
            new_path = self.files_dir / f"{name}_{counter}{ext}"
            if not new_path.exists():
                return new_path
            counter += 1
    
    def _save_file_metadata(self, **kwargs) -> int:
        """파일 메타데이터 저장"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            metadata_json = json.dumps(kwargs.get('metadata', {}))
            
            cursor.execute('''
                INSERT INTO files (filename, file_path, file_hash, size, mime_type, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                kwargs['filename'],
                kwargs['file_path'],
                kwargs['file_hash'],
                kwargs['size'],
                kwargs['mime_type'],
                metadata_json
            ))
            
            file_id = cursor.lastrowid
            conn.commit()
            return file_id
    
    def get_files(self, filters: Dict = None) -> pd.DataFrame:
        """파일 목록 조회"""
        with sqlite3.connect(self.db_path) as conn:
            query = '''
                SELECT f.*, GROUP_CONCAT(t.name) as tags
                FROM files f
                LEFT JOIN file_tags ft ON f.id = ft.file_id
                LEFT JOIN tags t ON ft.tag_id = t.id
            '''
            
            conditions = []
            params = []
            
            if filters:
                if 'status' in filters:
                    conditions.append("f.status IN ({})".format(','.join(['?'] * len(filters['status']))))
                    params.extend(filters['status'])
                
                if 'tags' in filters:
                    tag_conditions = "t.name IN ({})".format(','.join(['?'] * len(filters['tags'])))
                    conditions.append(tag_conditions)
                    params.extend(filters['tags'])
                
                if 'date_from' in filters:
                    conditions.append("f.upload_timestamp >= ?")
                    params.append(filters['date_from'])
                
                if 'date_to' in filters:
                    conditions.append("f.upload_timestamp <= ?")
                    params.append(filters['date_to'])
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " GROUP BY f.id ORDER BY f.upload_timestamp DESC"
            
            df = pd.read_sql_query(query, conn, params=params)
            return df
    
    def delete_file(self, file_id: int) -> Tuple[bool, str]:
        """파일 삭제"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 파일 정보 조회
                cursor.execute("SELECT filename, file_path FROM files WHERE id = ?", (file_id,))
                result = cursor.fetchone()
                
                if not result:
                    return False, "파일을 찾을 수 없습니다."
                
                filename, file_path = result
                
                # 물리적 파일 삭제
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                # 데이터베이스에서 삭제
                cursor.execute("DELETE FROM file_tags WHERE file_id = ?", (file_id,))
                cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
                conn.commit()
                
                # 활동 로그
                self._log_activity("file_delete", file_id, details=f"Deleted {filename}")
                
                # 인덱스 업데이트
                self._schedule_index_update()
                
                logger.info(f"File deleted: {filename}")
                return True, f"파일이 삭제되었습니다: {filename}"
                
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return False, f"파일 삭제 실패: {str(e)}"
    
    def create_backup(self) -> Tuple[bool, str]:
        """시스템 백업 생성"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backups_dir / f"backup_{timestamp}.zip"
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 데이터베이스 백업
                zipf.write(self.db_path, "database.db")
                
                # 파일들 백업
                for file_path in self.files_dir.rglob("*"):
                    if file_path.is_file():
                        arcname = f"files/{file_path.relative_to(self.files_dir)}"
                        zipf.write(file_path, arcname)
                
                # 인덱스 백업
                if self.indices_dir.exists():
                    for index_path in self.indices_dir.rglob("*"):
                        if index_path.is_file():
                            arcname = f"indices/{index_path.relative_to(self.indices_dir)}"
                            zipf.write(index_path, arcname)
            
            logger.info(f"Backup created: {backup_path}")
            return True, f"백업이 생성되었습니다: {backup_path.name}"
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False, f"백업 실패: {str(e)}"
    
    def rebuild_unified_index(self) -> Tuple[bool, str]:
        """통합 인덱스 재구축"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT file_path FROM files WHERE status = 'uploaded'")
                file_paths = [row[0] for row in cursor.fetchall()]
            
            if not file_paths:
                return False, "인덱싱할 파일이 없습니다."
            
            # 기존 파일들로부터 문서 로드
            documents = []
            for file_path in file_paths:
                if os.path.exists(file_path):
                    try:
                        file_docs = SimpleDirectoryReader(input_files=[file_path]).load_data()
                        for doc in file_docs:
                            doc.metadata['source_file'] = os.path.basename(file_path)
                        documents.extend(file_docs)
                    except Exception as e:
                        logger.warning(f"Failed to load {file_path}: {e}")
            
            if documents:
                # 인덱스 생성
                self.unified_index = VectorStoreIndex.from_documents(documents)
                
                # 인덱스 저장
                index_path = self.indices_dir / "unified_index"
                if index_path.exists():
                    shutil.rmtree(index_path)
                
                self.unified_index.storage_context.persist(persist_dir=str(index_path))
                
                logger.info(f"Unified index rebuilt with {len(documents)} documents")
                return True, f"통합 인덱스가 재구축되었습니다. ({len(documents)}개 문서)"
            else:
                return False, "로드할 수 있는 문서가 없습니다."
                
        except Exception as e:
            logger.error(f"Index rebuild failed: {e}")
            return False, f"인덱스 재구축 실패: {str(e)}"
    
    def advanced_search(self, query: str, filters: Dict = None) -> Dict:
        """고급 검색 기능"""
        try:
            if not self.unified_index:
                return {"error": "인덱스가 준비되지 않았습니다."}
            
            # 벡터 검색
            query_engine = self.unified_index.as_query_engine(
                similarity_top_k=10,
                response_mode="tree_summarize"
            )
            
            response = query_engine.query(query)
            
            # 검색 결과 구성
            search_results = {
                "answer": str(response),
                "sources": [],
                "search_time": None
            }
            
            if hasattr(response, 'source_nodes'):
                for node in response.source_nodes:
                    source_info = {
                        "text": node.text[:300] + "...",
                        "score": getattr(node, 'score', 0),
                        "source_file": node.metadata.get('source_file', 'Unknown'),
                        "metadata": node.metadata
                    }
                    search_results["sources"].append(source_info)
            
            # 활동 로그
            self._log_activity("search", details=f"Query: {query}")
            
            return search_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {"error": f"검색 실패: {str(e)}"}
    
    def _schedule_index_update(self):
        """인덱스 업데이트 스케줄링"""
        # 실제 구현에서는 백그라운드 태스크로 처리
        pass
    
    def _log_activity(self, action: str, file_id: int = None, details: str = None):
        """활동 로그 기록"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO activity_logs (action, file_id, details)
                    VALUES (?, ?, ?)
                ''', (action, file_id, details))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to log activity: {e}")
    
    def get_activity_logs(self, limit: int = 100) -> pd.DataFrame:
        """활동 로그 조회"""
        with sqlite3.connect(self.db_path) as conn:
            query = '''
                SELECT al.*, f.filename
                FROM activity_logs al
                LEFT JOIN files f ON al.file_id = f.id
                ORDER BY al.timestamp DESC
                LIMIT ?
            '''
            return pd.read_sql_query(query, conn, params=[limit])
    
    def export_data(self, format_type: str = "csv") -> Tuple[bool, str]:
        """데이터 내보내기"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if format_type == "csv":
                # 파일 메타데이터 내보내기
                df = self.get_files()
                export_path = self.exports_dir / f"files_export_{timestamp}.csv"
                df.to_csv(export_path, index=False)
                
            elif format_type == "json":
                # JSON 형태로 내보내기
                df = self.get_files()
                export_data = {
                    "export_timestamp": datetime.now().isoformat(),
                    "total_files": len(df),
                    "files": df.to_dict('records')
                }
                
                export_path = self.exports_dir / f"files_export_{timestamp}.json"
                with open(export_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True, f"데이터가 내보내졌습니다: {export_path.name}"
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False, f"내보내기 실패: {str(e)}"

class TagSystem:
    """태그 관리 시스템"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
    
    def create_tag(self, name: str, color: str = "#007acc", description: str = "") -> Tuple[bool, str]:
        """새 태그 생성"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO tags (name, color, description)
                    VALUES (?, ?, ?)
                ''', (name, color, description))
                conn.commit()
                
                return True, f"태그가 생성되었습니다: {name}"
        except sqlite3.IntegrityError:
            return False, "이미 존재하는 태그명입니다."
        except Exception as e:
            return False, f"태그 생성 실패: {str(e)}"
    
    def get_all_tags(self) -> List[Dict]:
        """모든 태그 조회"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tags ORDER BY name")
            
            tags = []
            for row in cursor.fetchall():
                tags.append({
                    "id": row[0],
                    "name": row[1],
                    "color": row[2],
                    "description": row[3]
                })
            
            return tags
    
    def add_tags_to_file(self, file_id: int, tag_names: List[str]):
        """파일에 태그 추가"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for tag_name in tag_names:
                # 태그가 없으면 생성
                cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
                result = cursor.fetchone()
                
                if result:
                    tag_id = result[0]
                else:
                    cursor.execute("INSERT INTO tags (name) VALUES (?)", (tag_name,))
                    tag_id = cursor.lastrowid
                
                # 파일-태그 관계 추가
                cursor.execute('''
                    INSERT OR IGNORE INTO file_tags (file_id, tag_id)
                    VALUES (?, ?)
                ''', (file_id, tag_id))
            
            conn.commit()

class WorkflowManager:
    """워크플로우 관리자"""
    
    def __init__(self, file_manager):
        self.file_manager = file_manager
        self.active_workflows = {}
    
    def create_workflow(self, name: str, trigger_type: str, action_type: str, config: Dict) -> bool:
        """워크플로우 생성"""
        # 워크플로우 구현 (예: 파일 업로드 시 자동 태깅, 정기적 백업 등)
        pass

class PerformanceMonitor:
    """성능 모니터링"""
    
    def __init__(self):
        self.metrics = {
            "search_times": [],
            "index_build_times": [],
            "file_operations": []
        }
    
    def record_search_time(self, duration: float):
        """검색 시간 기록"""
        self.metrics["search_times"].append({
            "timestamp": datetime.now(),
            "duration": duration
        })
    
    def get_performance_summary(self) -> Dict:
        """성능 요약 반환"""
        if not self.metrics["search_times"]:
            return {"message": "성능 데이터가 없습니다."}
        
        search_times = [m["duration"] for m in self.metrics["search_times"]]
        
        return {
            "avg_search_time": sum(search_times) / len(search_times),
            "total_searches": len(search_times),
            "max_search_time": max(search_times),
            "min_search_time": min(search_times)
        }

# 시스템 인스턴스
@st.cache_resource
def get_file_manager():
    return EnterpriseFileManager()

def render_dashboard(file_manager: EnterpriseFileManager):
    """대시보드 렌더링"""
    st.subheader("📊 시스템 대시보드")
    
    # 주요 메트릭
    df_files = file_manager.get_files()
    total_files = len(df_files)
    total_size = df_files['size'].sum() if not df_files.empty else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 파일 수", total_files)
    
    with col2:
        st.metric("총 크기", f"{total_size//1024//1024}MB")
    
    with col3:
        uploaded_today = len(df_files[df_files['upload_timestamp'].str.contains(datetime.now().strftime('%Y-%m-%d'))])
        st.metric("오늘 업로드", uploaded_today)
    
    with col4:
        active_tags = len(file_manager.tag_system.get_all_tags())
        st.metric("활성 태그", active_tags)
    
    # 파일 업로드 트렌드 차트
    if not df_files.empty:
        df_files['upload_date'] = pd.to_datetime(df_files['upload_timestamp']).dt.date
        daily_uploads = df_files.groupby('upload_date').size().reset_index(name='count')
        
        fig = px.line(daily_uploads, x='upload_date', y='count', title='일별 파일 업로드 현황')
        st.plotly_chart(fig, use_container_width=True)

def render_file_management(file_manager: EnterpriseFileManager):
    """파일 관리 인터페이스"""
    st.subheader("🗂️ 파일 관리")
    
    # 필터 옵션
    with st.expander("🔍 필터 및 검색", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            all_tags = file_manager.tag_system.get_all_tags()
            tag_names = [tag['name'] for tag in all_tags]
            selected_tags = st.multiselect("태그 필터", tag_names)
        
        with col2:
            status_filter = st.multiselect(
                "상태 필터",
                ["uploaded", "analyzed", "archived"],
                default=["uploaded", "analyzed"]
            )
        
        with col3:
            date_range = st.date_input(
                "업로드 날짜 범위",
                value=[datetime.now().date() - timedelta(days=30), datetime.now().date()]
            )
    
    # 필터 적용
    filters = {
        "status": status_filter,
        "tags": selected_tags
    }
    
    if len(date_range) == 2:
        filters["date_from"] = date_range[0].strftime('%Y-%m-%d')
        filters["date_to"] = date_range[1].strftime('%Y-%m-%d')
    
    # 파일 목록 조회
    df_files = file_manager.get_files(filters)
    
    if not df_files.empty:
        # 파일 목록 표시
        for _, file_row in df_files.iterrows():
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    st.write(f"📄 **{file_row['filename']}**")
                    if file_row['tags']:
                        tags_html = ""
                        for tag in file_row['tags'].split(','):
                            tags_html += f'<span style="background-color: #007acc; color: white; padding: 2px 6px; margin: 2px; border-radius: 3px; font-size: 12px;">{tag}</span>'
                        st.markdown(tags_html, unsafe_allow_html=True)
                
                with col2:
                    st.write(f"{file_row['size']//1024}KB")
                    st.caption(file_row['upload_timestamp'][:10])
                
                with col3:
                    st.write(file_row['status'])
                
                with col4:
                    if st.button("🗑️", key=f"delete_{file_row['id']}", help="파일 삭제"):
                        success, message = file_manager.delete_file(file_row['id'])
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                
                st.divider()
    else:
        st.info("조건에 맞는 파일이 없습니다.")

def main():
    st.title("🗂️ 엔터프라이즈 파일 관리 & QA 시스템")
    st.markdown("---")
    
    # 시스템 초기화
    file_manager = get_file_manager()
    
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
        
        # 시스템 초기화
        if st.button("🚀 시스템 초기화", type="primary"):
            if api_key:
                if file_manager.initialize_system(api_key):
                    st.success("✅ 시스템 초기화 완료!")
                    st.session_state.system_ready = True
                else:
                    st.error("시스템 초기화 실패")
            else:
                st.warning("API 키를 입력해주세요.")
        
        st.markdown("---")
        
        # 시스템 작업
        if getattr(st.session_state, 'system_ready', False):
            st.subheader("🔧 시스템 작업")
            
            if st.button("🔄 인덱스 재구축"):
                with st.spinner("인덱스를 재구축하는 중..."):
                    success, message = file_manager.rebuild_unified_index()
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
            
            if st.button("💾 백업 생성"):
                with st.spinner("백업을 생성하는 중..."):
                    success, message = file_manager.create_backup()
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
            
            # 데이터 내보내기
            export_format = st.selectbox("내보내기 형식", ["csv", "json"])
            if st.button("📤 데이터 내보내기"):
                success, message = file_manager.export_data(export_format)
                if success:
                    st.success(message)
                else:
                    st.error(message)
    
    # 메인 컨텐츠
    if not api_key:
        st.warning("⚠️ OpenAI API 키가 필요합니다.")
        return
    
    if not getattr(st.session_state, 'system_ready', False):
        st.info("👈 사이드바에서 시스템을 초기화해주세요.")
        
        # 시스템 소개
        st.markdown("""
        ### 🌟 엔터프라이즈 파일 관리 시스템의 특징:
        
        **📁 완전한 파일 관리**
        - 파일 버전 관리 및 중복 방지
        - 고급 메타데이터 및 태깅 시스템
        - 자동화된 백업 및 복원
        
        **🔍 지능형 검색**
        - AI 기반 의미론적 검색
        - 고급 필터링 및 정렬
        - 실시간 검색 결과
        
        **⚡ 성능 최적화**
        - 분산 인덱싱 및 캐싱
        - 배치 처리 및 워크플로우
        - 실시간 성능 모니터링
        
        **🔒 엔터프라이즈 기능**
        - 활동 로그 및 감사 추적
        - 데이터 내보내기/가져오기
        - API 통합 지원
        """)
        return
    
    # 탭 구성
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📤 파일 업로드",
        "🗂️ 파일 관리", 
        "🔍 고급 검색",
        "🏷️ 태그 관리",
        "📊 대시보드",
        "📋 활동 로그"
    ])
    
    with tab1:
        st.header("📤 파일 업로드")
        
        # 파일 업로드
        uploaded_files = st.file_uploader(
            "파일 선택",
            type=['pdf', 'txt', 'docx', 'md', 'html'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            # 태그 입력
            all_tags = file_manager.tag_system.get_all_tags()
            existing_tag_names = [tag['name'] for tag in all_tags]
            
            tags_input = st.text_input(
                "태그 (쉼표로 구분)",
                help="기존 태그: " + ", ".join(existing_tag_names[:10]) if existing_tag_names else "태그가 없습니다."
            )
            
            # 메타데이터 입력
            with st.expander("📝 추가 메타데이터"):
                description = st.text_area("설명")
                category = st.selectbox("카테고리", ["문서", "보고서", "매뉴얼", "기타"])
                importance = st.slider("중요도", 1, 5, 3)
            
            if st.button("📥 업로드 시작", type="primary"):
                tags = [tag.strip() for tag in tags_input.split(',')] if tags_input else []
                metadata = {
                    "description": description,
                    "category": category,
                    "importance": importance
                }
                
                success_count = 0
                for uploaded_file in uploaded_files:
                    success, message = file_manager.add_file(uploaded_file, tags, metadata)
                    if success:
                        success_count += 1
                    else:
                        st.error(f"{uploaded_file.name}: {message}")
                
                if success_count > 0:
                    st.success(f"✅ {success_count}개 파일이 업로드되었습니다!")
    
    with tab2:
        render_file_management(file_manager)
    
    with tab3:
        st.header("🔍 고급 검색")
        
        search_query = st.text_input(
            "검색어를 입력하세요:",
            placeholder="예: 문서에서 중요한 정보를 찾아주세요"
        )
        
        if search_query and st.button("🔍 검색", type="primary"):
            with st.spinner("검색하는 중..."):
                results = file_manager.advanced_search(search_query)
            
            if "error" in results:
                st.error(results["error"])
            else:
                st.write("### 📝 답변")
                st.write(results["answer"])
                
                if results["sources"]:
                    st.write("### 📄 참조 문서")
                    for i, source in enumerate(results["sources"]):
                        with st.expander(f"소스 {i+1}: {source['source_file']} (유사도: {source['score']:.3f})"):
                            st.write(source["text"])
    
    with tab4:
        st.header("🏷️ 태그 관리")
        
        # 새 태그 생성
        with st.expander("➕ 새 태그 생성"):
            col1, col2 = st.columns(2)
            with col1:
                new_tag_name = st.text_input("태그 이름")
                new_tag_color = st.color_picker("태그 색상", "#007acc")
            with col2:
                new_tag_desc = st.text_area("태그 설명", height=100)
            
            if st.button("✨ 태그 생성"):
                if new_tag_name:
                    success, message = file_manager.tag_system.create_tag(
                        new_tag_name, new_tag_color, new_tag_desc
                    )
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
        
        # 기존 태그 목록
        st.subheader("📋 기존 태그")
        tags = file_manager.tag_system.get_all_tags()
        
        if tags:
            for tag in tags:
                col1, col2, col3 = st.columns([2, 3, 1])
                with col1:
                    st.markdown(f'<span style="background-color: {tag["color"]}; color: white; padding: 4px 8px; border-radius: 4px;">{tag["name"]}</span>', unsafe_allow_html=True)
                with col2:
                    st.write(tag["description"] or "설명 없음")
                with col3:
                    st.caption(f"ID: {tag['id']}")
        else:
            st.info("생성된 태그가 없습니다.")
    
    with tab5:
        render_dashboard(file_manager)
    
    with tab6:
        st.header("📋 활동 로그")
        
        # 로그 필터
        log_limit = st.slider("표시할 로그 수", 10, 500, 100)
        
        # 활동 로그 조회
        df_logs = file_manager.get_activity_logs(log_limit)
        
        if not df_logs.empty:
            st.dataframe(df_logs, use_container_width=True)
        else:
            st.info("활동 로그가 없습니다.")

if __name__ == "__main__":
    main()