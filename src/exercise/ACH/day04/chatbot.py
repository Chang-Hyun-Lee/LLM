import os
import streamlit as st
from llama_index import Document, GPTVectorStoreIndex, LLMPredictor, PromptHelper, ServiceContext
from langchain.chat_models import ChatOpenAI
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
    st.stop()

# 텍스트 파일 폴더에서 문서 불러오기
def load_documents_from_folder(folder_path):
    documents = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            with open(os.path.join(folder_path, filename), encoding="utf-8") as f:
                text = f.read()
                documents.append(Document(text))
    return documents

# LangChain + llama_index LLM 세팅
llm = ChatOpenAI(model_name="gpt-4", temperature=0, openai_api_key=OPENAI_API_KEY)
llm_predictor = LLMPredictor(llm=llm)
prompt_helper = PromptHelper(max_input_size=4096, num_output=512, max_chunk_overlap=20)
service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor, prompt_helper=prompt_helper)

# 인덱스 캐시 (docs 폴더 내 텍스트파일 기반)
@st.cache_resource(show_spinner=False)
def load_index():
    docs = load_documents_from_folder("docs")  # "docs" 폴더에 텍스트 파일 넣어주세요
    index = GPTVectorStoreIndex.from_documents(docs, service_context=service_context)
    return index

st.title("🤖 llama_index + LangChain 챗봇")

index = load_index()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

query = st.text_input("질문을 입력하세요:")

if st.button("전송") and query.strip() != "":
    with st.spinner("답변 생성 중..."):
        response = index.query(query)
        answer = response.response
        st.session_state.chat_history.append({"user": query, "bot": answer})

# 대화 내역 출력
for chat in st.session_state.chat_history:
    st.markdown(f"**사용자:** {chat['user']}")
    st.markdown(f"**챗봇:** {chat['bot']}")
    st.markdown("---")
