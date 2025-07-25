import streamlit as st
from pathlib import Path
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.settings import Settings
import os

# -------------------------------
# 1. 앱 설정 및 제목
# - 페이지 레이아웃을 'wide'로 설정합니다.
# - markdown을 사용하여 제목의 상단 여백을 최소화하고, 화면 상단에 가깝게 배치합니다.
# -------------------------------
st.set_page_config(page_title="업로드 파일 기반 챗봇", layout="wide")

# 제목의 여백을 줄여 화면 공간을 확보합니다.
st.markdown(
    """
    <style>
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: #F0F2F6;
            border-radius: 4px 4px 0px 0px;
            gap: 1px;
            padding-top: 10px;
            padding-bottom: 10px;
        }
        .stTabs [aria-selected="true"] {
            background-color: #FFFFFF;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    """
    <div style="padding: 0rem 0 1rem 0;">
        <h1 style='font-size: 2.5rem; margin-bottom: 0;'>📄 업로드 파일 기반 챗봇</h1>
    </div>
    """,
    unsafe_allow_html=True
)


# -------------------------------
# 2. 사이드바: OpenAI API 키 입력 및 파일 업로드
# -------------------------------
with st.sidebar:
    st.header("⚙️ 설정")
    # 사용자로부터 OpenAI API 키를 입력받습니다.
    openai_api_key = st.text_input("🔑 OpenAI API Key:", type="password")
    st.caption("API 키는 저장되지 않으며, 새로고침 시 다시 입력해야 합니다.")
    
    # API 키가 없으면 경고 메시지를 표시하고 앱 실행을 중지합니다.
    if not openai_api_key:
        st.warning("사이드바에 OpenAI API 키를 입력해주세요.")
        st.stop()

    # LlamaIndex 설정: LLM과 임베딩 모델을 지정합니다.
    try:
        Settings.llm = OpenAI(api_key=openai_api_key, model="gpt-3.5-turbo")
        Settings.embed_model = OpenAIEmbedding(api_key=openai_api_key, model="text-embedding-ada-002")
    except Exception as e:
        st.error(f"API 키 인증에 실패했습니다: {e}")
        st.stop()

    st.divider()

    # 파일 저장을 위한 디렉토리 경로 설정
    UPLOAD_DIR = Path("uploaded_files")
    INDEX_DIR = Path("indexes")
    UPLOAD_DIR.mkdir(exist_ok=True)
    INDEX_DIR.mkdir(exist_ok=True)

    # PDF 파일 업로더
    uploaded_files = st.file_uploader(
        "📂 PDF 파일 업로드", 
        type="pdf", 
        accept_multiple_files=True,
        help="분석하고 싶은 PDF 파일을 하나 이상 업로드하세요."
    )

    # 파일이 업로드되면 인덱싱을 수행합니다.
    if uploaded_files:
        with st.spinner("파일 처리 및 인덱싱 중... 잠시만 기다려주세요."):
            for file in uploaded_files:
                # 파일을 서버에 저장
                save_path = UPLOAD_DIR / file.name
                with open(save_path, "wb") as f:
                    f.write(file.getbuffer())

                # 저장된 파일을 LlamaIndex로 로드하고 인덱싱
                try:
                    docs = SimpleDirectoryReader(input_files=[str(save_path)]).load_data()
                    index = VectorStoreIndex.from_documents(docs)
                    # 인덱스를 파일 이름으로 된 디렉토리에 저장
                    index.storage_context.persist(persist_dir=str(INDEX_DIR / file.name))
                except Exception as e:
                    st.error(f"'{file.name}' 파일 인덱싱 중 오류 발생: {e}")
        
        st.success(f"✅ {len(uploaded_files)}개의 파일 업로드 및 인덱싱 완료!")


# -------------------------------
# 3. 탭 UI: 파일 정보, 관리 및 문서 분석
# - 탭 제목에 HTML/CSS를 사용하여 글자 크기를 키웁니다.
# -------------------------------
tab_titles = [
    "ℹ️ <span style='font-size:1.1rem'>시작하기</span>",
    "🗂️ <span style='font-size:1.1rem'>업로드된 파일</span>",
    "💬 <span style='font-size:1.1rem'>문서 기반 챗봇</span>"
]
tab1, tab2, tab3 = st.tabs([st.markdown(t, unsafe_allow_html=True) for t in tab_titles])

with tab1:
    st.markdown("### 챗봇 사용 방법")
    st.markdown("""
    1.  **API 키 입력**: 왼쪽 사이드바에 OpenAI API 키를 입력하세요.
    2.  **파일 업로드**: 사이드바의 'PDF 파일 업로드' 섹션에서 분석할 PDF 파일을 업로드합니다.
    3.  **인덱싱 확인**: 파일 업로드 후 인덱싱이 완료될 때까지 잠시 기다립니다.
    4.  **챗봇 사용**: '문서 기반 챗봇' 탭으로 이동하여 질문할 파일을 선택하고, 문서 내용에 대해 질문을 입력하세요.
    """)
    st.info("지원 파일 형식: **PDF**")

with tab2:
    st.markdown("#### 🔖 업로드 및 인덱싱된 파일 목록")
    indexed_files = [f.name for f in UPLOAD_DIR.glob("*.pdf")]
    if indexed_files:
        for f_name in indexed_files:
            st.markdown(f"📄 **{f_name}**")
    else:
        st.info("아직 업로드된 파일이 없습니다. 사이드바에서 파일을 업로드해주세요.")

with tab3:
    st.markdown("### 💬 문서 기반 챗봇")
    
    indexed_files = [f.name for f in UPLOAD_DIR.glob("*.pdf")]
    
    # 인덱싱된 파일이 없을 경우 안내 메시지 표시
    if not indexed_files:
        st.warning("먼저 사이드바에서 PDF 파일을 업로드하고 인덱싱을 완료해주세요.")
        st.stop()

    # 드롭다운 메뉴로 질문할 PDF 파일 선택
    selected_file = st.selectbox("📑 질문할 PDF 문서를 선택하세요:", indexed_files)

    if selected_file:
        try:
            # 선택된 파일에 해당하는 인덱스를 불러옵니다.
            index_path = INDEX_DIR / selected_file
            storage_context = StorageContext.from_defaults(persist_dir=str(index_path))
            index = load_index_from_storage(storage_context)
            
            # 스트리밍 응답을 위한 쿼리 엔진 생성
            query_engine = index.as_query_engine(streaming=True)

            # 채팅 기록을 세션 상태에 초기화
            if "messages" not in st.session_state:
                st.session_state.messages = {}
            if selected_file not in st.session_state.messages:
                st.session_state.messages[selected_file] = [{"role": "assistant", "content": f"'{selected_file}' 문서에 대해 무엇이든 물어보세요!"}]

            # 이전 대화 내용 표시
            for message in st.session_state.messages[selected_file]:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            # 사용자 질문 입력
            if prompt := st.chat_input("문서에 대해 질문을 입력하세요..."):
                # 사용자 질문을 채팅 기록에 추가하고 화면에 표시
                st.session_state.messages[selected_file].append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                # AI 답변 생성 및 표시
                with st.chat_message("assistant"):
                    with st.spinner("답변을 생성하는 중입니다..."):
                        response_stream = query_engine.query(prompt)
                        response_container = st.empty()
                        full_response = ""
                        # 스트리밍 응답을 실시간으로 화면에 표시
                        for text in response_stream.response_gen:
                            full_response += text
                            response_container.markdown(full_response)
                        
                # 전체 답변을 채팅 기록에 추가
                st.session_state.messages[selected_file].append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"'{selected_file}' 파일의 인덱스를 불러오는 중 오류가 발생했습니다: {e}")
            st.warning("파일을 다시 업로드하고 인덱싱해보세요.")

