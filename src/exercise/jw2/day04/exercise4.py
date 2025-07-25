# 실습 #4: Streamlit과 LangChain agent를 사용하여 예전에 만들었던 특정 종목의 주가를 분석해주는 어플리케이션을 작성하시오. 티커코드가 아닌 종목명으로 주가를 찾을 수 있도록 하시오. 종목명이 약간 틀려도 주가를 찾을 수 있어야 한다.
# 예) 엘지전자, (주)엘지전자, 주식회사 LG전자, LG 전자, LG전자(주) ... 엘쥐전자

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

# Streamlit 메시지 상태 초기화
if "messages" not in st.session_state:
    st.session_state["messages"] = []

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_input = st.chat_input("메시지를 입력하세요...")

# NVIDIA 주가 데이터 함수
def get_ohlcv_data(query: str):
    ticker = yf.Ticker(query)
    df = ticker.history(period="3mo")  # 최근 2개월 OHLCV 데이터

    print(query)
    if df.empty or len(df) < 2:
            return f"'{query}'의 최근 2개월 주가 데이터를 가져올 수 없습니다."
    

    high, low, mean_close = df["High"].max(), df["Low"].min(), df["Close"].mean()
    trend = "상승 추세" if df["Close"].iloc[-1] > df["Close"].iloc[0] else "하락 추세"
    return (
            f"[{query}] 최근 3개월 분석 결과\n"
            f"- 최고가: {high:.2f}\n"
            f"- 최저가: {low:.2f}\n"
            f"- 평균 종가: {mean_close:.2f}\n"
            f"- 추세: {trend}\n"
        )

# Tool 정의
get_ohlcv = Tool(
    name="get_ohlcv_data",
    func=get_ohlcv_data,  # 함수 객체 그대로 사용
    description="특정 종목의 최근 2개월 OHLCV 데이터를 가져오며, 기술적 분석이나 데이터 분석 전에 반드시 이 도구를 사용해야 한다."
                "사용자가 입력한 내용에서 특정 종목의 티커(symbol)만 받아 최근 2개월 OHLCV 요약을 반환한다. "
                "이 도구는 주식 티커(symbol)만 입력으로 받습니다. 예: NVDA, AAPL, TSLA."
                "사용자 입력에서 회사명에 맡는 티커를 찾아서 입력으로 보내야합니다."
                "사용자 입력에서 오탈자는 알아서 수정해서 기업명을 찾아야해."
)

# LLM 및 Agent 초기화
llm = OpenAI(temperature=0)
tools = [get_ohlcv]
agent = initialize_agent(tools, llm, agent="zero-shot-react-description", verbose=True)

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


# nvidia의 최신 주가 2개월치 데이터를 보고 분석한 내용을 자세히 한글로 말해줘




