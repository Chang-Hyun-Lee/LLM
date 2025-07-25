import os
import json
import streamlit as st
from datetime import datetime, timedelta
from pykrx import stock

from langchain import hub
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import tool
from langchain.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.tools.tavily_search import TavilySearchResults

# ✅ 종목명 → 티커 자동 변환용 딕셔너리 생성
@st.cache_data
def get_ticker_dict():
    tickers = stock.get_market_ticker_list("KOSPI") + stock.get_market_ticker_list("KOSDAQ")
    return {stock.get_market_ticker_name(t): t for t in tickers}

# ✅ 주가 조회 Tool (LangChain Agent가 사용할 수 있음)
@tool
def get_stock_price_data(ticker: str, days: int = 30):
    """지정한 티커에 대해 최근 N일간 주가 데이터(OHLVC)를 조회합니다."""
    end = datetime.today()
    start = end - timedelta(days=days * 2)  # 주말 포함 고려
    df = stock.get_market_ohlcv(start.strftime('%Y%m%d'), end.strftime('%Y%m%d'), ticker)
    df = df.tail(days)
    df = df.reset_index()
    df["날짜"] = df["날짜"].dt.strftime("%Y-%m-%d")
    return json.dumps(df.to_dict(orient="records"), ensure_ascii=False)

# ✅ 에이전트 초기화
@st.cache_resource
def init_agent():
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0, streaming=True)
    prompt = hub.pull("hwchase17/openai-tools-agent")

    # 시스템 메시지 간결하게 설정
    prompt.messages[0].prompt.template = (
        "너는 주식 분석 전문가야. 사용자의 메시지에서 종목명을 추출하고 주가 데이터를 기반으로 분석해줘."
        " 필요 시 주가 조회 도구(get_stock_price_data)를 활용해."
    )

    tools = [get_stock_price_data, TavilySearchResults(k=3)]
    agent = create_openai_tools_agent(model, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    return executor

# ✅ Chat 수행 함수
def chat_with_agent(agent_executor, user_input):
    return agent_executor.invoke({"input": user_input})["output"]

# ✅ 메인 앱
def main():
    st.set_page_config(page_title="📈 주가 분석 챗봇", layout="wide")
    st.title("📊 한국 주식 분석 GPT 챗봇")

    ticker_dict = get_ticker_dict()
    agent_executor = init_agent()

    # 🔹 사용자 입력
    user_input = st.chat_input("분석할 종목명이나 질문을 입력하세요 (예: '삼성전자 최근 주가 어때?')")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 🔹 대화 기록 출력
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 🔹 입력 처리
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.spinner("GPT가 분석 중입니다..."):
            try:
                response = chat_with_agent(agent_executor, user_input)
            except Exception as e:
                response = f"❌ 오류 발생: {e}"

        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

if __name__ == "__main__":
    main()
