# 실습 #1: Streamlit과 LangChain agent를 사용하여 예전에 만들었던 특정 종목의 주가를 분석해주는 어플리케이션을 작성하시오.
# 실습 #2: Streamlit과 LangChain agent를 사용하여 예전에 만들었던 레스토랑을 찾아서 검색해주는 어플리케이션을 작성하시오.
# 실습 #3: Streamlit과 LangChain agent를 사용하여 예전에 만들었던 캠핑장을 추천해주는 어플리케이션을 작성하시오.


import streamlit as st
import os
import openai
from langchain.agents import initialize_agent, Tool
from langchain.llms import OpenAI
import yfinance as yf
from io import StringIO


openai.api_key = os.getenv("OPENAI_API_KEY")


# NVIDIA 주가 데이터 함수
def get_ohlcv_data(query=None):
    ticker = yf.Ticker("NVDA")  # nvidia 주가
    df = ticker.history(period="3m")  # 최근 3개월 OHLCV 데이터
    csv_buffer = StringIO()
    df.to_csv(csv_buffer)
    return csv_buffer.getvalue()

# Tool 정의
get_ohlcv = Tool(
    name="get_ohlcv_data",
    func=get_ohlcv_data,  # 함수 객체 그대로 사용
    description="NVIDIA의 최근 3개월 주가 OHLCV 데이터를 CSV 형식으로 반환한다."
)

# LLM 및 Agent 초기화
llm = OpenAI(temperature=0)
tools = [get_ohlcv]
agent = initialize_agent(tools, llm, agent="zero-shot-react-description", verbose=True)

# Streamlit 메시지 상태 초기화
if "messages" not in st.session_state:
    st.session_state["messages"] = []

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_input = st.chat_input("메시지를 입력하세요...")

if user_input:
    # 사용자 입력 저장
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Agent 실행
    prompt = user_input
    response = agent.run(prompt)

    # 응답 저장
    st.session_state["messages"].append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.write(response)


# nvidia의 최신 주가 3개월치 데이터를 보고 분석한 내용을 자세히 한글로 말해줘




