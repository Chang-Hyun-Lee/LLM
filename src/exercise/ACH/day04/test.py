import os
import streamlit as st
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.tools import tool

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    st.error("OPENAI_API_KEY 환경변수 없음")
    st.stop()

@tool
def general_search(query: str):
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=openai_api_key)
    return llm.predict(f"질문:{query}")

@st.cache_resource
def init_agent():
    try:
        st.warning("에이전트 초기화 중")  #← 이 메시지 보이면 정상
        # 아래 부분(프롬프트 등)은 일단 생략, general_search만 테스트
        # 필요시 여기에 print("step1") 등 삽입해가며 진행 상황 추적
        return general_search
    except Exception as e:
        st.error(f"에이전트 초기화 오류: {str(e)}")
        return None

def main():
    st.title("테스트 챗봇")
    executor = init_agent()
    if executor is None:
        st.stop()
    user_input = st.text_input("질문을 입력하세요")
    if user_input:
        st.write("사용자:", user_input)
        st.write("챗봇 응답:", executor(user_input))
if __name__ == "__main__":
    main()