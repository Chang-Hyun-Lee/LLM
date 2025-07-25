from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter

file_name = '소나기.pdf'

# 파일을 로드하기
loader = PyPDFLoader(file_name)
documents = loader.load()

# 문서를 일정 사이즈로 자르기
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
docs = text_splitter.split_documents(documents)

from langchain.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings

#embeddings = HuggingFaceEmbeddings()
embeddings = OpenAIEmbeddings()

from langchain.indexes import VectorstoreIndexCreator
from langchain.vectorstores import FAISS

# 벡터 DB로 만들기
index = VectorstoreIndexCreator(
    vectorstore_cls = FAISS,
    embedding = embeddings,
    ).from_loaders([loader])

# 파일로 저장 (faiss, pkl)
index.vectorstore.save_local("shower")