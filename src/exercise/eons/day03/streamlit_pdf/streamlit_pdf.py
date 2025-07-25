# rag_chat_app.py
import streamlit as st
import os
import openai

from langchain.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS

# OpenAI API 키
openai.api_key = os.getenv("OPENAI_API_KEY")

# 벡터 DB 로드
embeddings = OpenAIEmbeddings()
db = FAISS.load_local("shower", embeddings=embeddings, allow_dangerous_deserialization=True)

# Streamlit 앱 제목
st.title("📚 RAG + GPT 멀티턴 스트리밍 챗봇")

# 세션 상태 초기화
if "history" not in st.session_state:
    st.session_state["history"] = []

# 이전 대화 출력
for user_msg, bot_msg in st.session_state["history"]:
    if user_msg:
        with st.chat_message("user"):
            st.markdown(user_msg)
    if bot_msg:
        with st.chat_message("assistant"):
            st.markdown(bot_msg)

# 사용자 입력 받기
user_input = st.chat_input("질문을 입력하세요.")

# GPT 스트리밍 함수
def stream_rag_gpt_response(text):
    content = "당신은 친절한 어시스턴트입니다. 주어진 데이터를 보고 사용자에 친절하게 대답하세요.\n"
    content += "*" * 50 + "\n"
    docs = db.similarity_search(text)
    for doc in docs:
        content += doc.page_content + "\n"
        content += "*" * 50 + "\n"

    messages = [
        {"role": "system", "content": content},
        {"role": "user", "content": text}
    ]

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.5,
        max_tokens=512,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stream=True
    )

    reply = ""
    for chunk in response:
        delta = chunk.choices[0].delta
        if delta and delta.content:
            reply += delta.content
            yield reply

# 입력이 있을 경우 처리
if user_input:
    # 사용자 메시지 출력
    with st.chat_message("user"):
        st.markdown(user_input)

    # GPT 응답 출력 영역
    with st.chat_message("assistant"):
        msg_box = st.empty()
        full_reply = ""
        for partial in stream_rag_gpt_response(user_input):
            full_reply = partial
            msg_box.markdown(full_reply)

    # 세션에 대화 저장
    st.session_state["history"].append([user_input, full_reply])

# 대화 초기화 버튼
if st.button("🔄 대화 초기화"):
    st.session_state["history"] = []
    st.rerun()
