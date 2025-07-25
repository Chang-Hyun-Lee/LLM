import os
import streamlit as st
import openai
import json
from pykrx import stock
import requests # Ensure requests is imported for API calls 
import pandas as pd 
from langchain import hub
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import tool
from langchain_core.callbacks import Callbacks
from langchain_core.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

def get_fuzzy_ticker_from_name(partial_name: str) -> tuple[str, str]:
    """부분 종목명으로 가장 유사한 종목명을 찾아 종목코드와 함께 반환"""
    partial_name = partial_name.strip()
    tickers = stock.get_market_ticker_list()
    
    candidates = [
        (ticker, stock.get_market_ticker_name(ticker))
        for ticker in tickers
        if partial_name in stock.get_market_ticker_name(ticker)
    ]

    if not candidates:
        raise ValueError(f"입력하신 '{partial_name}' 에 해당하는 종목명을 찾을 수 없습니다.")

    # 정확히 일치하는 게 있으면 그걸 우선 반환
    for ticker, name in candidates:
        if name == partial_name:
            return ticker, name

    # 아니면 가장 앞에 있는 후보를 반환
    return candidates[0]

@tool
def get_market_ohlcv(start_date: str, end_date: str, stock_name: str) -> str:
    """입력한 종목명과 날짜로 주가 정보를 반환합니다. 날짜 형식은 'YYYYMMDD'"""
    start_date = start_date.strip()
    end_date = end_date.strip()
    stock_name = stock_name.strip()

    try:
        ticker, matched_name = get_fuzzy_ticker_from_name(stock_name)
    except ValueError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

    df = stock.get_market_ohlcv(start_date, end_date, ticker)
    if df.empty:
        return json.dumps({"error": "해당 날짜 범위에 데이터가 없습니다."}, ensure_ascii=False)

    df['종목명'] = matched_name
    return json.dumps(df.to_dict(orient='records'), ensure_ascii=False)

@st.cache_resource
def init_agent():
    openai.api_key = os.getenv("OPENAI_API_KEY")
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0, streaming=True)
    prompt = hub.pull("hwchase17/openai-tools-agent")
    prompt.messages[0] = SystemMessagePromptTemplate.from_template("당신은 주식 분석가입니다. 주어진 정보를 보고 주식에 대한 의견을 전달하세요.")

    tools = [get_market_ohlcv]
    agent = create_openai_tools_agent(
        model.with_config({"tags": ["agent_llm"]}), tools, prompt
    )
    agent_executor = AgentExecutor(agent=agent, tools=tools).with_config(
        {"run_name": "Agent"}
    )
    return model, prompt, tools, agent, agent_executor

def chat_with_bot(agent_executor, history):
    response = agent_executor.invoke({"input": {history[-1]["content"]}})
    return response["output"]

def main():
    st.title("Multi-turn Chatbot with Streamlit and OpenAI(+ Stock)")
    st.chat_input(placeholder="대화를 입력해주세요.", key="chat_input")

    model, prompt, tools, agent, agent_executor = init_agent()

    if "messages" not in st.session_state:
        st.session_state.messages = []        

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_input := st.session_state["chat_input"]:
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content":user_input})

        with st.spinner('답변을 준비중입니다 ... '):
            response = chat_with_bot(agent_executor, st.session_state.messages)
        with st.chat_message("assistant"):
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content":response})

if __name__ == "__main__":
    main()
