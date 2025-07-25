import streamlit as st
import pandas as pd
from pykrx import stock
import json
import re
from datetime import datetime, timedelta
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.tools import Tool

# 페이지 설정
st.set_page_config(page_title="한국 주식 분석 AI", page_icon="🇰🇷", layout="wide")

def normalize_company_name(name):
    """
    회사명을 정규화하여 검색 가능한 형태로 변환
    """
    if not name:
        return ""
    
    # 기본 정리
    normalized = name.strip()
    
    # 괄호와 법인 형태 제거
    patterns_to_remove = [
        r'\([^)]*\)',  # (주), (유) 등
        r'㈜\s*', r'\s*㈜',  # 주식회사 기호
        r'주식회사\s*', r'\s*주식회사',  # 주식회사
        r'\(주\)\s*', r'\s*\(주\)',  # (주)
        r'\(유\)\s*', r'\s*\(유\)',  # (유)
    ]
    
    for pattern in patterns_to_remove:
        normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE)
    
    # 공백 정리
    normalized = re.sub(r'\s+', '', normalized)
    
    # 한글 표기 통일
    replacements = {
        '엘지': 'LG', '엘쥐': 'LG',
        '에스케이': 'SK', 
    }
    
    for korean, standard in replacements.items():
        normalized = normalized.replace(korean, standard)
    
    return normalized.strip()

@st.cache_data(ttl=3600)  # 1시간 캐시
def get_all_stock_codes():
    """
    PyKRX를 사용해 모든 한국 주식 종목 코드와 이름 가져오기
    """
    try:
        # KOSPI + KOSDAQ 전체 종목 가져오기
        kospi_codes = stock.get_market_ticker_list(market="KOSPI")
        kosdaq_codes = stock.get_market_ticker_list(market="KOSDAQ")
        
        all_codes = kospi_codes + kosdaq_codes
        
        # 종목명 정보 가져오기
        stock_info = {}
        for ticker in all_codes:
            try:
                name = stock.get_market_ticker_name(ticker)
                if name:
                    stock_info[ticker] = name
            except:
                continue
                
        return stock_info
    except Exception as e:
        st.error(f"주식 데이터 로딩 중 오류: {e}")
        return {}

def search_stock_by_name(company_name, stock_info):
    """
    회사명으로 주식 코드 검색
    """
    normalized_input = normalize_company_name(company_name)
    
    # 완전 일치 검색
    for ticker, name in stock_info.items():
        if normalized_input == normalize_company_name(name):
            return ticker, name
    
    # 부분 일치 검색
    candidates = []
    for ticker, name in stock_info.items():
        normalized_name = normalize_company_name(name)
        if normalized_input in normalized_name or normalized_name in normalized_input:
            candidates.append((ticker, name, len(normalized_name)))
    
    # 이름이 가장 짧은 것(대표 종목) 우선
    if candidates:
        candidates.sort(key=lambda x: x[2])
        return candidates[0][0], candidates[0][1]
    
    # 키워드 검색
    keywords = ['전자', '화학', '바이오', '에너지', '텔레콤', '자동차', '건설', '금융']
    for keyword in keywords:
        if keyword in normalized_input:
            for ticker, name in stock_info.items():
                normalized_name = normalize_company_name(name)
                if keyword in normalized_name and any(comp in normalized_name for comp in ['삼성', 'LG', 'SK', '현대']):
                    return ticker, name
    
    return None, None

