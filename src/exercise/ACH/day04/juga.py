import os
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from pykrx import stock
from dotenv import load_dotenv

from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
    st.stop()

llm = ChatOpenAI(model_name="gpt-4", temperature=0.7, openai_api_key=OPENAI_API_KEY)

st.title("📈 한국 주식 주가 분석기 (종목명 + 날짜 입력)")

def get_ticker_by_name(name):
    try:
        tickers = stock.get_market_ticker_list(market="KOSPI") + stock.get_market_ticker_list(market="KOSDAQ")
        names = {stock.get_market_ticker_name(t).strip(): t for t in tickers}
        return names.get(name.strip())
    except Exception:
        return None

# 세션 상태 초기화
if "submitted" not in st.session_state:
    st.session_state.submitted = False

with st.form("input_form"):
    stock_name = st.text_input("종목명 입력 (예: 삼성전자, 현대차, 카카오 등)", value="삼성전자")
    start_date = st.date_input("시작 날짜", value=pd.to_datetime("2024-01-01"))
    end_date = st.date_input("종료 날짜", value=pd.to_datetime("today"))
    submit = st.form_submit_button("분석 시작")

if submit:
    # 제출하면 상태 저장
    st.session_state.submitted = True
    st.session_state.stock_name = stock_name
    st.session_state.start_date = start_date
    st.session_state.end_date = end_date

if st.session_state.submitted:
    # 제출된 상태일 때만 실행
    stock_name = st.session_state.stock_name
    start_date = st.session_state.start_date
    end_date = st.session_state.end_date

    if start_date > end_date:
        st.error("시작 날짜는 종료 날짜보다 빠를 수 없습니다.")
        st.stop()

    ticker = get_ticker_by_name(stock_name)
    if not ticker:
        st.error(f"'{stock_name}' 종목을 찾을 수 없습니다. 정확한 종목명을 입력해 주세요.")
        st.stop()

    with st.spinner(f"'{stock_name}'({ticker}) 주가 데이터를 불러오는 중..."):
        df = stock.get_market_ohlcv_by_date(start_date.strftime("%Y%m%d"), end_date.strftime("%Y%m%d"), ticker)

    if df.empty:
        st.warning("해당 기간에 주가 데이터가 없습니다.")
        st.stop()

    df["MA20"] = df["종가"].rolling(window=20).mean()
    df["MA60"] = df["종가"].rolling(window=60).mean()

    st.subheader(f"📊 {stock_name} ({ticker}) 종가 및 이동평균선")
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(df.index, df["종가"], label="종가", color="black")
    ax.plot(df.index, df["MA20"], label="20일 이동평균", linestyle="--", color="blue")
    ax.plot(df.index, df["MA60"], label="60일 이동평균", linestyle="--", color="red")
    ax.set_xlabel("날짜")
    ax.set_ylabel("가격 (원)")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

    recent_df = df[["종가"]].tail(30)
    summary_text = recent_df.to_string()

    prompt = f"""
다음은 최근 30일간 '{stock_name}'의 종가 데이터입니다:

{summary_text}

이 데이터를 기반으로 아래 항목을 분석해 주세요:
1. 주가의 전반적인 추세는 어떤가요?
2. 투자자 입장에서 유의할 점은 무엇인가요?
3. 현재 시점에서의 간단한 투자 의견을 알려주세요.
"""

    st.subheader("🤖 GPT-4 주가 분석")

    with st.spinner("분석 중... 잠시만 기다려주세요."):
        system_message = SystemMessage(content="당신은 주식 분석 전문가입니다. 한국어로 친절하고 전문적으로 답변해 주세요.")
        human_message = HumanMessage(content=prompt)

        response = llm([system_message, human_message])
        analysis = response.content

        st.markdown("---")
        st.write(analysis)
