import os
import streamlit as st
import json
from pykrx import stock

from langchain import hub
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import tool
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import SystemMessagePromptTemplate

# ------- 주식 도구 -------
@tool
def get_market_ohlcv(start_date, end_date, ticker):
    """Return prices within given dates for ticker stock. start_date and end_date should be 'YYYYMMDD' format."""
    start_date = start_date.strip()
    end_date = end_date.strip()
    ticker = ticker.strip()
    stock_name = stock.get_market_ticker_name(ticker)
    df = stock.get_market_ohlcv(start_date, end_date, ticker)
    df['종목명'] = [stock_name] * len(df)
    return json.dumps(df.to_dict(orient='records'), ensure_ascii=False)

# ------- 주식 키워드로 질문인지 판별 -------
def is_stock_question(text):
    stock_keywords = ["주가", "코스피", "코스닥", "티커", "차트", "상장", "KRX", "PER", "EPS",
                      "매출", "재무", "종목", "시가총액", "배당", "거래량", "가격", "주식", "적정가치", "투자",
                      "삼성전자", "카카오", "네이버", "LG에너지", "현대차", "POSCO", "SK하이닉스"]
    return any(k in text for k in stock_keywords)

# ------- 주식 Agent -------
@st.cache_resource
def init_agent():
    openai_api_key = os.getenv("OPENAI_API_KEY")
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=openai_api_key, streaming=False)
    prompt = hub.pull("hwchase17/openai-tools-agent")
    prompt.messages[0] = SystemMessagePromptTemplate.from_template(
        "당신은 숙련된 주식 분석가입니다. 종목, 차트, 주가, 기업 등 주식 및 투자 관련 정보를 요청받으면 전문적으로 의견을 내어 분석해 주세요."
    )
    tools = [get_market_ohlcv]
    agent = create_openai_tools_agent(
        model.with_config({"tags": ["agent_llm"]}), tools, prompt
    )
    agent_executor = AgentExecutor(agent=agent, tools=tools).with_config(
        {"run_name": "Agent"}
    )
    return model, prompt, tools, agent, agent_executor

# ------- 일반 LLM 직접 호출 -------
def call_general_llm(question):
    openai_api_key = os.getenv("OPENAI_API_KEY")
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=openai_api_key, streaming=False)
    return llm.predict(question)

def chat_with_bot(agent_executor, history):
    response = agent_executor.invoke({"input": history[-1]["content"]})
    return response["output"]

def main():
    st.title("멀티 챗: 주식 + 일반 대화")

    model, prompt, tools, agent, agent_executor = init_agent()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_input = st.chat_input(placeholder="대화를 입력해주세요.", key="chat_input")
    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content":user_input})

        with st.spinner('답변을 준비중입니다 ... '):
            if is_stock_question(user_input):
                response = chat_with_bot(agent_executor, st.session_state.messages)
            else:
                # 일반 질문: LLM 직접 호출
                response = call_general_llm(user_input)
        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content":response})

if __name__ == "__main__":
    main()