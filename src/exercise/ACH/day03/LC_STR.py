import os
import streamlit as st
import openai
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain

# langchain.memory에서 ConversationBufferMemory 가져오기
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import AIMessage, HumanMessage
from dotenv import load_dotenv

# ✅ 환경변수 로드
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if api_key is None:
    raise ValueError("❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")

openai.api_key = api_key

# 세션 상태 초기화
if "conversation_chain" not in st.session_state:
    st.session_state.conversation_chain = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# PDF 처리 함수
def process_pdf(pdf_path):
    try:
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()

        if not documents:
            return "❌ PDF에서 텍스트를 추출할 수 없습니다."

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
            length_function=len
        )
        chunks = text_splitter.split_documents(documents)

        if not chunks:
            return "❌ PDF 내용을 분할할 수 없습니다."

        embeddings = OpenAIEmbeddings()
        vectorstore = FAISS.from_documents(chunks, embeddings)

        memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        
        st.session_state.conversation_chain = ConversationalRetrievalChain.from_llm(
            llm=ChatOpenAI(temperature=0.7, model_name="gpt-4"),
            retriever=vectorstore.as_retriever(),
            memory=memory
        )

        st.session_state.chat_history = []
        return "✅ PDF가 성공적으로 처리되었습니다. 이제 질문할 수 있습니다."

    except Exception as e:
        return f"❌ 오류 발생: {str(e)}"

# 질문에 대한 답변 처리
def answer_query(user_input):
    if not user_input.strip():
        return

    if st.session_state.conversation_chain is None:
        st.warning("⚠️ 먼저 PDF 파일을 업로드하고 처리하세요.")
        return

    try:
        response = st.session_state.conversation_chain.invoke({"question": user_input})
        answer = response["answer"]
        st.session_state.chat_history.append(("user", user_input))
        st.session_state.chat_history.append(("bot", answer))
    except Exception as e:
        st.session_state.chat_history.append(("bot", f"❌ 오류가 발생했습니다: {str(e)}"))

# UI 구성
st.set_page_config(page_title="PDF QA System", layout="wide")
st.title("📄 PDF 기반 질의응답 시스템")
st.markdown("PDF 파일을 업로드하고, 내용에 대해 질문해보세요!")

# === 사이드바 영역 시작 ===
with st.sidebar:
    st.header("📁 PDF 업로드 및 처리")
    uploaded_file = st.file_uploader("PDF 파일 선택", type=["pdf"])
    if uploaded_file is not None:
        with st.spinner("PDF 처리 중..."):
            with open("temp.pdf", "wb") as f:
                f.write(uploaded_file.read())
        status_message = process_pdf("temp.pdf")
        
        # 상태 메시지 표시
        if "✅" in status_message:
            st.success(status_message)
        else:
            st.error(status_message)

    if st.button("🔄 대화 초기화"):
        st.session_state.chat_history = []
        st.session_state.conversation_chain = None
        st.success("대화 기록이 초기화되었습니다.")

# 대화창 영역
st.subheader("💬 질문 및 답변")

if prompt := st.text_input("질문을 입력하세요", key="user_input"):
    answer_query(prompt)

# 대화 히스토리 출력
for sender, message in st.session_state.chat_history:
    if sender == "user":
        st.markdown(f"**🙋‍♂️ 질문:** {message}")
    else:
        st.markdown(f"**🤖 답변:** {message}")

##streamlit run LC_STR.py