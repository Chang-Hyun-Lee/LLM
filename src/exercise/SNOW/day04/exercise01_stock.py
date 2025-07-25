import streamlit as st
from pykrx import stock
from datetime import datetime
from langchain.agents import initialize_agent, AgentType, Tool
from langchain_experimental.tools.python.tool import PythonREPLTool
from langchain_community.chat_models import ChatOpenAI
import difflib

# 🔐 OpenAI API 키 불러오기
openai_key = st.secrets["OPENAI_API_KEY"]

# 🌟 LangChain Agent 초기화 (GPT-4o-mini + 파싱 오류 복구)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7, api_key=openai_key)
tools = [PythonREPLTool()]
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=False,
    handle_parsing_errors=True  # ✅ 파싱 오류 시 자동 복구
)

# 🧭 종목명 → 종목코드 변환 맵
@st.cache_data
def get_name_to_code_map():
    tickers = stock.get_market_ticker_list()
    return {stock.get_market_ticker_name(t): t for t in tickers}

# 🎨 Streamlit UI
st.title("📈 종목명 기반 GPT-4o-mini 주가 분석 챗봇")
input_name = st.text_input("종목명을 입력하세요 (예: 삼성전자, LG화학 등)")
col1, col2 = st.columns(2)
start = col1.date_input("시작일", datetime(2024, 1, 1))
end = col2.date_input("종료일", datetime(2024, 7, 1))

name_to_code = get_name_to_code_map()
matched_code = name_to_code.get(input_name)
similar_names = difflib.get_close_matches(input_name, name_to_code.keys(), n=3, cutoff=0.6)

# 🔍 분석 요청 버튼
if st.button("분석 요청"):
    if matched_code:
        try:
            df = stock.get_market_ohlcv_by_date(start.strftime("%Y%m%d"), end.strftime("%Y%m%d"), matched_code)
            if df.empty:
                st.warning("📭 데이터가 없습니다.")
            else:
                # 📊 요약
                avg_price = df["종가"].mean()
                max_price = df["종가"].max()
                min_price = df["종가"].min()

                summary = f"""
{input_name} 주가 분석 요약 ({start.strftime('%Y-%m-%d')} ~ {end.strftime('%Y-%m-%d')}):
- 평균 종가: {avg_price:,.0f}원
- 최고 종가: {max_price:,.0f}원
- 최저 종가: {min_price:,.0f}원
"""
                st.subheader("📃 요약 정보")
                st.text(summary)

                # 🧠 GPT 해석 요청 (Agent가 형식 미일치 시도 자동 복구)
                prompt = summary + "\n위 요약을 보고 투자자 관점에서 간단하고 명확하게 해석해줘."
                gpt_response = agent.run(prompt)

                st.subheader("🧠 GPT 해석")
                st.write(gpt_response)

                st.subheader("📈 종가 추이")
                st.line_chart(df["종가"])
        except Exception as e:
            st.error(f"❗ 오류 발생: {e}")
    else:
        st.warning(f"❌ '{input_name}'이라는 종목명을 찾을 수 없습니다.")
        if similar_names:
            st.info("🔍 유사한 종목명 추천:")
            for name in similar_names:
                st.write(f"- {name}")
        else:
            st.error("유사한 종목명이 없습니다.")