import streamlit as st
import os
from datetime import datetime
import pandas as pd
from pykrx import stock
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_openai import OpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.tools import tool
import sys
# StreamlitSecretsError를 명시적으로 임포트하여 처리합니다.
from streamlit.errors import StreamlitSecretNotFoundError

# --- 1. 필요한 패키지 확인 및 설치 안내 ---
try:
    import tabulate # tabulate는 pandas dataframe 출력 시 가끔 사용될 수 있어 확인합니다.
except ImportError:
    st.error("필요한 패키지 'tabulate'이(가) 설치되지 않았습니다. 터미널에서 다음 명령어를 실행해주세요:\npip install tabulate")
    sys.exit(1) # 패키지 없으면 종료

# --- 2. OpenAI API 키 설정 (사용자 요청에 따라 직접 삽입) ---
# 경고: 이 방법은 보안상 매우 취약합니다. API 키가 코드에 직접 노출됩니다.
# 프로덕션 환경에서는 절대 사용하지 마세요!
# 대신 Streamlit secrets (st.secrets["OPENAI_API_KEY"]) 또는 환경 변수를 사용하세요.
os.environ["OPENAI_API_KEY"] = "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"
st.warning("OpenAI API 키가 코드에 직접 삽입되었습니다. 보안에 유의하세요!")


# --- 3. Streamlit 페이지 기본 설정 ---
st.set_page_config(page_title="주식 분석 도우미", page_icon="📊", layout="wide")
st.title("📊 AI 기반 주식 분석 도우미")
st.markdown("사용자의 자연어 입력에 따라 주식 종목을 인식하고, 해당 종목의 데이터를 기반으로 AI가 분석 리포트를 생성합니다.")

# --- 4. LangChain 도구 정의 (종목명 -> 티커 변환 로직) ---
@tool
def get_ticker_from_name(stock_name: str) -> str:
    """
    주식 종목명(예: "삼성전자", "삼전")을 받아서 해당 종목의 공식 티커 코드(예: "005930")를 반환합니다.
    자주 사용되는 별칭(예: "삼전", "하닉")과 부분 일치 검색을 지원합니다.
    티커를 찾지 못하면 빈 문자열을 반환합니다.
    """
    today_str = datetime.now().strftime("%Y%m%d")
    
    # 자주 사용되는 별칭에 대한 하드코딩된 매핑 (정확성 향상)
    alias_map = {
        "삼전": "005930",
        "삼성전자": "005930",
        "하닉": "000660",
        "sk하이닉스": "000660",
        "네이버": "035420",
        "naver": "035420",
        "카카오": "035720",
        "엘지엔솔": "373220",
        "lg에너지솔루션": "373220",
        "엘지전자": "066570", # LG전자 추가
        "lg전자": "066570" # LG전자 추가
    }
    
    # 사용자 입력 정규화 (소문자, 공백 제거)
    normalized_input = stock_name.lower().replace(" ", "")

    # 1. 별칭 맵에서 직접 확인
    if normalized_input in alias_map:
        return alias_map[normalized_input]

    # 2. pykrx를 통해 전체 시장 종목 리스트에서 검색
    try:
        all_tickers = stock.get_market_ticker_list(today_str)
    except Exception as e:
        st.error(f"pykrx에서 시장 종목 목록을 가져오는 중 오류 발생: {e}")
        return ""

    # 3. 정확한 종목명 일치 검색
    for ticker_code in all_tickers:
        try:
            official_name = stock.get_market_ticker_name(ticker_code)
            if official_name.lower().replace(" ", "") == normalized_input:
                return ticker_code
        except Exception:
            continue # 종목명 조회 실패 시 건너뛰기

    # 4. 부분 일치 검색 (더 유연한 검색)
    for ticker_code in all_tickers:
        try:
            official_name = stock.get_market_ticker_name(ticker_code)
            if normalized_input in official_name.lower().replace(" ", ""):
                return ticker_code
        except Exception:
            continue

    return "" # 티커를 찾지 못한 경우

@tool
def get_company_name_from_ticker(ticker_code: str) -> str:
    """
    주식 티커 코드(예: "005930")를 받아서 해당 종목의 공식 회사명을 반환합니다.
    회사명을 찾지 못하면 빈 문자열을 반환합니다.
    """
    try:
        return stock.get_market_ticker_name(ticker_code)
    except Exception:
        return ""

