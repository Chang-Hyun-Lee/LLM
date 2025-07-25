# app.py

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
from io import StringIO
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
from stock_database import get_stock_database
from stock_tool import analyze_stock_data
import utils_input_AIcheck as utils
from pykrx import stock

# --- 🎨 Claude.ai 스타일 CSS ---
CLAUDE_CSS = """
<style>
    .stApp { background-color: #191919; color: #EAEAEB; }
    h1, h2, h3 { color: #FFFFFF; }
    .st-emotion-cache-16txtl3 { background-color: #2A2A2B; }
    .stButton > button { background-color: #8874FF; color: #FFFFFF; border-radius: 12px; border: none; padding: 10px 16px; font-weight: bold; }
    .stButton > button:hover { background-color: #7A65E8; }
    .stTextInput > div > div > input, .stTextArea > div > div > textarea { background-color: #3C3C3D; color: #EAEAEB; border-radius: 8px; border: 1px solid #5A5A5B; }
    .stSlider > div > div > div > div { background-color: #8874FF; }
    .stAlert { border-radius: 12px; }
</style>
"""
st.markdown(CLAUDE_CSS, unsafe_allow_html=True)

# --- 페이지 설정 ---
st.set_page_config(page_title="AI 주식 분석기", page_icon="📊", layout="wide")
st.title("📈 AI 주식 분석기")

# --- 앱 시작 시 DB 로드 및 UI 처리 ---
# ✨ AttributeError 해결: get_stock_database가 반환하는 튜플을 올바르게 처리합니다.
stock_db_tuple = get_stock_database()
if stock_db_tuple and stock_db_tuple[0]:
    stock_db = stock_db_tuple[0]  # 튜플의 첫 번째 요소인 실제 DB를 사용합니다.
    is_newly_created = stock_db_tuple[1]
    if is_newly_created:
        st.toast("✅ 주식 데이터베이스 파일 생성 완료!", icon="🎉")
else:
    st.error("주식 데이터베이스를 로드할 수 없습니다. 인터넷 연결을 확인하거나, 잠시 후 다시 시도해주세요.")
    st.stop()

try:
    latest_business_day_str = stock.get_nearest_business_day_in_a_week()
    latest_business_day = datetime.strptime(latest_business_day_str, "%Y%m%d").date()
except Exception:
    latest_business_day = datetime.now().date() - timedelta(days=1)

@st.cache_resource
def get_agent():
    print("🚀 Agent를 초기화합니다...")
    try:
        llm = ChatOpenAI(model="gpt-4-turbo", temperature=0, openai_api_key=st.secrets["OPENAI_API_KEY"])
        tools = []
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful AI assistant specializing in financial data analysis. The user will provide you with a summary of stock data. Your role is to answer follow-up questions based *only* on the data provided by the user in the prompt."),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        agent = create_openai_tools_agent(llm, tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=True)
    except Exception as e:
        st.error(f"Agent 초기화 중 오류: {e}")
        return None

# --- 세션 상태 관리 ---
if "analysis_result" not in st.session_state: st.session_state.analysis_result = None
if "stock_name" not in st.session_state: st.session_state.stock_name = ""
if "history" not in st.session_state: st.session_state.history = []
if "suggestions" not in st.session_state: st.session_state.suggestions = []
if "analysis_params" not in st.session_state: st.session_state.analysis_params = None
if "stock_to_analyze" not in st.session_state: st.session_state.stock_to_analyze = None

def perform_analysis(official_name, ticker, market_code, start_date, end_date, period_selection_text):
    st.session_state.stock_name = official_name
    with st.spinner(f"{official_name} 주가 데이터를 분석 중입니다..."):
        start_date_str = start_date.strftime("%Y-%m-%d") if isinstance(start_date, (datetime, date)) else start_date
        end_date_str = end_date.strftime("%Y-%m-%d") if isinstance(end_date, (datetime, date)) else end_date
        result = analyze_stock_data.func(official_name=official_name, ticker=ticker, start_date=start_date_str, end_date=end_date_str, market=market_code)
        st.session_state.analysis_result = result
        if "error" not in result:
            history_entry = {"stock_name": official_name, "ticker": ticker, "period": period_selection_text, "result": result}
            is_duplicate = any(h['stock_name'] == official_name and h['period'] == period_selection_text for h in st.session_state.history)
            if not is_duplicate:
                st.session_state.history.insert(0, history_entry)
                st.session_state.history = st.session_state.history[:5]

def handle_suggestion_click(suggested_name):
    st.session_state.stock_to_analyze = {"official_name": suggested_name}
    st.session_state.suggestions = []
    
def clear_history():
    st.session_state.history = []

