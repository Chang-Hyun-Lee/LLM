import os
import streamlit as st
from pathlib import Path
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.llms.openai import OpenAI

# 🔑 API 키 불러오기
openai_key = st.secrets["OPENAI_API_KEY"]

# 📁 문서 저장 경로
UPLOAD_DIR = Path("docs")
UPLOAD_DIR.mkdir(exist_ok=True)

# 🧠 세션 상태 초기화
for key, default in {
    "index": None,
    "query_engine": None,
    "chat_history": [],
    "selected_file": None
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

st.title("📚 GPT-4o-mini + LlamaIndex 문서 챗봇")
st.caption("파일 업로드, 요약, 멀티턴 대화 및 삭제 기능 포함")

# 📤 파일 다중 업로드
uploaded_files = st.file_uploader("파일 업로드", type=["pdf", "txt", "md"], accept_multiple_files=True)
if uploaded_files:
    for uploaded_file in uploaded_files:
        file_path = UPLOAD_DIR / uploaded_file.name
        with open(file_path, "wb") as f:
            f.write(uploaded_file.read())
    st.success(f"✅ {len(uploaded_files)}개 파일 업로드 완료!")
    st.rerun()

# 📋 파일 리스트 및 선택
files = sorted(UPLOAD_DIR.glob("*"))
file_names = [f.name for f in files]
selected = st.selectbox("문서 선택", file_names if file_names else ["(파일 없음)"])

# 🧹 선택된 파일 삭제
if selected and selected != "(파일 없음)":
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("삭제"):
            os.remove(UPLOAD_DIR / selected)
            st.success(f"`{selected}` 삭제됨")
            st.rerun()

# ⏳ 선택된 파일의 인덱스 재생성
if selected != "(파일 없음)" and selected != st.session_state.selected_file:
    try:
        file_path = UPLOAD_DIR / selected
        docs = SimpleDirectoryReader(input_files=[file_path]).load_data()
        llm = OpenAI(model="gpt-4o-mini", api_key=openai_key)
        index = VectorStoreIndex.from_documents(docs)
        query_engine = index.as_query_engine(llm=llm)

        st.session_state.index = index
        st.session_state.query_engine = query_engine
        st.session_state.selected_file = selected
        st.session_state.chat_history = []

        st.success("📚 인덱스 생성 완료!")
    except Exception as e:
        st.error(f"❗ 인덱스 오류: {e}")

# 💬 챗봇 UI
if st.session_state.query_engine:
    if not st.session_state.chat_history:
        st.markdown("👋 문서를 선택하고 질문을 입력하면 챗봇이 응답합니다.")

    for q, a in st.session_state.chat_history:
        with st.chat_message("user"):
            st.markdown(q)
        with st.chat_message("assistant"):
            st.markdown(a)

    user_input = st.chat_input("질문을 입력하세요")
    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)
        try:
            response = st.session_state.query_engine.query(user_input).response
        except Exception as e:
            response = f"❗ 응답 오류: {e}"
        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.chat_history.append((user_input, response))

    # 📝 요약 요청 버튼
    if st.button("문서 요약 받기"):
        with st.chat_message("user"):
            st.markdown("이 문서를 요약해줘")
        try:
            summary = st.session_state.query_engine.query("이 문서를 요약해줘").response
        except Exception as e:
            summary = f"❗ 요약 오류: {e}"
        with st.chat_message("assistant"):
            st.markdown(summary)
        st.session_state.chat_history.append(("이 문서를 요약해줘", summary))

# 🧪 상태 디버그 (사이드바)
st.sidebar.header("🔍 상태 보기")
st.sidebar.write("📄 선택된 문서:", st.session_state.selected_file or "없음")
st.sidebar.write("🧠 Query Engine:", "✅ 있음" if st.session_state.query_engine else "❌ 없음")
st.sidebar.write("📜 대화 수:", len(st.session_state.chat_history))