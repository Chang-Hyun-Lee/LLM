import streamlit as st
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from openai import OpenAI
import tempfile

client = OpenAI()

st.set_page_config(page_title="📄 PDF Q&A Chatbot", page_icon="📄")
st.title("📄 PDF 문서 기반 Q&A")

uploaded_file = st.file_uploader("PDF 파일 업로드", type=["pdf"])

if uploaded_file:
    # ✅ 임시 파일로 저장
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_path = tmp_file.name

    with st.spinner("📖 문서를 처리 중입니다..."):
        loader = PyPDFLoader(tmp_path)
        documents = loader.load()

        splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        docs = splitter.split_documents(documents)

        embeddings = OpenAIEmbeddings()
        vectorstore = FAISS.from_documents(docs, embeddings)
        retriever = vectorstore.as_retriever()

    st.success("✅ 문서 로딩 완료! 이제 질문하세요.")
    query = st.text_input("❓ 문서에 대해 궁금한 점을 입력하세요:")

    if query:
        with st.spinner("🤖 GPT가 응답 중입니다..."):
            context_docs = retriever.get_relevant_documents(query)
            context = "\n\n".join([doc.page_content for doc in context_docs])

            messages = [
                {"role": "system", "content": "너는 문서 내용을 기반으로 정확하게 답변해주는 도우미야."},
                {"role": "user", "content": f"{context}\n\n질문: {query}"}
            ]

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages
            )

            answer = response.choices[0].message.content
            st.markdown("### 💬 답변")
            st.write(answer)