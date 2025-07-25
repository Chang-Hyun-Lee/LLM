# stock_tool.py

import pandas as pd
import yfinance as yf
from pykrx import stock
from langchain.tools import tool

@tool
def analyze_stock_data(official_name: str, ticker: str, start_date: str, end_date: str, market: str) -> dict:
    """
    주어진 티커와 기간에 대한 주식 데이터를 분석합니다.
    """
    print(f"🤖 데이터 분석 실행: 티커='{ticker}', 시장='{market}'")
    
    df = pd.DataFrame()
    try:
        if market == "KR":
            df = stock.get_market_ohlcv_by_date(start_date.replace("-", ""), end_date.replace("-", ""), ticker)
            df.reset_index(inplace=True)
            df = df.rename(columns={"날짜": "Date", "종가": "Close"})
        elif market == "US":
            df = yf.download(ticker, start=start_date, end=end_date, group_by='column')
            df.reset_index(inplace=True)

    except Exception as e:
        return {"error": f"'{ticker}'에 대한 데이터 수집 중 오류 발생: {e}"}

    if df.empty or 'Close' not in df.columns or df['Close'].isnull().all():
        return {"error": f"'{official_name}({ticker})'의 주가 데이터를 해당 기간에 찾을 수 없습니다."}
    
    df.dropna(subset=['Close'], inplace=True)
    if len(df) < 2:
        return {"error": "분석을 위해 최소 2일 이상의 데이터가 필요합니다."}
        
    df["Date"] = pd.to_datetime(df["Date"])
    
    start_price = df["Close"].iloc[0]
    end_price = df["Close"].iloc[-1]
    change = end_price - start_price
    percent_change = (change / start_price) * 100 if start_price != 0 else 0
    direction = "상승" if change > 0 else "하락"
    market_name = "한국" if market == "KR" else "미국"
    period_str = f"{df['Date'].min().strftime('%Y-%m-%d')} ~ {df['Date'].max().strftime('%Y-%m-%d')}"

    report = (f"**📈 {official_name} ({market_name}) 분석 요약**\n\n- **분석 기간**: {period_str}\n- **주가 변동**: {start_price:,.2f}에서 {end_price:,.2f}으로, 기간 내 **{percent_change:.2f}% {direction}**했습니다.\n- **최고가/최저가**: 기간 내 최고가는 {df['Close'].max():,.2f}, 최저가는 {df['Close'].min():,.2f}이었습니다.")

    return {"report": report, "chart_data": df[["Date", "Close"]].to_json(orient="split", date_format="iso")}