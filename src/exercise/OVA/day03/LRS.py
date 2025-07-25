import streamlit as st
import yfinance as yf
import json
import os
from datetime import datetime, timedelta
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.tools import Tool
from langchain_community.tools.tavily_search import TavilySearchResults

# 페이지 설정
st.set_page_config(page_title="주식 분석 AI", page_icon="📈", layout="wide")

# 제목
st.title("📈 주식 분석 AI Assistant")
st.markdown("**LangChain Agent를 활용한 지능형 주식 분석 도구**")

# 사이드바 API 키 설정
with st.sidebar:
    st.header("🔑 API 설정")
    openai_key = st.text_input(
        "OpenAI API Key", 
        type="password", 
        value="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"
    )
    tavily_key = st.text_input(
        "Tavily API Key", 
        type="password", 
        value="asst_vKsnmuZX2sUZI9vhdSAEVCKT"
    )
    
    st.markdown("---")
    st.markdown("### 📋 지원 종목 예시")
    st.markdown("""
    **🇰🇷 한국 주식:**
    - 삼성전자, SK하이닉스
    - NAVER, 카카오
    - LG에너지솔루션, 현대차
    
    **🇺🇸 미국 주식:**
    - AAPL, MSFT, GOOGL
    - TSLA, NVDA, AMZN
    """)

# 한국 주식 매핑 딕셔너리
KOREAN_STOCKS = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS", 
    "NAVER": "035420.KS",
    "네이버": "035420.KS",
    "카카오": "035720.KS",
    "LG에너지솔루션": "373220.KS",
    "삼성바이오로직스": "207940.KS",
    "현대차": "005380.KS",
    "기아": "000270.KS",
    "POSCO홀딩스": "005490.KS",
    "LG화학": "051910.KS",
    "셀트리온": "068270.KS",
    "삼성SDI": "006400.KS",
    "KB금융": "105560.KS",
    "신한지주": "055550.KS",
    "하이브": "352820.KS",
    "CJ제일제당": "097950.KS"
}

def get_stock_symbol(stock_name):
    """한국 주식명을 야후 파이낸스 심볼로 변환"""
    return KOREAN_STOCKS.get(stock_name, stock_name)

def get_stock_data(stock_symbol, start_date, end_date):
    """
    yfinance를 사용하여 주가 데이터를 가져와서 분석하는 함수
    이전에 만들었던 함수를 기반으로 구현
    """
    try:
        # 한국 주식명을 심볼로 변환
        converted_symbol = get_stock_symbol(stock_symbol)
        
        # yfinance로 데이터 가져오기
        ticker = yf.Ticker(converted_symbol)
        data = ticker.history(start=start_date, end=end_date)
        
        if data.empty:
            return json.dumps({
                "error": f"'{stock_symbol}' 종목의 {start_date}~{end_date} 기간 데이터를 찾을 수 없습니다.",
                "suggestion": "종목명이나 기간을 확인해주세요."
            }, ensure_ascii=False, indent=2)
        
        # 주가 분석 계산
        current_price = round(data['Close'].iloc[-1], 2)
        start_price = round(data['Close'].iloc[0], 2)
        price_change = round(current_price - start_price, 2)
        price_change_percent = round((price_change / start_price) * 100, 2)
        
        highest_price = round(data['High'].max(), 2)
        lowest_price = round(data['Low'].min(), 2)
        avg_volume = int(data['Volume'].mean())
        
        # 변동성 계산
        daily_returns = data['Close'].pct_change()
        volatility = round(daily_returns.std() * 100, 2)
        
        # 회사 정보 가져오기
        try:
            info = ticker.info
            company_name = info.get('longName', converted_symbol)
            market_cap = info.get('marketCap')
        except:
            company_name = stock_symbol
            market_cap = None
        
        # 분석 결과 구성
        analysis_result = {
            "stock_symbol": converted_symbol,
            "company_name": company_name,
            "period": f"{start_date} ~ {end_date}",
            "current_price": current_price,
            "start_price": start_price,
            "price_change": price_change,
            "price_change_percent": price_change_percent,
            "highest_price": highest_price,
            "lowest_price": lowest_price,
            "average_volume": avg_volume,
            "volatility": volatility,
            "market_cap": market_cap,
            "total_trading_days": len(data),
            "trend": "상승" if price_change > 0 else "하락" if price_change < 0 else "보합"
        }
        
        return json.dumps(analysis_result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"주가 데이터 조회 중 오류 발생: {str(e)}",
            "stock_symbol": stock_symbol
        }, ensure_ascii=False, indent=2)

