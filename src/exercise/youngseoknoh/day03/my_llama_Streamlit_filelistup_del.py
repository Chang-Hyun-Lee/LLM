import os
import shutil
import streamlit as st
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

# 업로드 디렉토리 설정
UPLOAD_DIR = "uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

st.set_page_config(page_title="📄 LlamaIndex 파일 QA", layout="wide")
st.title("📄 LlamaIndex 기반 문서 질문응답")

# 파일 업로드
st.sidebar.header("📤 문서 업로드")
uploaded_files = st.sidebar.file_uploader("파일을 업로드하세요", type=["pdf", "txt", "md"], accept_multiple_files=True)

if uploaded_files:
    for file in uploaded_files:
        with open(os.path.join(UPLOAD_DIR, file.name), "wb") as f:
            f.write(file.read())
    st.sidebar.success("파일 업로드 완료!")

# 업로드된 파일 리스트업
st.sidebar.header("📚 업로드된 파일 목록")
file_list = os.listdir(UPLOAD_DIR)

if file_list:
    selected_files = st.sidebar.multiselect("❌ 삭제할 파일 선택", file_list)

    # 파일 삭제
    if st.sidebar.button("삭제 실행"):
        if selected_files:
            for filename in selected_files:
                file_path = os.path.join(UPLOAD_DIR, filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
            st.sidebar.success("선택한 파일이 삭제되었습니다.")
            st.rerun()

    st.sidebar.markdown("#### 현재 파일:")
    for f in file_list:
        st.sidebar.markdown(f"- {f}")
else:
    st.sidebar.info("업로드된 파일이 없습니다.")

# 문서 인덱싱 및 QA
if file_list:
    with st.spinner("🔍 문서를 불러오고 인덱스를 만드는 중..."):
        documents = SimpleDirectoryReader(UPLOAD_DIR).load_data()
        index = VectorStoreIndex.from_documents(documents)
        query_engine = index.as_query_engine()

    st.markdown("## 💬 질문을 입력하세요")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_input = st.chat_input("무엇을 도와드릴까요?")
    if user_input:
        # 대화 기록에 추가
        st.session_state.chat_history.append(("user", user_input))

        with st.spinner("🤔 답변 생성 중..."):
            response = query_engine.query(user_input)
            st.session_state.chat_history.append(("bot", response.response))

    # 대화 내역 출력
    for role, msg in st.session_state.chat_history:
        with st.chat_message(role):
            st.markdown(msg)
else:
    st.info("왼쪽 사이드바에서 파일을 업로드하면 질문할 수 있어요.")