def get_stock_data_pykrx(stock_name, start_date, end_date):
    """
    PyKRX를 사용하여 한국 주식 데이터 분석
    """
    try:
        # 전체 주식 정보 로딩
        with st.spinner("주식 데이터를 로딩중입니다..."):
            stock_info = get_all_stock_codes()
        
        if not stock_info:
            return json.dumps({
                "error": "주식 데이터를 불러올 수 없습니다.",
                "suggestion": "잠시 후 다시 시도해주세요."
            }, ensure_ascii=False, indent=2)
        
        # 종목 검색
        ticker, company_name = search_stock_by_name(stock_name, stock_info)
        
        if not ticker:
            # 유사한 종목명 제안
            suggestions = []
            normalized_input = normalize_company_name(stock_name)
            for t, name in list(stock_info.items())[:10]:  # 상위 10개만 체크
                if any(keyword in normalize_company_name(name) for keyword in normalized_input.split()):
                    suggestions.append(name)
            
            return json.dumps({
                "error": f"'{stock_name}' 종목을 찾을 수 없습니다.",
                "suggestion": "다음 종목들을 확인해보세요: " + ", ".join(suggestions[:5]) if suggestions else "종목명을 정확히 입력해주세요."
            }, ensure_ascii=False, indent=2)
        
        # 날짜 형식 변환 (YYYYMMDD)
        start_date_str = start_date.replace('-', '')
        end_date_str = end_date.replace('-', '')
        
        # PyKRX로 주가 데이터 가져오기
        df = stock.get_market_ohlcv_by_date(start_date_str, end_date_str, ticker)
        
        if df.empty:
            return json.dumps({
                "error": f"'{company_name}' 종목의 {start_date}~{end_date} 기간 데이터가 없습니다.",
                "suggestion": "기간을 조정하거나 다른 종목을 시도해보세요."
            }, ensure_ascii=False, indent=2)
        
        # 주가 분석 계산
        current_price = int(df['종가'].iloc[-1])
        start_price = int(df['종가'].iloc[0])
        price_change = current_price - start_price
        price_change_percent = round((price_change / start_price) * 100, 2)
        
        highest_price = int(df['고가'].max())
        lowest_price = int(df['저가'].min())
        avg_volume = int(df['거래량'].mean())
        total_volume = int(df['거래량'].sum())
        
        # 변동성 계산 (일간 수익률의 표준편차)
        daily_returns = df['종가'].pct_change()
        volatility = round(daily_returns.std() * 100, 2)
        
        # 시가총액 정보 (최신 날짜 기준)
        try:
            market_cap_df = stock.get_market_cap_by_date(end_date_str, end_date_str, ticker)
            if not market_cap_df.empty:
                market_cap = int(market_cap_df['시가총액'].iloc[-1])
                market_cap_formatted = f"{market_cap//100000000:,}억원"
            else:
                market_cap_formatted = "정보없음"
        except:
            market_cap_formatted = "정보없음"
        
        # 분석 결과 구성
        analysis_result = {
            "original_input": stock_name,
            "ticker": ticker,
            "company_name": company_name,
            "period": f"{start_date} ~ {end_date}",
            "current_price": current_price,
            "start_price": start_price,
            "price_change": price_change,
            "price_change_percent": price_change_percent,
            "highest_price": highest_price,
            "lowest_price": lowest_price,
            "average_volume": avg_volume,
            "total_volume": total_volume,
            "volatility": volatility,
            "market_cap": market_cap_formatted,
            "total_trading_days": len(df),
            "trend": "상승" if price_change > 0 else "하락" if price_change < 0 else "보합"
        }
        
        return json.dumps(analysis_result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"주가 데이터 조회 중 오류 발생: {str(e)}",
            "stock_name": stock_name
        }, ensure_ascii=False, indent=2)

