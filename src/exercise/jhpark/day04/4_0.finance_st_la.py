import os
from datetime import datetime, timedelta
import streamlit as st
from pykrx import stock
from langchain.agents import Tool, initialize_agent

from langchain.agents.agent_types import AgentType
from langchain.chat_models import ChatOpenAI

# --- PyKRX 기반 주가 분석 함수 ---
def analyze_stock_data(stock_code, start_date, end_date):
    # Fetch stock data
    df = stock.get_market_ohlcv(start_date, end_date, stock_code)
    
    # Convert DataFrame to CSV format
    csv_buffer = StringIO()
    df.to_csv(csv_buffer)
    csv_data = csv_buffer.getvalue()
    
    # Analyze stock data using OpenAI API
    response = openai.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
    {
      "role": "system",
      "content": "다음은 {stock_code}의 날짜별 주가 데이터야. 2024년 12월부터 2025년 1월까지 주가를 분석해줘."
    },
    {
      "role": "user",
      "content": csv_data
    }
  ],
  temperature=0,
  max_tokens=1024,
  top_p=1,
  frequency_penalty=0,
  presence_penalty=0
)

# --- LangChain Tool 정의 ---
tools = [
    Tool(
        name="GetStockAnalysis",
        func=analyze_stock_data,
        description="주식 종목 코드를 입력받아 최근 주가를 분석해주는 도구입니다. 예: '005930'"
    )
]


agent = initialize_agent(
    tools,
    response,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=False
)

# --- Streamlit 앱 시작 ---
def main():
    st.title("📈 주가 분석 챗봇")
    st.write("주식 종목 코드를 입력하면 최근 주가를 분석해드립니다. 예: 005930 (삼성전자)")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 채팅 메시지 렌더링
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 사용자 입력 처리
    user_input = st.chat_input("종목 코드를 입력해주세요 (예: 005930)")
    if user_input:
        # 사용자 메시지 저장 및 출력
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # LangChain 에이전트 실행
        response = agent.run(user_input)

        # 봇 메시지 저장 및 출력
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

if __name__ == "__main__":
    main()
