#실습 #1: Streamlit과 LangChain agent를 사용하여 예전에 만들었던 특정 종목의 주가를 분석해주는 어플리케이션을 작성하시오.

# 필요한 라이브러리 임포트
import os
import streamlit as st
import openai
import json
from pykrx import stock

# LangChain 관련 라이브러리
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

# LangChain Tool 정의: 주어진 종목코드의 시세 데이터를 불러오는 함수
@tool
def get_market_ohlcv(start_date, end_date, ticker):
    """
    주어진 시작일과 종료일 사이의 종목 시세 정보를 반환합니다.
    날짜 형식: 'YYYYMMDD'
    """
    start_date = start_date.strip()
    end_date = end_date.strip()
    ticker = ticker.strip()
    
    stock_name = stock.get_market_ticker_name(ticker)  # 종목명 가져오기
    df = stock.get_market_ohlcv(start_date, end_date, ticker)  # 시세 데이터 가져오기
    df['종목명'] = [stock_name] * len(df)  # 종목명 컬럼 추가

    # JSON 형태로 반환
    return json.dumps(df.to_dict(orient='records'), ensure_ascii=False)

# Streamlit에서 리소스를 캐시해서 재실행 시 초기화를 피함
@st.cache_resource
def init_agent():
    # OpenAI API 키 설정
    openai.api_key = os.getenv("OPENAI_API_KEY")
    
    # GPT-4o-mini 모델 로딩 (LangChain의 ChatOpenAI 사용)
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0, streaming=True)

    # LangChain Hub에서 프롬프트 템플릿 로드 후 시스템 프롬프트 변경
    prompt = hub.pull("hwchase17/openai-tools-agent")
    prompt.messages[0] = SystemMessagePromptTemplate.from_template(
        "당신은 주식 분석가입니다. 주어진 정보를 보고 주식에 대한 의견을 전달하세요."
    )

    tools = [get_market_ohlcv]  # 사용할 도구 목록에 위에서 만든 도구 추가

    # 도구와 함께 LangChain Agent 구성
    agent = create_openai_tools_agent(
        model.with_config({"tags": ["agent_llm"]}), tools, prompt
    )
    agent_executor = AgentExecutor(agent=agent, tools=tools).with_config(
        {"run_name": "Agent"}
    )

    return model, prompt, tools, agent, agent_executor

# 챗봇에 메시지를 전달하고 응답을 받아오는 함수
def chat_with_bot(agent_executor, history):
    # 가장 마지막 메시지를 agent에 전달
    response = agent_executor.invoke({"input": {history[-1]["content"]}})
    return response["output"]

# Streamlit 앱 메인 함수
def main():
    st.title("Multi-turn Chatbot with Streamlit and OpenAI(+ Stock)")

    # 사용자 입력 필드
    st.chat_input(placeholder="대화를 입력해주세요.", key="chat_input")

    # Agent 초기화
    model, prompt, tools, agent, agent_executor = init_agent()

    # 메시지 세션 상태 초기화
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 이전 대화 내용 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 사용자의 새로운 입력 처리
    if user_input := st.session_state["chat_input"]:
        # 사용자 메시지 표시 및 세션에 저장
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        # 챗봇 응답 생성
        with st.spinner('답변을 준비중입니다 ... '):
            response = chat_with_bot(agent_executor, st.session_state.messages)
        with st.chat_message("assistant"):
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

# 메인 함수 실행
if __name__ == "__main__":
    main()
