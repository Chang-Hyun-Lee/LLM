# 실습 #4: Streamlit과 LangChain agent를 사용하여 예전에 만들었던 특정 종목의 주가를 분석해주는 어플리케이션을 작성하시오. 티커코드가 아닌 종목명으로 주가를 찾을 수 있도록 하시오. 종목명이 약간 틀려도 주가를 찾을 수 있어야 한다.
# 예) 엘지전자, (주)엘지전자, 주식회사 LG전자, LG 전자, LG전자(주) ...
#엘쥐전자

import os
import json
import streamlit as st
from datetime import datetime, timedelta

from pykrx import stock
from fuzzywuzzy import process
from langchain import hub
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import tool
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import SystemMessagePromptTemplate


# 종목명 → 티커 찾기 (유사도 기반)
def find_ticker_by_name_fuzzy(user_input):
    tickers = stock.get_market_ticker_list()
    name_dict = {code: stock.get_market_ticker_name(code) for code in tickers}
    # 이름 목록에서 best match
    name_list = list(name_dict.values())
    best_match, score = process.extractOne(user_input, name_list)
    for code, name in name_dict.items():
        if name == best_match:
            return code, name
    return None, None


# LangChain Tool: 주가 분석
@tool
def get_stock_summary_by_name(stock_name: str) -> str:
    """
    유저가 입력한 종목명(예: '엘쥐전자', 'LG 전자')으로 최근 주가를 요약합니다.
    """
    try:
        ticker, matched_name = find_ticker_by_name_fuzzy(stock_name)
        if ticker is None:
            return f"[{stock_name}]에 해당하는 종목을 찾을 수 없습니다."

        end = datetime.today()
        start = end - timedelta(days=10)
        df = stock.get_market_ohlcv_by_date(start.strftime("%Y%m%d"), end.strftime("%Y%m%d"), ticker)
        df = df.tail(5)

        summary = f"[{matched_name}] ({ticker}) 최근 5일 종가 요약:\n"
        for date, row in df.iterrows():
            summary += f"- {date.date()} 종가: {row['종가']:,}원\n"
        return summary

    except Exception as e:
        return f"에러 발생: {str(e)}"


# LangChain Agent 초기화
@st.cache_resource
def init_agent():
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0, streaming=True)
    prompt = hub.pull("hwchase17/openai-tools-agent")
    prompt.messages[0] = SystemMessagePromptTemplate.from_template("""
        너는 주식 데이터 분석 도우미야.
        사용자가 한국 주식 종목명을 입력하면, 주가 데이터를 요약 및 분석해서 알려줘.
        종목명이 약간 틀렸더라도 유사한 종목을 찾아 분석해줘.
    """)
    tools = [get_stock_summary_by_name]
    agent = create_openai_tools_agent(model, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools)


# Streamlit
def main():
    st.title("종목명 기반 주가 분석 챗봇")
    user_input = st.chat_input("예: 엘쥐전자, LG전자(주), 삼성전자는 어때요?")

    agent_executor = init_agent()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.spinner("주가 분석 중..."):
            response = agent_executor.invoke({"input": user_input})
        with st.chat_message("assistant"):
            st.markdown(response["output"])
            st.session_state.messages.append({"role": "assistant", "content": response["output"]})


if __name__ == "__main__":
    main()
