# tool을 쓴다 => 에이전트를 사용한다.

#실습 #1: Streamlit과 LangChain agent를 사용하여 예전에 만들었던 특정 종목의 주가를 분석해주는 어플리케이션을 작성하시오.
#실습 #2: Streamlit과 LangChain agent를 사용하여 예전에 만들었던 레스토랑을 찾아서 검색해주는 어플리케이션을 작성하시오.
#실습 #3: Streamlit과 LangChain agent를 사용하여 예전에 만들었던 캠핑장을 추천해주는 어플리케이션을 작성하시오.

# tavily search는 export TAVILY_API_KEY= 로 설정하고 사용

import streamlit as st
from pykrx import stock
from datetime import datetime, timedelta
from langchain.tools import tool
from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain import hub

@tool
def stock_data(ticker : str) -> str:
    """ 주식 종목을 분석합니다 (ticker는 6자리 입니다. (예시 : '005930'))"""
    try:
        end = datetime.today()
        start = end - timedelta(days=7)

        df = stock.get_market_ohlcv_by_date(start.strftime('%Y%m%d'), end.strftime('%Y%m%d'), ticker)
        if df.empty:
            return f"{ticker}에 대한 데이터를 찾을 수 없습니다."
        
        summary = f"{ticker} 최근 종가 요약 : \n"
        df = df.tail(5)
        for date, row in df.iterrows():
            summary += f" - {date.date()} 종가 : {row['종가']:,}원"

        return summary
    except Exception as e:
        return f"에러 : {str(e)}"
    
from pykrx import stock

def name_to_ticker(name: str) -> str:
    """종목명을 티커로 변환 (예: '삼성전자' → '005930')"""
    tickers = stock.get_market_ticker_list()
    for ticker in tickers:
        if stock.get_market_ticker_name(ticker) == name:
            return ticker
    return None


# LangChain Agent 구성
llm = ChatOpenAI(model_name="gpt-4o", temperature=0)
tools = [stock_data]

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=False
)

# Streamlit 인터페이스 구성
st.set_page_config(page_title="한국 주식 분석 에이전트")
st.title("주식 분석 AI")
st.markdown("**주식 종목 입력해주세요 .**")

# 멀티턴 대화 저장
if "messages" not in st.session_state:
    st.session_state.messages = []

user_input = st.chat_input("입력해주세요. (예: 삼성전자 분석해줘)")

# 이전 메시지 렌더링
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 사용자 입력 처리
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 종목명을 티커로 변환
    query = user_input.strip()
    ticker = name_to_ticker(query)
    if ticker:
        query = ticker

    with st.chat_message("assistant"):
        with st.spinner("분석 중..."):
            response = agent.run(query)
            st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