def stock_analysis_tool(query: str) -> str:
    """
    사용자 질문을 분석하여 종목과 기간을 추출하고 주가 분석을 수행하는 도구
    """
    try:
        # OpenAI를 사용해 사용자 질문에서 파라미터 추출
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=openai_key)
        
        today = datetime.now().strftime('%Y-%m-%d')
        three_months_ago = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        
        extract_prompt = f"""
사용자의 주식 분석 요청에서 다음 정보를 추출해주세요:

사용자 질문: "{query}"

다음 JSON 형식으로만 응답해주세요:
{{
    "stock_symbol": "종목명_또는_코드",
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD"
}}

추출 규칙:
1. 종목명: 사용자가 언급한 정확한 종목명 또는 코드 사용
2. 기간이 없으면: start_date="{three_months_ago}", end_date="{today}" (최근 3개월)
3. "2024년", "올해" 등이 있으면: start_date="2024-01-01", end_date="{today}"
4. 특정 월이 있으면 해당 월 1일부터 말일까지
5. 종목이 명확하지 않으면 stock_symbol을 "UNKNOWN"으로 설정

오늘 날짜: {today}
"""
        
        response = llm.invoke(extract_prompt)
        params = json.loads(response.content)
        
        # 종목이 지정되지 않은 경우 처리
        if params.get("stock_symbol") == "UNKNOWN":
            return "❌ 분석할 종목을 명확히 지정해주세요.\n\n예시: '삼성전자 주가 분석해줘', 'AAPL 최근 3개월 분석'"
        
        # 주가 데이터 분석 실행
        result_json = get_stock_data(
            params["stock_symbol"],
            params["start_date"], 
            params["end_date"]
        )
        
        # JSON 결과를 사용자 친화적 형태로 포맷팅
        result_data = json.loads(result_json)
        
        if "error" in result_data:
            return f"❌ 오류: {result_data['error']}\n💡 {result_data.get('suggestion', '')}"
        
        # 결과 포맷팅
        formatted_result = f"""
📊 **{result_data['company_name']} ({result_data['stock_symbol']})** 주가 분석 결과

📅 **분석 기간**: {result_data['period']}
💰 **현재가**: {result_data['current_price']:,}
📈 **시작가**: {result_data['start_price']:,}
🔺 **변동**: {result_data['price_change']:+,} ({result_data['price_change_percent']:+.2f}%)

📊 **주요 지표**:
- 🔺 최고가: {result_data['highest_price']:,}
- 🔻 최저가: {result_data['lowest_price']:,}
- 📊 평균 거래량: {result_data['average_volume']:,}주
- 📈 변동성: {result_data['volatility']}%
- 📅 거래일수: {result_data['total_trading_days']}일
- 🎯 추세: **{result_data['trend']}**
"""
        
        if result_data.get('market_cap'):
            formatted_result += f"- 💎 시가총액: {result_data['market_cap']:,}\n"
            
        return formatted_result
        
    except Exception as e:
        return f"❌ 주식 분석 중 오류가 발생했습니다: {str(e)}"

def analyze_stock_with_agent(user_query):
    """
    LangChain Agent를 사용하여 사용자 질문을 분석하고 적절한 도구를 호출
    """
    if not openai_key or not tavily_key:
        return "❌ API 키를 모두 입력해주세요."
    
    try:
        # 환경변수로 API 키 설정
        os.environ["TAVILY_API_KEY"] = tavily_key
        
        # LLM 초기화
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=openai_key)
        
        # 도구 정의
        stock_tool = Tool(
            name="stock_analysis",
            description="특정 종목의 주가 데이터를 분석합니다. 종목명과 기간이 포함된 질문에 사용하세요.",
            func=stock_analysis_tool
        )
        
        search_tool = TavilySearchResults(
            max_results=3,
            description="최신 주식 뉴스나 시장 정보를 검색합니다."
        )
        
        tools = [stock_tool, search_tool]
        
        # 에이전트 프롬프트
        prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 전문적인 주식 분석 AI입니다.

