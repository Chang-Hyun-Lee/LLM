from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter

file_name = '소나기.pdf'

loader = PyPDFLoader(file_name)
documents = loader.load()

text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
docs = text_splitter.split_documents(documents)

from langchain.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings

#embeddings = HuggingFaceEmbeddings()
embeddings = OpenAIEmbeddings()

from langchain.indexes import VectorstoreIndexCreator
from langchain.vectorstores import FAISS

index = VectorstoreIndexCreator(
    vectorstore_cls=FAISS,
    embedding=embeddings,
    ).from_loaders([loader])

# 파일로 저장
index.vectorstore.save_local("shower")