import streamlit as st
from llama_index import VectorStoreIndex, ServiceContext, Document
from llama_index.llms import OpenAI
import openai
import os
import shutil
from llama_index import StorageContext, load_index_from_storage
from dotenv import load_dotenv
from PyPDF2 import PdfReader
import docx2txt
import glob

# 환경변수 로드
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if api_key is None:
    st.error("❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
    st.stop()

openai.api_key = api_key

# 페이지 제목 설정
st.title("LlamaIndex 문서 관리 챗봇")

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_engine" not in st.session_state:
    st.session_state.chat_engine = None
if "current_file" not in st.session_state:
    st.session_state.current_file = None
if "file_summary" not in st.session_state:
    st.session_state.file_summary = {}

# 저장 디렉토리 설정
storage_dir = "./storage"
os.makedirs(storage_dir, exist_ok=True)

# 사이드바 - 파일 관리 섹션
st.sidebar.title("파일 관리")

# 파일 업로드 기능
uploaded_file = st.sidebar.file_uploader("문서를 업로드하세요", type=["pdf", "txt", "docx"])

# 파일 내용 추출 함수
def extract_text_from_file(file):
    if file.type == "text/plain":
        return file.getvalue().decode("utf-8")
    elif file.type == "application/pdf":
        pdf_reader = PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return docx2txt.process(file)
    return ""

# 파일 요약 생성 함수
def generate_file_summary(text, file_name):
    try:
        llm = OpenAI(model="gpt-3.5-turbo", temperature=0.5)
        summary_prompt = f"다음 문서의 내용을 200자 이내로 요약해주세요:\n\n{text[:2000]}..."
        summary = llm.complete(summary_prompt)
        return summary.text
    except Exception as e:
        st.error(f"요약 생성 중 오류 발생: {e}")
        return "요약을 생성할 수 없습니다."

# 파일 목록 가져오기
def get_file_list():
    files = []
    for dir_name in os.listdir(storage_dir):
        dir_path = os.path.join(storage_dir, dir_name)
        if os.path.isdir(dir_path):
            for file_path in glob.glob(os.path.join(dir_path, "*.*")):
                if os.path.isfile(file_path) and not file_path.endswith((".gitignore", ".DS_Store")):
                    file_name = os.path.basename(file_path)
                    files.append((file_name, dir_name))
    return files

# 파일 처리
if uploaded_file:
    # 파일명으로 디렉토리 생성
    file_dir = os.path.join(storage_dir, os.path.splitext(uploaded_file.name)[0])
    os.makedirs(file_dir, exist_ok=True)
    
    # 파일 저장
    file_path = os.path.join(file_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getvalue())
    
    # 파일 내용 추출
    text = extract_text_from_file(uploaded_file)
    
    # 파일 요약 생성
    if uploaded_file.name not in st.session_state.file_summary:
        summary = generate_file_summary(text, uploaded_file.name)
        st.session_state.file_summary[uploaded_file.name] = summary
    
    # 저장된 인덱스가 있는지 확인
    if os.path.exists(os.path.join(file_dir, "index")):
        st.sidebar.info("저장된 인덱스를 불러옵니다...")
        # 저장된 인덱스 로드
        storage_context = StorageContext.from_defaults(persist_dir=os.path.join(file_dir, "index"))
        index = load_index_from_storage(storage_context)
        st.session_state.chat_engine = index.as_chat_engine(verbose=True)
    else:
        st.sidebar.info("새로운 인덱스를 생성합니다...")
        if text:
            documents = [Document(text=text)]
            
            # 인덱스 생성
            service_context = ServiceContext.from_defaults(llm=OpenAI(model="gpt-3.5-turbo", temperature=0.5))
            index = VectorStoreIndex.from_documents(documents, service_context=service_context)
            
            # 인덱스 저장
            index.storage_context.persist(os.path.join(file_dir, "index"))
            st.session_state.chat_engine = index.as_chat_engine(verbose=True)
            st.sidebar.success("인덱스가 생성되었습니다!")
        else:
            st.sidebar.error("파일 내용을 추출할 수 없습니다.")
    
    st.session_state.current_file = uploaded_file.name
    st.session_state.messages = []  # 새 파일이 업로드되면 대화 초기화

# 파일 목록 표시
file_list = get_file_list()
if file_list:
    st.sidebar.subheader("업로드된 파일 목록")
    for file_name, dir_name in file_list:
        col1, col2, col3 = st.sidebar.columns([3, 1, 1])
        with col1:
            if st.button(f"📄 {file_name}", key=f"select_{file_name}"):
                file_dir = os.path.join(storage_dir, dir_name)
                if os.path.exists(os.path.join(file_dir, "index")):
                    storage_context = StorageContext.from_defaults(persist_dir=os.path.join(file_dir, "index"))
                    index = load_index_from_storage(storage_context)
                    st.session_state.chat_engine = index.as_chat_engine(verbose=True)
                    st.session_state.current_file = file_name
                    st.session_state.messages = []  # 파일 변경 시 대화 초기화
        with col2:
            if st.button("🔍", key=f"view_{file_name}"):
                file_dir = os.path.join(storage_dir, dir_name)
                file_path = os.path.join(file_dir, file_name)
                if os.path.exists(file_path):
                    with open(file_path, "rb") as f:
                        file_content = f.read()
                    
                    if file_name.endswith(".txt"):
                        st.sidebar.text_area("파일 내용", file_content.decode("utf-8"), height=200)
                    elif file_name.endswith(".pdf"):
                        st.sidebar.info(f"{file_name} - PDF 파일은 미리보기를 지원하지 않습니다.")
                    elif file_name.endswith(".docx"):
                        st.sidebar.info(f"{file_name} - DOCX 파일은 미리보기를 지원하지 않습니다.")
        with col3:
            if st.button("❌", key=f"delete_{file_name}"):
                file_dir = os.path.join(storage_dir, dir_name)
                if os.path.exists(file_dir):
                    shutil.rmtree(file_dir)
                    st.experimental_rerun()

# 현재 선택된 파일 표시
if st.session_state.current_file:
    st.subheader(f"현재 파일: {st.session_state.current_file}")
    
    # 파일 요약 표시
    if st.session_state.current_file in st.session_state.file_summary:
        with st.expander("파일 요약 보기", expanded=False):
            st.write(st.session_state.file_summary[st.session_state.current_file])

# 대화 인터페이스
st.subheader("문서에 대해 질문하기")

# 이전 대화 내용 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 사용자 입력 처리
if prompt := st.chat_input("질문을 입력하세요:"):
    # 사용자 메시지 추가
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 챗봇 응답 생성
    if st.session_state.chat_engine:
        with st.chat_message("assistant"):
            with st.spinner("답변 생성 중..."):
                response = st.session_state.chat_engine.chat(prompt)
                st.markdown(response.response)
                st.session_state.messages.append({"role": "assistant", "content": response.response})
    else:
        with st.chat_message("assistant"):
            st.markdown("먼저 문서를 업로드하거나 기존 문서를 선택해주세요.")
            st.session_state.messages.append({"role": "assistant", "content": "먼저 문서를 업로드하거나 기존 문서를 선택해주세요."})

# 대화 초기화 버튼
if st.button("대화 초기화"):
    st.session_state.messages = []
    st.experimental_rerun()

# 파일 전체 내용 설명 기능
if st.session_state.current_file and st.button("파일 전체 내용 설명"):
    if st.session_state.chat_engine:
        with st.spinner("파일 내용 분석 중..."):
            prompt = "이 문서의 전체 내용을 상세히 요약해서 설명해주세요."
            response = st.session_state.chat_engine.chat(prompt)
            
            st.subheader("파일 내용 설명")
            st.write(response.response)
            
            # 대화 기록에 추가
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.messages.append({"role": "assistant", "content": response.response})

# 고급 분석 기능 (추가 기능)
if st.session_state.current_file:
    with st.expander("고급 분석 옵션", expanded=False):
        if st.button("주요 키워드 추출"):
            if st.session_state.chat_engine:
                with st.spinner("키워드 추출 중..."):
                    prompt = "이 문서에서 가장 중요한 10개의 키워드를 추출하고 각각에 대해 간략히 설명해주세요."
                    response = st.session_state.chat_engine.chat(prompt)
                    st.write(response.response)
        
        if st.button("핵심 질문 생성"):
            if st.session_state.chat_engine:
                with st.spinner("질문 생성 중..."):
                    prompt = "이 문서의 내용을 바탕으로 독자가 가질 수 있는 5가지 중요한 질문을 생성해주세요."
                    response = st.session_state.chat_engine.chat(prompt)
                    st.write(response.response)

# 사용 안내
with st.expander("사용 방법", expanded=False):
    st.markdown("""
    ### 사용 방법
    1. **파일 업로드**: 사이드바에서 PDF, TXT, DOCX 파일을 업로드하세요.
    2. **파일 선택**: 업로드된 파일 목록에서 파일을 선택하세요.
    3. **질문하기**: 선택한 문서에 대해 질문을 입력하세요.
    4. **파일 관리**: 파일 목록에서 파일을 보거나 삭제할 수 있습니다.
    5. **전체 내용 설명**: '파일 전체 내용 설명' 버튼을 클릭하여 문서 전체 내용을 요약해서 볼 수 있습니다.
    
    ### 팁
    - 구체적인 질문을 하면 더 정확한 답변을 받을 수 있습니다.
    - 대화는 연속적으로 이어집니다. 이전 질문을 참조할 수 있습니다.
    - 대화 초기화 버튼을 사용하여 새로운 대화를 시작할 수 있습니다.
    """)

# 푸터
st.markdown("---")
st.markdown("LlamaIndex와 Streamlit으로 만든 문서 기반 챗봇 | 개발: 2023")