사용 가능한 도구:
1. stock_analysis: 특정 종목의 주가 데이터를 분석 (yfinance 기반)
2. tavily_search_results_json: 최신 주식 뉴스나 시장 정보 검색

사용자 질문을 분석하여:
- 특정 종목의 주가 분석 요청 → stock_analysis 도구 사용
- 최신 뉴스나 일반적인 시장 정보 요청 → tavily_search_results_json 도구 사용
- 필요시 두 도구를 모두 사용하여 종합적인 분석 제공

항상 친절하고 전문적으로 답변하세요."""),
            ("user", "{input}"),
            ("assistant", "{agent_scratchpad}")
        ])
        
        # 에이전트 생성 및 실행
        agent = create_openai_tools_agent(llm, tools, prompt)
        executor = AgentExecutor(agent=agent, tools=tools, verbose=False)
        
        result = executor.invoke({"input": user_query})
        return result["output"]
        
    except Exception as e:
        return f"❌ Agent 실행 오류: {str(e)}"

# 메인 UI
st.markdown("---")

# 예제 질문 섹션
st.subheader("💡 예제 질문")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("삼성전자 분석", use_container_width=True):
        st.session_state.query = "삼성전자 주가를 최근 3개월간 분석해줘"

with col2:
    if st.button("애플 주식 분석", use_container_width=True):
        st.session_state.query = "AAPL 2024년 주가 분석해줘"

with col3:
    if st.button("테슬라 분석", use_container_width=True):
        st.session_state.query = "TSLA 주식 최근 6개월 분석"

with col4:
    if st.button("주식 뉴스", use_container_width=True):
        st.session_state.query = "한국 주식시장 최신 뉴스 알려줘"

# 사용자 입력
st.markdown("### 🎯 주식 분석 질문")
user_input = st.text_input(
    "분석하고 싶은 종목과 기간을 입력하세요:",
    value=st.session_state.get('query', ''),
    placeholder="예: 삼성전자 2024년 주가 분석해줘 / SK하이닉스 최근 6개월 분석 / NVDA 주식 분석"
)

# 분석 실행
if st.button("🔍 AI 분석 시작", type="primary", use_container_width=True):
    if user_input.strip():
        with st.spinner("🤖 AI Agent가 분석 중입니다..."):
            result = analyze_stock_with_agent(user_input)
            
        st.markdown("### 📊 분석 결과")
        st.markdown(result)
    else:
        st.warning("⚠️ 분석할 종목과 질문을 입력해주세요.")

# 하단 정보
st.markdown("---")
with st.expander("ℹ️ 사용법 및 정보"):
    st.markdown("""
    ### 🚀 사용법
    1. **종목 지정**: 한글명(삼성전자) 또는 영문 코드(AAPL) 입력
    2. **기간 설정**: "최근 3개월", "2024년", "6개월간" 등으로 표현
    3. **질문 형태**: "삼성전자 주가를 2024년 분석해줘" 형태로 입력
    
    ### 📈 분석 항목
    - 현재가, 시작가, 변동률
    - 최고가, 최저가
    - 평균 거래량, 변동성
    - 추세 분석
    
    ### 🔧 기술 스택
    - **Streamlit**: 웹 인터페이스
    - **LangChain Agent**: 지능형 질문 처리
    - **yfinance**: 실시간 주가 데이터
    - **OpenAI GPT**: 자연어 처리
    - **Tavily**: 최신 뉴스 검색
    """)

# API 키 상태 표시
if openai_key and tavily_key:
    st.success("✅ 모든 API 키가 설정되었습니다. 분석을 시작할 수 있습니다!")
else:
    st.error("❌ 사이드바에서 API 키를 입력해주세요.")