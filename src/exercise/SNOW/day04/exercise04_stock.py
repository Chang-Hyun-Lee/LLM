import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from langchain.chat_models import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import tool
from langchain_core.prompts import (
    ChatPromptTemplate, SystemMessagePromptTemplate,
    HumanMessagePromptTemplate, MessagesPlaceholder
)
from pykrx import stock
import yfinance as yf
import datetime
from pandas.tseries.offsets import BDay

# 📊 KRX 주식 정보 도구
@tool
def get_krx_summary(code: str):
    """한국거래소(KRX)에서 종목의 현재가, PER, EPS를 조회합니다."""
    try:
        date = (datetime.datetime.today() - BDay(1)).strftime("%Y%m%d")
        price = stock.get_market_ohlcv_by_date(date, date, code)["종가"].values[0]
        per = stock.get_market_fundamental_by_date(date, date, code)["PER"].values[0]
        eps = stock.get_market_fundamental_by_date(date, date, code)["EPS"].values[0]
        return {
            "현재가": price,
            "PER": per,
            "EPS": eps,
            "출처": "pykrx (KRX, 한국거래소)"
        }
    except Exception as e:
        return {"error": f"KRX 조회 오류: {str(e)}"}

# 🌍 해외 주식 정보 도구
@tool
def get_yfinance_info(ticker: str):
    """Yahoo Finance에서 종목의 재무정보를 조회합니다."""
    try:
        info = yf.Ticker(ticker).info
        return {
            "종목명": info.get("shortName", "N/A"),
            "현재가": info.get("currentPrice", "N/A"),
            "EPS": info.get("trailingEps", "N/A"),
            "PER": info.get("trailingPE", "N/A"),
            "시가총액": info.get("marketCap", "N/A"),
            "산업군": info.get("industry", "N/A"),
            "출처": "Yahoo Finance"
        }
    except Exception as e:
        return {"error": f"yfinance 조회 오류: {str(e)}"}

# 📈 해외 주가 그래프 도구
@tool
def get_yfinance_chart(ticker: str, period: str = "1y"):
    """Yahoo Finance에서 종목의 기간별 주가 추이를 조회합니다."""
    try:
        df = yf.Ticker(ticker).history(period=period).reset_index()
        if df.empty:
            return {"error": f"{ticker}의 시계열 데이터가 없습니다."}
        return df.to_dict()
    except Exception as e:
        return {"error": f"그래프 조회 오류: {str(e)}"}

# 📊 그래프 시각화 함수
def plot_chart(data, label):
    df = pd.DataFrame(data)
    if "Date" in df and "Close" in df and isinstance(df["Date"], pd.Series):
        df["Date"] = pd.to_datetime(df["Date"])
        plt.figure(figsize=(10, 4))
        plt.plot(df["Date"], df["Close"], label=label, color="green")
        plt.title(f"{label} 주가 추이")
        plt.xlabel("날짜")
        plt.ylabel("종가")
        plt.grid(True)
        st.pyplot(plt)
    else:
        st.warning("📭 유효한 그래프 데이터를 찾을 수 없습니다.")

# 🤖 GPT Agent 구성 (대화형 스타일)
@st.cache_resource
def setup_agent():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    tools = [get_krx_summary, get_yfinance_info, get_yfinance_chart]
    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(
            "당신은 친절하고 직관적인 금융 대화 파트너입니다. 사용자의 질문을 자연어로 이해하고, 해당 종목이나 지표를 인식해서 필요한 도구를 호출하세요. 감정, 투자 성향, 궁금증에 맞춰 따뜻하고 직관적인 해석과 조언을 제공하세요. 수치를 나열하기보다는 해석하고 질문을 제안하세요."
        ),
        HumanMessagePromptTemplate.from_template("{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])
    agent = create_openai_functions_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)

# 🚀 Streamlit 앱
def main():
    st.set_page_config(page_title="💬 GPT 대화형 주식 챗봇", page_icon="📈")
    st.title("📈 GPT 기반 대화형 주식 분석 챗봇")

    agent = setup_agent()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    query = st.chat_input("궁금한 주식 관련 질문을 자유롭게 입력하세요!")
    if query:
        with st.chat_message("user"):
            st.markdown(query)
        st.session_state.messages.append({"role": "user", "content": query})

        with st.spinner("🤔 GPT가 분석 중입니다..."):
            result = agent.invoke({"input": query})
            output = result.get("output", result)

        with st.chat_message("assistant"):
            if isinstance(output, dict) and "Date" in output and isinstance(output["Date"], list):
                plot_chart(output, "종목 그래프")
                st.markdown("📈 위 그래프를 참고해 주세요\n\n📜 출처: Yahoo Finance")
            elif isinstance(output, dict) and "error" in output:
                st.error(f"⚠️ {output['error']}")
            else:
                st.markdown(output)
        st.session_state.messages.append({"role": "assistant", "content": str(output)})

if __name__ == "__main__":
    main()