# --- UI 레이아웃 (사이드바) ---
with st.sidebar:
    with st.form(key="analysis_form"):
        st.header("📄 분석 설정")
        market_selection = st.radio("시장 선택", ["국내 주식", "미국 주식"], horizontal=True)
        placeholder_text = "예: 삼성전자, 엘지전자" if market_selection == "국내 주식" else "예: 엔비디아, TSLA"
        user_input_stock_name = st.text_input("분석할 종목명 또는 티커", placeholder=placeholder_text)
        
        with st.expander("ℹ️ 분석 기간 안내", expanded=False):
            st.caption(f"모든 분석은 최근 영업일({latest_business_day.strftime('%Y-%m-%d')})을 기준으로 수행됩니다.")

        period_options = ("1주일", "2주일", "1개월", "3개월", "6개월", "1년", "5년", "직접 설정")
        period_selection = st.selectbox("분석 기간 선택", period_options)
        
        start_date_input, end_date_input = None, None
        if period_selection == "직접 설정":
            st.caption("분석할 시작일과 종료일을 직접 선택하세요.")
            cols = st.columns(2)
            start_date_input = cols[0].date_input("시작일", latest_business_day - timedelta(days=30), max_value=latest_business_day)
            end_date_input = cols[1].date_input("종료일", latest_business_day, max_value=latest_business_day)
            
        analyze_button = st.form_submit_button("📊 주가 분석 실행")

    if st.session_state.suggestions:
        st.divider()
        st.subheader("혹시 이 종목을 찾으셨나요?")
        for suggested_name in st.session_state.suggestions:
            st.button(suggested_name, key=f"suggestion_{suggested_name}", use_container_width=True, on_click=handle_suggestion_click, args=(suggested_name,))

    st.divider()
    cols = st.columns([0.7, 0.3])
    cols[0].subheader("최근 분석 기록")
    if st.session_state.history:
        cols[1].button("삭제", on_click=clear_history, use_container_width=True)

    if not st.session_state.history:
        st.caption("분석 기록이 없습니다.")
    else:
        for i, entry in enumerate(st.session_state.history):
            button_text = f"🕒 {entry['stock_name']} ({entry.get('ticker', '')}) ({entry['period']})"
            if st.button(button_text, key=f"history_{i}", use_container_width=True):
                st.session_state.analysis_result = entry['result']
                st.session_state.stock_name = entry['stock_name']
                st.rerun()

# --- 분석 실행 제어 로직 ---
if analyze_button:
    st.session_state.suggestions = []
    st.session_state.stock_to_analyze = None
    if not user_input_stock_name.strip():
        st.warning("❗ 종목명을 입력해주세요.")
    else:
        market_code = "KR" if market_selection == "국내 주식" else "US"
        
        start_date, end_date = start_date_input, end_date_input
        period_text = period_selection
        if period_selection != "직접 설정":
            period_map = {"1주일": 7, "2주일": 14, "1개월": 30, "3개월": 90, "6개월": 182, "1년": 365, "5년": 1825}
            end_date = latest_business_day
            start_date = end_date - timedelta(days=period_map[period_selection])
        else:
            period_text = f"{start_date.strftime('%y.%m.%d')}~{end_date.strftime('%y.%m.%d')}"

        if start_date and end_date and start_date >= end_date:
            st.error("❗ 시작일은 종료일보다 빨라야 합니다.")
        else:
            st.session_state.analysis_params = {"market_code": market_code, "start_date": start_date, "end_date": end_date, "period_text": period_text}
            search_result = utils.find_closest_stock(user_input_stock_name, market_code, stock_db)
            
            if search_result["status"] == "exact":
                st.session_state.stock_to_analyze = search_result
            elif search_result["status"] == "suggestion":
                st.session_state.suggestions = search_result["suggestions"]
            elif search_result["status"] == "not_found":
                st.error(search_result["message"])

if st.session_state.stock_to_analyze:
    params = st.session_state.analysis_params
    stock_info = st.session_state.stock_to_analyze
    if params and stock_info:
        if "ticker" not in stock_info:
            market_code = params["market_code"]
            ticker = stock_db[market_code].get(stock_info["official_name"])
            stock_info["ticker"] = ticker

        perform_analysis(stock_info["official_name"], stock_info["ticker"], params["start_date"], params["end_date"], params["market_code"], params["period_text"])
    st.session_state.stock_to_analyze = None

# --- 분석 결과 및 Q&A 표시 ---
if st.session_state.analysis_result:
    result = st.session_state.analysis_result
    st.subheader("기본 분석 리포트")
    if "error" in result:
        st.error(result["error"])
    else:
        st.markdown(result["report"])
        chart_data = pd.read_json(StringIO(result["chart_data"]), orient="split")
        st.line_chart(chart_data.rename(columns={"Date": "index"}).set_index("index"))
        
        st.subheader("🤖 AI에게 추가 질문하기")
        agent_executor = get_agent()
        if agent_executor:
            user_question = st.text_input(
                "분석된 데이터에 대한 추가 질문을 입력하세요.",
                placeholder="예: 이 기간 동안의 투자 전략을 요약해줘",
                key=f"qa_input_{st.session_state.stock_name}"
            )
            if user_question:
                with st.spinner("AI가 답변을 생성 중입니다..."):
                    prompt_with_context = (
                        f"Here is the summary of the stock analysis for {st.session_state.stock_name}:\n"
                        f"{result['report']}\n\n"
                        f"Based on this data, please answer the following question: {user_question}"
                    )
                    try:
                        response = agent_executor.invoke({"input": prompt_with_context})
                        st.info(response.get("output", "답변을 생성하지 못했습니다."))
                    except Exception as e:
                        st.error(f"AI 답변 생성 중 오류 발생: {e}")
