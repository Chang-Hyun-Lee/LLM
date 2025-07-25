import os
import streamlit as st
import json
from pykrx import stock

from langchain import hub
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import tool
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import SystemMessagePromptTemplate
from langchain_core.messages import HumanMessage, AIMessage

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

# ------- 주식 키워드 판별 -------
def is_stock_question(text):
    stock_keywords = [
        "주가", "코스피", "코스닥", "티커", "차트", "상장", "KRX", "PER", "EPS",
        "매출", "재무", "종목", "시가총액", "배당", "거래량", "가격", "주식", "적정가치", "투자",
        "삼성전자", "카카오", "네이버", "LG에너지", "현대차", "POSCO", "SK하이닉스"
    ]
    return any(k in text for k in stock_keywords)

# ------- 주식 Agent 초기화 -------
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
    return model, agent_executor

# ------- 메시지 변환 (Streamlit → LangChain) -------
def convert_to_langchain_messages(messages):
    langchain_msgs = []
    for m in messages:
        if m["role"] == "user":
            langchain_msgs.append(HumanMessage(content=m["content"]))
        elif m["role"] == "assistant":
            langchain_msgs.append(AIMessage(content=m["content"]))
    return langchain_msgs

# ------- 일반 LLM 멀티턴 처리 -------
def call_general_llm(messages):
    openai_api_key = os.getenv("OPENAI_API_KEY")
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=openai_api_key, streaming=False)
    langchain_messages = convert_to_langchain_messages(messages)
    return llm.predict_messages(langchain_messages).content

# ------- 주식 Agent 단발 처리 -------
def chat_with_bot(agent_executor, messages):
    # 현재 LangChain Agent는 멀티턴 지원이 약함 → 최신 user 메시지만 사용
    user_input = messages[-1]["content"]
    response = agent_executor.invoke({"input": user_input})
    return response["output"]

# ------- Streamlit App -------
def main():
    st.title("📈 멀티 챗봇: 주식 + 일반 대화")

    model, agent_executor = init_agent()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 이전 대화 출력
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 사용자 입력
    user_input = st.chat_input(placeholder="대화를 입력하세요.")
    if user_input:
        # 메시지 저장 및 출력
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # 응답 생성
        with st.spinner("답변을 생성 중입니다..."):
            if is_stock_question(user_input):
                response = chat_with_bot(agent_executor, st.session_state.messages)
            else:
                response = call_general_llm(st.session_state.messages)

        # 응답 저장 및 출력
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

# ------- 실행 -------
if __name__ == "__main__":
    main()