def stock_analysis_tool(query: str) -> str:
    """
    사용자 질문을 분석하여 종목과 기간을 추출하고 주가 분석을 수행하는 도구
    """
    try:
        openai_key = st.session_state.get('openai_key', '')
        if not openai_key:
            return "❌ OpenAI API 키가 설정되지 않았습니다."
            
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=openai_key)
        
        today = datetime.now().strftime('%Y-%m-%d')
        three_months_ago = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        
        extract_prompt = f"""
사용자의 주식 분석 요청에서 다음 정보를 추출해주세요:

사용자 질문: "{query}"

다음 JSON 형식으로만 응답해주세요:
{{
    "stock_symbol": "종목명",
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD"
}}

추출 규칙:
1. 종목명: 사용자가 언급한 정확한 한국 종목명 사용
2. 기간이 없으면: start_date="{three_months_ago}", end_date="{today}" (최근 3개월)
3. "2024년", "올해" 등이 있으면: start_date="2024-01-01", end_date="{today}"
4. "최근 6개월"이면 6개월 전부터 오늘까지
5. 종목이 명확하지 않으면 stock_symbol을 "UNKNOWN"으로 설정

오늘 날짜: {today}
"""
        
        response = llm.invoke(extract_prompt)
        params = json.loads(response.content)
        
        # 종목이 지정되지 않은 경우 처리
        if params.get("stock_symbol") == "UNKNOWN":
            return "❌ 분석할 한국 종목을 명확히 지정해주세요.\n\n예시: '삼성전자 주가 분석해줘', 'LG전자 최근 3개월 분석'"
        
        # 주가 데이터 분석 실행
        result_json = get_stock_data_pykrx(
            params["stock_symbol"],
            params["start_date"], 
            params["end_date"]
        )
        
        # JSON 결과를 사용자 친화적 형태로 포맷팅
        result_data = json.loads(result_json)
        
        if "error" in result_data:
            error_msg = f"❌ {result_data['error']}"
            if result_data.get('suggestion'):
                error_msg += f"\n💡 {result_data['suggestion']}"
            return error_msg
        
        # 결과 포맷팅
        formatted_result = f"""
📊 **{result_data['company_name']} ({result_data['ticker']})** 주가 분석 결과
🔍 입력한 종목명: "{result_data['original_input']}"
🏢 시가총액: {result_data['market_cap']}

📅 **분석 기간**: {result_data['period']}
💰 **현재가**: {result_data['current_price']:,}원
📈 **시작가**: {result_data['start_price']:,}원
🔺 **변동**: {result_data['price_change']:+,}원 ({result_data['price_change_percent']:+.2f}%)

📊 **주요 지표**:
- 🔺 최고가: {result_data['highest_price']:,}원
- 🔻 최저가: {result_data['lowest_price']:,}원
- 📊 평균 거래량: {result_data['average_volume']:,}주
- 📈 총 거래량: {result_data['total_volume']:,}주
- 📈 변동성: {result_data['volatility']}%
- 📅 거래일수: {result_data['total_trading_days']}일
- 🎯 추세: **{result_data['trend']}**
"""
        
        return formatted_result
        
    except Exception as e:
        return f"❌ 주식 분석 중 오류가 발생했습니다: {str(e)}"

def analyze_stock_with_agent(user_query):
    """
    LangChain Agent를 사용하여 사용자 질문을 분석하고 주식 분석 수행
    """
    openai_key = st.session_state.get('openai_key', '')
    
    if not openai_key:
        return "❌ 사이드바에서 OpenAI API 키를 입력해주세요."
    
    try:
        # LLM 초기화
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=openai_key)
        
        # 주식 분석 도구
        stock_tool = Tool(
            name="stock_analysis",
            description="특정 한국 종목의 주가 데이터를 분석합니다. PyKRX를 사용하여 정확한 한국거래소 데이터를 제공합니다.",
            func=stock_analysis_tool
        )
        
        tools = [stock_tool]
        
        # 에이전트 프롬프트
        prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 한국 주식 전문 분석 AI입니다.

사용 가능한 도구:
- stock_analysis: PyKRX를 사용한 한국 주식 데이터 분석 (KOSPI, KOSDAQ)

사용자의 한국 주식 분석 요청을 받으면 stock_analysis 도구를 사용하여 분석을 수행하세요.
한국거래소의 정확한 데이터를 바탕으로 신뢰할 수 있는 분석을 제공합니다.

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
        return f"❌ AI 분석 중 오류가 발생했습니다: {str(e)}"

# 메인 UI
st.title("🇰🇷 한국 주식 분석 AI")
st.markdown("**PyKRX 기반 한국거래소 공식 데이터 분석 도구**")

