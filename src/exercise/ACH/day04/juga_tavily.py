import os
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import requests
from dotenv import load_dotenv
from pykrx import stock
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

# -------- 초기 설정 --------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not OPENAI_API_KEY or not TAVILY_API_KEY:
    st.error("❌ 'OPENAI_API_KEY' 또는 'TAVILY_API_KEY' 환경변수가 설정되지 않았습니다.")
    st.stop()

# Tavily API 호출 함수 (requests 사용)
def tavily_search(query, country="KR", top_k=5):
    url = "https://api.tavily.com/v1/search/stocks"  # 실제 API 문서 확인 필요
    headers = {
        "Authorization": f"Bearer {TAVILY_API_KEY}"
    }
    params = {
        "query": query,
        "country": country,
        "top_k": top_k
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        raise Exception(f"Tavily API 오류: {response.status_code} {response.text}")
    return response.json()

# -------- Streamlit 앱 UI --------
st.set_page_config(page_title="한국 주식 분석기", layout="wide")
st.title("📈 한국 주식 주가 분석기 (Tavily + pykrx + GPT)")
st.write("아래 항목을 입력 후 '분석 시작' 버튼을 누르면 분석이 실행됩니다.")

# -- 입력 폼 --
stock_input = st.text_input("① 종목명 입력 (예: 삼성전자, 현대차)")
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("② 시작 날짜", value=pd.to_datetime("2024-01-01"))
with col2:
    end_date = st.date_input("③ 종료 날짜", value=pd.to_datetime("today"))

analyze_btn = st.button("🔍 분석 시작")

# GPT 세팅
llm = ChatOpenAI(model_name="gpt-4", openai_api_key=OPENAI_API_KEY)

# -------- 분석 로직 --------
if analyze_btn:
    try:
        if not stock_input:
            st.warning("종목명을 입력해 주세요.")
            st.stop()

        # Tavily API로 종목 검색
        with st.spinner("종목을 검색하는 중..."):
            search_result = tavily_search(stock_input)
        suggestions = search_result.get("results", [])
        if not suggestions:
            st.warning("종목을 찾을 수 없습니다. 다시 입력해주세요.")
            st.stop()

        # 종목 선택 UI
        selection = st.selectbox("종목 선택", [f"{item['name']} ({item['ticker']})" for item in suggestions])
        ticker = selection.split("(")[1].strip(")")

        if start_date > end_date:
            st.warning("시작 날짜는 종료 날짜보다 빠를 수 없습니다.")
            st.stop()

        # pykrx 데이터 조회
        with st.spinner("주가 데이터를 불러오는 중..."):
            df = stock.get_market_ohlcv_by_date(
                start_date.strftime("%Y%m%d"),
                end_date.strftime("%Y%m%d"),
                ticker
            )
        if df.empty:
            st.error("❌ 해당 기간에 주가 데이터가 없습니다.")
            st.stop()

        # 차트 그리기
        df["MA20"] = df["종가"].rolling(20).mean()
        df["MA60"] = df["종가"].rolling(60).mean()
        st.subheader(f"{stock_input} ({ticker}) 종가 및 이동평균선")
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(df.index, df["종가"], label="종가", color="black")
        ax.plot(df.index, df["MA20"], label="20일 MA", linestyle="--", color="blue")
        ax.plot(df.index, df["MA60"], label="60일 MA", linestyle="--", color="red")
        ax.set_xlabel("날짜")
        ax.set_ylabel("가격 (원)")
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)

        # 최근 30일 종가 요약
        recent = df["종가"].tail(30)
        summary_text = recent.to_string()

        prompt = f"""
다음은 최근 30일간 '{stock_input}'({ticker}) 의 종가 데이터입니다:

{summary_text}

다음을 분석해 주세요:
1. 주가의 전반적인 추세는 어떤가요?
2. 투자자가 유의해야 할 점은 무엇인가요?
3. 현재 시점에서 간단한 투자 의견을 알려주세요.
"""

        st.subheader("🧠 GPT 분석 결과")
        with st.spinner("GPT로 분석 중..."):
            resp = llm([
                SystemMessage(content="당신은 한국 주식 시장 전문가입니다."),
                HumanMessage(content=prompt)
            ])
            st.write(resp.content)

    except Exception as e:
        st.error(f"❌ 오류 발생: {e}")
