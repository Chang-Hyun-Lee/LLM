import gradio as gr
import tempfile

from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA

# 임시 변수 (세션 기반 공유용)
qa_chain = None

# PDF 로딩 및 QA 체인 생성 함수
def load_pdf(file):
    global qa_chain

    # file은 bytes 객체
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(file)
        pdf_path = tmp_file.name

    # 문서 로딩 및 분할
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_documents(documents)

    # 임베딩 및 벡터 저장
    embedding_model = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(chunks, embedding_model)

    # QA 체인 구성 (GPT-4o 사용)
    retriever = vectorstore.as_retriever()
    llm = ChatOpenAI(model_name="gpt-4o")
    qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)

    return "✅ PDF 로딩 및 처리 완료! 질문을 입력해보세요."

# 챗 응답 함수
def chat(message, history):
    global qa_chain
    if qa_chain is None:
        return "❗ 먼저 PDF 파일을 업로드해주세요."

    response = qa_chain.run(message)
    history.append((message, response))
    return "", history

# Gradio 챗 인터페이스 구성
with gr.Blocks() as demo:
    gr.Markdown("## 📄 PDF 기반 GPT-4o 챗봇")
    gr.Markdown("PDF를 업로드하고 질문을 입력하면, 해당 내용에 기반해 GPT-4o가 응답합니다.")

    file_input = gr.File(label="📎 PDF 업로드", type="binary")
    file_status = gr.Textbox(label="✅ 파일 상태", interactive=False)

    chatbot = gr.Chatbot(label="🗨️ 챗기록", height=400)
    msg_input = gr.Textbox(label="💬 질문 입력", placeholder="예: 핵심 주장이 뭐야?", lines=1)
    send_btn = gr.Button("질문하기")

    # 이벤트 연결
    file_input.change(fn=load_pdf, inputs=file_input, outputs=file_status)
    send_btn.click(fn=chat, inputs=[msg_input, chatbot], outputs=[msg_input, chatbot])

# 실행
if __name__ == "__main__":
    demo.launch()