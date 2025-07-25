# shared/ingest.py
"""
LlamaIndex 기반 문서 처리 공용 모듈
전체 실습에서 공통으로 사용할 수 있는 유틸리티 함수들
"""

import os
import logging
import tempfile
import shutil
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings, Document
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.memory import ChatMemoryBuffer

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """문서 처리를 위한 공용 클래스"""
    
    SUPPORTED_EXTENSIONS = ['.pdf', '.txt', '.docx', '.md', '.html']
    
    def __init__(self, api_key: str, model_name: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.model_name = model_name
        self._initialize_settings()
    
    def _initialize_settings(self):
        """LlamaIndex 설정 초기화"""
        try:
            Settings.llm = OpenAI(model=self.model_name, api_key=self.api_key)
            Settings.embed_model = OpenAIEmbedding(api_key=self.api_key)
            logger.info(f"LlamaIndex initialized with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize LlamaIndex: {e}")
            raise
    
    def load_documents_from_directory(
        self, 
        directory: str, 
        file_extensions: Optional[List[str]] = None
    ) -> Tuple[Optional[List[Document]], str]:
        """디렉토리에서 문서 로드"""
        try:
            if not os.path.exists(directory):
                return None, f"Directory not found: {directory}"
            
            # 파일 확장자 필터링
            extensions = file_extensions or self.SUPPORTED_EXTENSIONS
            
            reader = SimpleDirectoryReader(
                directory,
                required_exts=extensions,
                recursive=True
            )
            
            documents = reader.load_data()
            
            if not documents:
                return None, f"No supported documents found in {directory}"
            
            # 메타데이터 추가
            for doc in documents:
                if not doc.metadata:
                    doc.metadata = {}
                doc.metadata['load_time'] = datetime.now().isoformat()
                doc.metadata['source_directory'] = directory
            
            logger.info(f"Loaded {len(documents)} documents from {directory}")
            return documents, f"Successfully loaded {len(documents)} documents"
            
        except Exception as e:
            logger.error(f"Failed to load documents: {e}")
            return None, f"Document loading failed: {str(e)}"
    
    def load_documents_from_files(
        self, 
        file_paths: List[str]
    ) -> Tuple[Optional[List[Document]], str]:
        """특정 파일들에서 문서 로드"""
        try:
            documents = []
            successful_files = []
            failed_files = []
            
            for file_path in file_paths:
                try:
                    if not os.path.exists(file_path):
                        failed_files.append(f"{file_path} (not found)")
                        continue
                    
                    reader = SimpleDirectoryReader(input_files=[file_path])
                    file_docs = reader.load_data()
                    
                    # 메타데이터 추가
                    for doc in file_docs:
                        if not doc.metadata:
                            doc.metadata = {}
                        doc.metadata.update({
                            'file_name': os.path.basename(file_path),
                            'file_path': file_path,
                            'file_size': os.path.getsize(file_path),
                            'load_time': datetime.now().isoformat()
                        })
                    
                    documents.extend(file_docs)
                    successful_files.append(os.path.basename(file_path))
                    
                except Exception as e:
                    failed_files.append(f"{os.path.basename(file_path)} ({str(e)})")
            
            if not documents:
                return None, f"No documents could be loaded. Failed files: {failed_files}"
            
            message = f"Loaded {len(documents)} documents from {len(successful_files)} files"
            if failed_files:
                message += f". Failed: {len(failed_files)} files"
            
            logger.info(message)
            return documents, message
            
        except Exception as e:
            logger.error(f"Failed to load documents from files: {e}")
            return None, f"File loading failed: {str(e)}"
    
    def create_index(
        self, 
        documents: List[Document],
        chunk_size: int = 1024,
        chunk_overlap: int = 50
    ) -> Tuple[Optional[VectorStoreIndex], str]:
        """문서에서 벡터 인덱스 생성"""
        try:
            # 텍스트 분할기 설정
            splitter = SentenceSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            
            # 인덱스 생성
            index = VectorStoreIndex.from_documents(
                documents,
                transformations=[splitter]
            )
            
            logger.info(f"Created index from {len(documents)} documents")
            return index, f"Successfully created index from {len(documents)} documents"
            
        except Exception as e:
            logger.error(f"Failed to create index: {e}")
            return None, f"Index creation failed: {str(e)}"
    
    def save_uploaded_file(
        self, 
        uploaded_file, 
        save_directory: str
    ) -> Tuple[Optional[str], str]:
        """업로드된 파일을 저장"""
        try:
            os.makedirs(save_directory, exist_ok=True)
            
            file_path = os.path.join(save_directory, uploaded_file.name)
            
            # 중복 파일명 처리
            if os.path.exists(file_path):
                base, ext = os.path.splitext(uploaded_file.name)
                counter = 1
                while os.path.exists(file_path):
                    file_path = os.path.join(save_directory, f"{base}_{counter}{ext}")
                    counter += 1
            
            # 파일 저장
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            logger.info(f"Saved uploaded file: {file_path}")
            return file_path, f"File saved successfully: {os.path.basename(file_path)}"
            
        except Exception as e:
            logger.error(f"Failed to save uploaded file: {e}")
            return None, f"File save failed: {str(e)}"

class ChatEngine:
    """채팅 엔진 래퍼 클래스"""
    
    def __init__(
        self, 
        index: VectorStoreIndex,
        chat_mode: str = "context",
        memory_token_limit: int = 1500,
        system_prompt: Optional[str] = None
    ):
        self.index = index
        self.chat_mode = chat_mode
        self.memory_token_limit = memory_token_limit
        self.system_prompt = system_prompt or self._default_system_prompt()
        self._create_chat_engine()
    
    def _default_system_prompt(self) -> str:
        """기본 시스템 프롬프트"""
        return (
            "당신은 문서 내용을 바탕으로 질문에 답하는 전문 어시스턴트입니다. "
            "정확하고 도움이 되는 답변을 제공하며, 문서에 없는 내용은 추측하지 않습니다. "
            "가능한 경우 답변의 출처를 명시해주세요."
        )
    
    def _create_chat_engine(self):
        """채팅 엔진 생성"""
        try:
            memory = ChatMemoryBuffer.from_defaults(
                token_limit=self.memory_token_limit
            )
            
            self.chat_engine = self.index.as_chat_engine(
                chat_mode=self.chat_mode,
                memory=memory,
                system_prompt=self.system_prompt
            )
            
            logger.info("Chat engine created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create chat engine: {e}")
            raise
    
    def chat(self, message: str) -> Tuple[Optional[str], str]:
        """채팅 메시지 처리"""
        try:
            response = self.chat_engine.chat(message)
            return str(response), "Success"
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            return None, f"Chat failed: {str(e)}"
    
    def reset_memory(self):
        """채팅 메모리 초기화"""
        try:
            self._create_chat_engine()
            logger.info("Chat memory reset")
        except Exception as e:
            logger.error(f"Failed to reset memory: {e}")

class FileManager:
    """파일 관리를 위한 유틸리티 클래스"""
    
    def __init__(self, base_directory: str):
        self.base_directory = Path(base_directory)
        self.base_directory.mkdir(exist_ok=True)
    
    def list_files(self, extensions: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """파일 목록 조회"""
        files_info = []
        
        for file_path in self.base_directory.iterdir():
            if file_path.is_file():
                if extensions and file_path.suffix.lower() not in extensions:
                    continue
                
                stat = file_path.stat()
                files_info.append({
                    'name': file_path.name,
                    'path': str(file_path),
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime),
                    'extension': file_path.suffix.lower()
                })
        
        return sorted(files_info, key=lambda x: x['modified'], reverse=True)
    
    def delete_file(self, filename: str) -> Tuple[bool, str]:
        """파일 삭제"""
        try:
            file_path = self.base_directory / filename
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted file: {filename}")
                return True, f"File deleted successfully: {filename}"
            else:
                return False, f"File not found: {filename}"
        except Exception as e:
            logger.error(f"Failed to delete file {filename}: {e}")
            return False, f"Delete failed: {str(e)}"
    
    def delete_all_files(self) -> Tuple[int, str]:
        """모든 파일 삭제"""
        try:
            deleted_count = 0
            for file_path in self.base_directory.iterdir():
                if file_path.is_file():
                    file_path.unlink()
                    deleted_count += 1
            
            logger.info(f"Deleted {deleted_count} files")
            return deleted_count, f"Deleted {deleted_count} files successfully"
            
        except Exception as e:
            logger.error(f"Failed to delete all files: {e}")
            return 0, f"Delete all failed: {str(e)}"
    
    def get_file_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """특정 파일 정보 조회"""
        file_path = self.base_directory / filename
        if file_path.exists():
            stat = file_path.stat()
            return {
                'name': file_path.name,
                'path': str(file_path),
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'extension': file_path.suffix.lower()
            }
        return None

def format_file_size(size_bytes: int) -> str:
    """파일 크기를 읽기 쉬운 형태로 포맷"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes/(1024**2):.1f} MB"
    else:
        return f"{size_bytes/(1024**3):.1f} GB"

def validate_api_key(api_key: str) -> bool:
    """API 키 유효성 검증"""
    if not api_key:
        return False
    
    # OpenAI API 키 형식 검증
    if api_key.startswith('sk-') and len(api_key) > 20:
        return True
    
    return False

# 설정 상수
DEFAULT_CHUNK_SIZE = 1024
DEFAULT_CHUNK_OVERLAP = 50
DEFAULT_SIMILARITY_TOP_K = 3
DEFAULT_MEMORY_TOKEN_LIMIT = 1500

SUPPORTED_FILE_TYPES = {
    'pdf': 'PDF 문서',
    'txt': '텍스트 파일', 
    'docx': 'Word 문서',
    'md': 'Markdown 파일',
    'html': 'HTML 파일'
}

# 로깅 설정
def setup_logging(level=logging.INFO):
    """로깅 설정"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
        ]
    )