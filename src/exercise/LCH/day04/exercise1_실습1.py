import streamlit as st
import yfinance as yf
import pandas as pd

from langchain.agents import initialize_agent, Tool
from langchain.chat_models import ChatOpenAI
from langchain.agents.agent_types import AgentType

# 🔑 OpenAI API 키 입력
import os
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="📈 주가 분석 에이전트", layout="wide")
st.title("특정 종목 주가 분석 with LangChain Agent")

# 🎯 종목 코드 입력
ticker = st.text_input("종목 코드를 입력하세요 (예: AAPL, MSFT, TSLA)", value="TSLA")

if ticker:
    # 🧾 데이터 불러오기
    data = yf.Ticker(ticker).history(period="12mo")
    st.subheader(f"최근 6개월 주가 차트 ({ticker})")
    st.line_chart(data["Close"])

    # 🛠️ LangChain 분석 에이전트 설정

    # 📊 툴 1: 최근 종가 통계 요약
    def describe_stock():
        avg = data["Close"].mean()
        high = data["Close"].max()
        low = data["Close"].min()
        return f"""
        최근 6개월 동안 {ticker} 종목의 평균 종가는 {avg:.2f}입니다.
        최고가는 {high:.2f}, 최저가는 {low:.2f}입니다.
        """

    tools = [
        Tool(
            name="Stock Summary Tool",
            func=lambda x: describe_stock(),
            description="주가 데이터에 대한 간단한 통계를 알려주는 도구입니다.",
        ),
    ]

    # 💬 에이전트 초기화
    llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")

    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=False
    )

    # 📩 분석 요청
    st.subheader("🧠 분석 질문")
    user_query = st.text_input("LangChain 에이전트에게 질문해보세요", value="최근 주가 흐름은 어때?")
    
    if st.button("분석 실행"):
        with st.spinner("분석 중..."):
            result = agent.run(user_query)
            st.success("✅ 분석 완료")
            st.markdown(result)