# 사이드바 API 키 설정
with st.sidebar:
    st.header("🔑 API 설정")
    openai_key = st.text_input(
        "OpenAI API Key", 
        type="password",
        value="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",
        help="OpenAI API 키를 입력하세요"
    )
    
    # 세션 상태에 저장
    if openai_key:
        st.session_state.openai_key = openai_key
    
    st.markdown("---")
    st.markdown("### 🇰🇷 PyKRX 한국거래소 데이터")
    st.markdown("""
    **지원 시장:**
    - 📈 KOSPI (코스피)
    - 📊 KOSDAQ (코스닥)
    
    **데이터 특징:**
    - 🏛️ 한국거래소 공식 데이터
    - 💰 시가총액 정보 포함
    - 📊 정확한 거래량 데이터
    - 🔄 실시간 업데이트
    """)

st.markdown("---")

# 예제 질문 섹션
st.subheader("💡 예제 질문")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("삼성전자 분석", use_container_width=True):
        st.session_state.query = "삼성전자 주가를 최근 3개월간 분석해줘"

with col2:
    if st.button("LG전자 분석", use_container_width=True):
        st.session_state.query = "LG전자 2024년 주가 분석해줘"

with col3:
    if st.button("SK하이닉스", use_container_width=True):
        st.session_state.query = "SK하이닉스 최근 6개월 분석"

with col4:
    if st.button("NAVER", use_container_width=True):
        st.session_state.query = "네이버 주식 분석"

# 사용자 입력
st.markdown("### 🎯 한국 주식 분석 질문")
user_input = st.text_input(
    "분석하고 싶은 한국 종목과 기간을 입력하세요:",
    value=st.session_state.get('query', ''),
    placeholder="예: 삼성전자 분석 / LG전자 6개월 / 카카오 2024년 분석"
)

# 분석 실행
if st.button("🔍 AI 분석 시작", type="primary", use_container_width=True):
    if user_input.strip():
        with st.spinner("🇰🇷 한국거래소 데이터를 가져와서 분석 중입니다..."):
            result = analyze_stock_with_agent(user_input)
            
        st.markdown("### 📊 분석 결과")
        st.markdown(result)
    else:
        st.warning("⚠️ 분석할 한국 종목과 질문을 입력해주세요.")

# 실시간 종목 검색 테스트
with st.expander("🔍 종목 검색 테스트 (PyKRX 실시간)"):
    test_input = st.text_input("한국 종목명 검색:", placeholder="예: 삼성전자, LG전자, 카카오")
    if test_input:
        with st.spinner("종목 검색 중..."):
            stock_info = get_all_stock_codes()
            ticker, company_name = search_stock_by_name(test_input, stock_info)
            
        if ticker:
            st.success(f"✅ '{test_input}' → {company_name} ({ticker})")
        else:
            st.error(f"❌ '{test_input}' 종목을 찾을 수 없습니다.")

# PyKRX 정보
with st.expander("ℹ️ PyKRX 기능 및 장점"):
    st.markdown("""
    ### 🏛️ PyKRX 한국거래소 API
    - **공식 데이터**: 한국거래소에서 직접 제공하는 정확한 데이터
    - **실시간 업데이트**: 매일 최신 주가 정보 반영
    - **풍부한 정보**: 시가총액, 거래량, OHLCV 데이터 제공
    - **한국 특화**: 한국 주식 시장에 최적화된 API
    
    ### 📊 제공 데이터
    - **주가 정보**: 시가, 고가, 저가, 종가
    - **거래 정보**: 거래량, 거래대금
    - **시장 정보**: 시가총액, 상장주식수
    - **시장 구분**: KOSPI, KOSDAQ 구분
    
    ### 🚀 사용법
    - 한국 종목명을 자연어로 입력
    - 다양한 기간 설정 가능 (일, 월, 년)
    - 법인명 자동 정규화 (주식회사, (주) 등 자동 제거)
    """)

# API 키 상태 표시
if st.session_state.get('openai_key'):
    st.success("✅ OpenAI API 키가 설정되었습니다. 한국 주식 분석을 시작할 수 있습니다!")
else:
    st.error("❌ 사이드바에서 OpenAI API 키를 입력해주세요.")