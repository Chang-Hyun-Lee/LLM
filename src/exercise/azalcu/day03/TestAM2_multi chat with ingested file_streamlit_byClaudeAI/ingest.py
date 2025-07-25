# ingest.py - PDF 문서 인덱싱 모듈

import os
import pickle
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import streamlit as st

class DocumentIngestor:
    def __init__(self, openai_api_key=None):
        """문서 인덱서 초기화"""
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        self.embeddings = OpenAIEmbeddings()
    
    def load_single_pdf(self, pdf_path):
        """단일 PDF 파일 로드"""
        try:
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()
            return documents
        except Exception as e:
            st.error(f"PDF 로드 오류: {str(e)}")
            return []
    
    def load_directory_pdfs(self, directory_path):
        """디렉토리의 모든 PDF 파일 로드"""
        try:
            loader = DirectoryLoader(
                directory_path,
                glob="**/*.pdf",
                loader_cls=PyPDFLoader
            )
            documents = loader.load()
            return documents
        except Exception as e:
            st.error(f"디렉토리 PDF 로드 오류: {str(e)}")
            return []
    
    def process_documents(self, documents):
        """문서를 청크로 분할"""
        if not documents:
            return []
        
        texts = self.text_splitter.split_documents(documents)
        return texts
    
    def create_vectorstore(self, texts):
        """벡터 스토어 생성"""
        try:
            vectorstore = FAISS.from_documents(texts, self.embeddings)
            return vectorstore
        except Exception as e:
            st.error(f"벡터 스토어 생성 오류: {str(e)}")
            return None
    
    def save_vectorstore(self, vectorstore, save_path):
        """벡터 스토어 저장"""
        try:
            # 디렉토리가 없으면 생성
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # FAISS 인덱스 저장
            vectorstore.save_local(save_path)
            
            # 메타데이터 저장
            metadata = {
                'document_count': vectorstore.index.ntotal,
                'embedding_dimension': vectorstore.index.d
            }
            
            with open(f"{save_path}/metadata.pkl", "wb") as f:
                pickle.dump(metadata, f)
            
            return True
        except Exception as e:
            st.error(f"벡터 스토어 저장 오류: {str(e)}")
            return False
    
    def load_vectorstore(self, load_path):
        """저장된 벡터 스토어 로드"""
        try:
            vectorstore = FAISS.load_local(load_path, self.embeddings)
            return vectorstore
        except Exception as e:
            st.error(f"벡터 스토어 로드 오류: {str(e)}")
            return None
    
    def ingest_pdf(self, pdf_path, save_path=None):
        """PDF를 인덱싱하여 벡터 스토어 생성"""
        # 1. PDF 로드
        st.info("📄 PDF 파일을 로드하는 중...")
        documents = self.load_single_pdf(pdf_path)
        
        if not documents:
            return None
        
        st.success(f"✅ {len(documents)} 페이지를 로드했습니다.")
        
        # 2. 텍스트 분할
        st.info("✂️ 텍스트를 청크로 분할하는 중...")
        texts = self.process_documents(documents)
        
        if not texts:
            st.error("텍스트 분할에 실패했습니다.")
            return None
        
        st.success(f"✅ {len(texts)} 개의 텍스트 청크를 생성했습니다.")
        
        # 3. 벡터 스토어 생성
        st.info("🔄 벡터 임베딩 생성 중...")
        vectorstore = self.create_vectorstore(texts)
        
        if not vectorstore:
            return None
        
        st.success("✅ 벡터 스토어가 생성되었습니다.")
        
        # 4. 저장 (선택사항)
        if save_path:
            st.info("💾 벡터 스토어를 저장하는 중...")
            if self.save_vectorstore(vectorstore, save_path):
                st.success(f"✅ 벡터 스토어가 {save_path}에 저장되었습니다.")
            else:
                st.warning("⚠️ 벡터 스토어 저장에 실패했지만, 메모리에서 사용 가능합니다.")
        
        return vectorstore
    
    def ingest_directory(self, directory_path, save_path=None):
        """디렉토리의 모든 PDF를 인덱싱"""
        # 1. 디렉토리의 PDF 로드
        st.info("📁 디렉토리에서 PDF 파일들을 로드하는 중...")
        documents = self.load_directory_pdfs(directory_path)
        
        if not documents:
            return None
        
        st.success(f"✅ {len(documents)} 개의 문서를 로드했습니다.")
        
        # 2. 텍스트 분할
        st.info("✂️ 텍스트를 청크로 분할하는 중...")
        texts = self.process_documents(documents)
        
        if not texts:
            st.error("텍스트 분할에 실패했습니다.")
            return None
        
        st.success(f"✅ {len(texts)} 개의 텍스트 청크를 생성했습니다.")
        
        # 3. 벡터 스토어 생성
        st.info("🔄 벡터 임베딩 생성 중...")
        vectorstore = self.create_vectorstore(texts)
        
        if not vectorstore:
            return None
        
        st.success("✅ 벡터 스토어가 생성되었습니다.")
        
        # 4. 저장 (선택사항)
        if save_path:
            st.info("💾 벡터 스토어를 저장하는 중...")
            if self.save_vectorstore(vectorstore, save_path):
                st.success(f"✅ 벡터 스토어가 {save_path}에 저장되었습니다.")
            else:
                st.warning("⚠️ 벡터 스토어 저장에 실패했지만, 메모리에서 사용 가능합니다.")
        
        return vectorstore


def main():
    """CLI용 메인 함수"""
    import sys
    
    if len(sys.argv) != 3:
        print("사용법: python ingest.py <PDF경로> <저장경로>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    save_path = sys.argv[2]
    
    # OpenAI API 키 확인
    if not os.getenv("OPENAI_API_KEY"):
        api_key = input("OpenAI API 키를 입력하세요: ")
        os.environ["OPENAI_API_KEY"] = api_key
    
    # 인덱싱 실행
    ingestor = DocumentIngestor()
    vectorstore = ingestor.ingest_pdf(pdf_path, save_path)
    
    if vectorstore:
        print(f"✅ 인덱싱 완료: {save_path}")
    else:
        print("❌ 인덱싱 실패")


if __name__ == "__main__":
    main()