import os
import streamlit as st
from openai import OpenAI
from pykrx import stock
from datetime import datetime, timedelta

# OpenAI 클라이언트 생성
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="📈 주가 분석기 (전체 종목)", layout="wide")
st.title("📊 종목명/코드 입력형 대화형 주가 분석기 (KOSPI/KOSDAQ)")

# 1. KOSPI + KOSDAQ 종목 리스트 불러오기 (종목코드-종목명 딕셔너리 생성)
@st.cache_data(ttl=3600)
def load_tickers():
    kospi = stock.get_market_ticker_list(market="KOSPI")
    kosdaq = stock.get_market_ticker_list(market="KOSDAQ")
    tickers = kospi + kosdaq
    names = {}
    for t in tickers:
        name = stock.get_market_ticker_name(t)
        names[t] = name
    return names

tickers = load_tickers()

# 2. 입력값이 종목코드인지 종목명인지 판단하고 종목코드를 리턴하는 함수
def resolve_ticker(user_input):
    user_input = user_input.strip()
    # 종목코드는 보통 6자리 숫자
    if user_input.isdigit() and len(user_input) == 6:
        if user_input in tickers:
            return user_input
        else:
            return None
    else:
        # 종목명 기준으로 부분 일치 검색 (앞에서부터 가장 매칭 높은 걸로)
        matched = [code for code, name in tickers.items() if user_input in name]
        if matched:
            return matched[0]  # 첫 번째 결과 반환
        else:
            return None

# 3. 주가 데이터 가져오기 함수
def get_stock_data(ticker, days=30):
    end = datetime.today()
    start = end - timedelta(days=days * 2)  # 여유 날짜 포함
    df = stock.get_market_ohlcv_by_date(
        start.strftime("%Y%m%d"), end.strftime("%Y%m%d"), ticker
    )
    df.reset_index(inplace=True)
    df = df.tail(days)
    df = df[['날짜', '시가', '고가', '저가', '종가', '거래량']]
    return df

# 4. 데이터 텍스트 변환 함수
def convert_data_to_text(df):
    text = ""
    for _, row in df.iterrows():
        text += (
            f"{row['날짜'].strftime('%Y-%m-%d')}: 시가 {row['시가']:,}, "
            f"고가 {row['고가']:,}, 저가 {row['저가']:,}, 종가 {row['종가']:,}, "
            f"거래량 {row['거래량']:,}\n"
        )
    return text

# 5. GPT 분석 요청 함수
def ask_gpt_analysis(ticker, name, data_text):
    prompt = (
        f"다음은 한국 증시 종목 '{name}' (종목코드: {ticker})의 최근 주가 데이터입니다.\n"
        f"이 데이터를 분석하여 추세, 특징적인 변동, 이상치 및 투자자 관점의 인사이트를 알려주세요.\n\n"
        f"{data_text}"
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "당신은 전문적인 주식 데이터 분석가입니다."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
        max_tokens=1024,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    return response.choices[0].message.content

# --- Streamlit UI ---

user_input = st.text_input("종목명 또는 종목코드 입력 (예: 삼성전자 또는 005930)")

days = st.slider("분석 기간 (일)", min_value=5, max_value=365, value=30, step=1)

if st.button("분석 시작"):
    if not user_input:
        st.warning("종목명 또는 종목코드를 입력해 주세요.")
    else:
        ticker = resolve_ticker(user_input)
        if not ticker:
            st.error("종목코드 또는 종목명을 찾을 수 없습니다. 정확히 입력해 주세요.")
        else:
            st.write(f"선택된 종목: {tickers[ticker]} ({ticker})")
            with st.spinner("주가 데이터 불러오는 중..."):
                df = get_stock_data(ticker, days)
                if df.empty:
                    st.error("주가 데이터를 불러오지 못했습니다.")
                else:
                    data_text = convert_data_to_text(df)
                    st.text_area("주가 데이터 (텍스트)", data_text, height=300)
                    with st.spinner("GPT 분석 중... 잠시만 기다려 주세요."):
                        analysis = ask_gpt_analysis(ticker, tickers[ticker], data_text)
                    st.subheader("GPT 주가 분석 결과")
                    st.write(analysis)
