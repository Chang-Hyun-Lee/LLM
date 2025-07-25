import streamlit as st
from pykrx import stock
from datetime import datetime, timedelta
from langchain.chat_models import ChatOpenAI
from langchain.agents import Tool, initialize_agent
from langchain.agents.agent_types import AgentType
from langchain.tools import tool
from rapidfuzz import process
from dateparser import parse as date_parse
import re
import os

# OpenAI 키 설정
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")  

# 종목명 - 코드 매핑
@st.cache_data
def get_name_code_map():
    tickers = stock.get_market_ticker_list(market="ALL")
    return {stock.get_market_ticker_name(code): code for code in tickers}

name_code_map = get_name_code_map()

# 종목명 유사도 기반 자동 매칭
def find_closest_korean_ticker(user_input, name_code_map):
    match, score, _ = process.extractOne(user_input, name_code_map.keys())
    if score > 70:
        return match, name_code_map[match]
    return None, None

# 자연어에서 기간 추출
def extract_dates_from_input(text):
    today = datetime.today()
    start, end = None, today

    # '올해'
    if "올해" in text:
        start = datetime(today.year, 1, 1)
    elif "작년" in text:
        start = datetime(today.year - 1, 1, 1)
        end = datetime(today.year - 1, 12, 31)

    # 'n월부터' 또는 'yyyy년 n월부터'
    range_match = re.findall(r"(\d{4}년)?\s*(\d{1,2})월부터", text)
    if range_match:
        year_part, month_part = range_match[0]
        year = today.year if not year_part else int(re.sub(r"[^\d]", "", year_part))
        month = int(month_part)
        start = datetime(year, month, 1)

    # 전체 날짜 범위 파싱 (예: 2023년 6월부터 2024년 5월까지)
    date_range = re.findall(r"(\d{4}년\s*\d{1,2}월)", text)
    if len(date_range) == 2:
        start = date_parse(date_range[0])
        end = date_parse(date_range[1])

    if not start:
        start = today - timedelta(days=180)

    return start.strftime("%Y%m%d"), end.strftime("%Y%m%d")

# pykrx 주가 분석 함수
@tool
def get_korean_stock_summary(user_input: str) -> str:
    """
    사용자 입력으로부터 종목명과 기간을 추출하여 주가 정보를 요약합니다.
    """
    matched_name, matched_code = find_closest_korean_ticker(user_input, name_code_map)
    if not matched_code:
        return "종목명을 정확히 인식하지 못했습니다. 다시 입력해 주세요."

    start_str, end_str = extract_dates_from_input(user_input)
    df = stock.get_market_ohlcv_by_date(start_str, end_str, matched_code)

    if df.empty:
        return f"{matched_name}({matched_code})의 데이터를 찾을 수 없습니다."

    avg_price = df['종가'].mean()
    max_price = df['종가'].max()
    min_price = df['종가'].min()
    recent_price = df['종가'][-1]

    return f"""
📈 **{matched_name} ({matched_code})** 주가 요약  
기간: {start_str} ~ {end_str}

- 📌 최근 종가: {recent_price:,.0f}원
- 📊 평균 종가: {avg_price:,.0f}원
- 🔼 최고 종가: {max_price:,.0f}원
- 🔽 최저 종가: {min_price:,.0f}원
- 📅 거래일 수: {len(df)}일
"""

# LangChain Agent 설정
llm = ChatOpenAI(temperature=0.3, model="gpt-4o-mini")
tools = [get_korean_stock_summary]
agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=False)

# Streamlit UI
st.set_page_config(page_title="한국 주식 챗봇", layout="centered")
st.title("국장에도 미래는 있는가?")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("예: '작년부터 LG전자 주가 알려줘'")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    response = agent.run(user_input)

    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)