# --- 5. 주식 데이터 조회 함수 ---
@st.cache_data(ttl=3600) # 1시간 캐싱
def get_stock_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    pykrx를 사용하여 지정된 기간의 주식 시가, 고가, 저가, 종가, 거래량 데이터를 가져옵니다.
    """
    try:
        df = stock.get_market_ohlcv_by_date(start_date, end_date, ticker)
        return df
    except Exception as e:
        st.error(f"주식 데이터 조회 중 오류가 발생했습니다: {e}\n(종목 코드: {ticker}, 기간: {start_date}~{end_date})")
        return pd.DataFrame() # 오류 발생 시 빈 DataFrame 반환

# --- 6. LangChain 에이전트를 사용한 주식 데이터 분석 함수 ---
def analyze_with_langchain_agent(df: pd.DataFrame, company_name: str) -> str:
    """
    LangChain pandas dataframe agent를 사용하여 주식 데이터를 분석하고 결과를 반환합니다.
    """
    llm = OpenAI(
        temperature=0, # 창의성 낮게 설정하여 일관된 결과 도출
        model_name="gpt-3.5-turbo-instruct" # 지시 기반 모델 사용
    )
    
    # DataFrame 인덱스를 문자열 형식으로 전처리 (에이전트가 처리하기 쉽게)
    df_processed = df.copy()
    df_processed.index = df_processed.index.strftime('%Y-%m-%d')
    
    try:
        # 보안 설정을 포함하여 에이전트 생성
        agent = create_pandas_dataframe_agent(
            llm,
            df_processed,
            verbose=True, # 에이전트의 내부 동작을 콘솔에 출력 (디버깅용)
            handle_parsing_errors=True, # 파싱 오류 처리 시도
            allow_dangerous_code=True, # 잠재적으로 위험한 코드 실행 허용 (주의 필요, 프로덕션에서는 최소화)
            prefix=f"""
            당신은 {company_name}의 주식 데이터를 분석하는 주식 분석 전문가입니다. 주어진 데이터를 기반으로 다음 지침을 따르세요:
            데이터프레임에는 다음 컬럼이 포함되어 있습니다:
            - 시가: 장 시작시 가격
            - 고가: 장중 최고가
            - 저가: 장중 최저가
            - 종가: 장 마감 가격
            - 거래량: 거래된 주식 수
            
            분석을 시작하기 전에 항상 데이터프레임의 첫 몇 행과 마지막 몇 행을 확인하여 데이터의 구조와 기간을 이해하세요.
            """
        )
        
        # 에이전트에게 전달할 분석 프롬프트
        prompt = f"""
        {company_name}의 주가 데이터를 심층적으로 분석해서 다음 형식으로 답변해주세요:
        
        1. **주가 변동 추이 요약:** 분석 기간 동안의 전반적인 주가 추이(상승, 하락, 횡보)와 그 특징을 설명해주세요.
        2. **거래량 분석:** 거래량의 특징(예: 특정 시기 급증/감소)과 이것이 주가에 미친 영향을 분석해주세요.
        3. **주요 변동 포인트:** 가장 큰 폭의 상승 또는 하락이 있었던 시점과 그 원인(추정)을 설명해주세요. (데이터 내에서 확인할 수 있는 정보 기준)
        4. **투자 위험 요소:** 해당 종목의 주가 흐름에서 나타나는 잠재적인 위험 요소를 지적해주세요.
        5. **투자 추천:** 현재 데이터만을 기반으로, 이 종목에 대한 매수/매도/관망 중 어떤 의견을 가지며 그 이유는 무엇인지 명확하게 제시해주세요. (면책 조항: 이 분석은 인공지능에 의한 것이며 실제 투자 자문이 아닙니다.)
        
        모든 답변은 한국어로 자세하고 명료하게 작성해주세요.
        """
        
        response = agent.run(prompt)
        return response
        
    except Exception as e:
        st.error(f"AI 분석 에이전트 실행 중 오류가 발생했습니다: {e}\n데이터 또는 프롬프트를 확인해주세요.")
        return "AI 분석 중 오류가 발생했습니다. 잠시 후 다시 시도하거나, 다른 종목으로 시도해주세요."

# --- 7. LangChain 에이전트를 사용한 자연어 종목명 해석 함수 ---
def resolve_stock_with_agent(user_input: str) -> tuple[str, str]:
    """
    LangChain 에이전트와 커스텀 도구를 사용하여 자연어 종목명을
    티커 코드와 공식 회사명으로 변환합니다.
    (티커, 회사명) 튜플을 반환하거나, 찾지 못하면 ("", "")를 반환합니다.
    """
    llm = OpenAI(temperature=0, model_name="gpt-3.5-turbo-instruct")
    tools = [get_ticker_from_name, get_company_name_from_ticker]

    # 종목명 해석 전용 에이전트 초기화
    agent_executor = initialize_agent(
        tools,
        llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, # 도구 사용에 대한 추론 능력 활용
        verbose=True, # 에이전트의 작동 과정 콘솔 출력 (디버깅용)
        handle_parsing_errors=True, # 에이전트의 파싱 오류 처리 시도
        agent_kwargs={
            "prefix": """
            당신은 주식 종목명 또는 별칭을 정확한 종목 코드로 변환하는 데 특화된 전문가입니다.
            사용자가 제공한 주식 종목명이나 별칭에 대해 `get_ticker_from_name` 도구를 사용하여 6자리 종목 코드를 찾아야 합니다.
            찾은 종목 코드를 다른 설명 없이 **오직 6자리 숫자 문자열**로만 최종 답변으로 반환해야 합니다.
            만약 어떤 이유로든 종목 코드를 찾을 수 없다면, **"NOT_FOUND"**라는 문자열을 반환해야 합니다.
            회사명을 찾을 필요가 있다면 `get_company_name_from_ticker` 도구를 사용하세요.
            """
        }
    )

    try:
        # 에이전트에게 종목 코드를 찾고 특정 형식으로 반환하도록 지시
        st.info(f"'{user_input}'에 대한 종목 코드 확인을 AI에게 요청 중입니다...")
        agent_response = agent_executor.run(f"'{user_input}' 종목의 코드를 찾아주세요.")
        
        ticker = agent_response.strip()

        if ticker.isdigit() and len(ticker) == 6:
            company_name = get_company_name_from_ticker(ticker)
            if company_name:
                st.success(f"'{user_input}'을(를) **{company_name} ({ticker})** 로 인식했습니다.")
                return ticker, company_name
            else:
                st.warning(f"종목 코드 '{ticker}'에 대한 공식 종목명을 가져올 수 없습니다. 다른 종목을 시도해주세요.")
                return "", ""
        elif ticker == "NOT_FOUND":
            st.warning(f"AI가 '{user_input}'에 해당하는 종목 코드를 찾지 못했습니다.")
            return "", ""
        else:
            st.warning(f"AI의 종목명 해석 응답이 예상과 다릅니다: '{agent_response}'. 잠시 후 다시 시도해주세요.")
            return "", ""
    except Exception as e:
        st.error(f"종목명 해석 에이전트 실행 중 심각한 오류가 발생했습니다: {e}")
        st.info("이 오류는 대개 OpenAI API 키 문제, API 서버 연결 문제 또는 모델 응답 형식 문제로 인해 발생합니다.")
        return "", ""

# --- 8. Streamlit UI 구성 ---
with st.sidebar:
    st.header("분석 설정")
    # 사용자 입력: 종목명 또는 종목 코드
    user_stock_input = st.text_input(
        "분석할 종목명 또는 종목 코드를 입력하세요.",
        value="삼성전자",
        help="예: 삼성전자, 삼전, 005930, 엘지전자"
    )
    
    # 분석 기간 선택
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "시작일",
            value=datetime(2023, 1, 1),
            format="YYYY-MM-DD"
        )
    with col2:
        end_date = st.date_input(
            "종료일",
            value=datetime.now(),
            format="YYYY-MM-DD"
        )
    
    # 분석 시작 버튼
    analyze_button = st.button("📈 분석 시작", type="primary")

# --- 9. 메인 화면에 분석 결과 표시 ---
if analyze_button:
    if not user_stock_input:
        st.error("종목명 또는 종목 코드를 입력해주세요.")
    else:
        # 1단계: LangChain 에이전트를 사용하여 사용자 입력 종목명 해석
        with st.spinner(f"'{user_stock_input}'에 대한 종목 정보를 확인 중입니다..."):
            ticker, company_name = resolve_stock_with_agent(user_stock_input)

        if not ticker:
            # 종목을 찾지 못한 경우 오류 메시지 표시 (resolve_stock_with_agent에서 이미 표시됨)
            pass 
        else:
            try:
                # 2단계: pykrx를 통해 주식 데이터 가져오기
                with st.spinner(f"'{company_name}'({ticker})의 주가 데이터를 가져오는 중입니다..."):
                    # 날짜 형식 변환 (pykrx는 YYYYMMDD 형식 요구)
                    start_str = start_date.strftime("%Y%m%d")
                    end_str = end_date.strftime("%Y%m%d")
                    
                    df = get_stock_data(ticker, start_str, end_str)
                    
                    if df.empty:
                        st.warning(f"'{company_name}'({ticker})에 대한 {start_date.strftime('%Y-%m-%d')}부터 {end_date.strftime('%Y-%m-%d')}까지의 데이터가 없습니다. 기간을 조정하거나 다른 종목을 선택해주세요.")
                    else:
                        # 3단계: 기본 주식 정보 표시
                        st.subheader(f"💰 {company_name}({ticker}) 기본 정보")
                        col_info1, col_info2, col_info3 = st.columns(3)
                        with col_info1:
                            if not df.empty:
                                current_price = df['종가'].iloc[-1] 
                                st.metric("현재가", f"{current_price:,.0f}원")
                            else:
                                st.write("데이터 없음")
                        with col_info2:
                            if not df.empty:
                                volume = df['거래량'].iloc[-1]
                                st.metric("오늘 거래량", f"{volume:,.0f}")
                            else:
                                st.write("데이터 없음")
                        with col_info3:
                             if len(df) > 1:
                                start_price = df['종가'].iloc[0] 
                                current_price = df['종가'].iloc[-1]
                                price_change_abs = current_price - start_price
                                price_change_pct = (price_change_abs / start_price) * 100 if start_price != 0 else 0
                                st.metric("기간 내 변동", f"{price_change_abs:,.0f}원", f"{price_change_pct:.1f}%")
                             else:
                                st.write("기간 내 데이터 부족")
                        
                        # 4단계: 주가 차트 표시
                        st.subheader("📈 주가 차트")
                        st.line_chart(df[['시가', '고가', '저가', '종가']], use_container_width=True)
                        
                        # 5단계: LangChain 에이전트를 통한 AI 분석 수행
                        with st.spinner("AI가 주가 데이터를 분석 중입니다. 잠시만 기다려 주세요..."):
                            analysis = analyze_with_langchain_agent(df, company_name)
                            st.subheader("🤖 AI 분석 결과")
                            st.markdown(analysis) # 마크다운 형식으로 출력
                        
                        # 6단계: 최근 데이터 표시
                        st.subheader("📋 최근 5일 데이터")
                        st.dataframe(df.tail().style.format(formatter={
                            '시가': '{:,.0f}', '고가': '{:,.0f}', '저가': '{:,.0f}', '종가': '{:,.0f}', '거래량': '{:,.0f}'
                        }), use_container_width=True)
                        
            except Exception as e:
                st.error(f"데이터 처리 또는 분석 중 예상치 못한 오류가 발생했습니다: {e}")
                st.info("입력된 종목명과 기간을 확인하고 다시 시도해주세요.")
else:
    # 앱 초기 로드 시 안내 메시지
    st.info("👈 왼쪽 사이드바에서 분석할 종목명 또는 종목 코드와 기간을 입력하고 '분석 시작' 버튼을 클릭하세요.")
    
    # 예시 종목명/코드 안내
    st.markdown("""
    ---
    ### 💡 종목명/코드 입력 예시
    - **정식 종목명:** 삼성전자, SK하이닉스, NAVER, 카카오, LG에너지솔루션, LG전자
    - **자주 쓰는 별칭:** 삼전, 하닉, 네이버, 엘지엔솔, 엘지전자
    - **종목 코드:** 005930, 000660, 035420, 035720, 373220, 066570
    """)
