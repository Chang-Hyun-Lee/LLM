import streamlit as st
import os
from datetime import datetime
import pandas as pd
from pykrx import stock
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_openai import OpenAI
from typing import Dict, Any
import sys

# Check for required packages
try:
    import tabulate
except ImportError:
    st.error("필요한 패키지가 설치되지 않았습니다. 터미널에서 다음 명령어를 실행해주세요:\npip install tabulate")
    sys.exit(1)

# OpenAI API 키 설정
os.environ["OPENAI_API_KEY"] = "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"

# Streamlit 페이지 설정
st.set_page_config(page_title="주식 분석 도우미", page_icon="📊")
st.title("📊 주식 분석 도우미")

def get_stock_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """주식 데이터를 가져오는 함수"""
    df = stock.get_market_ohlcv_by_date(start_date, end_date, ticker)
    return df

def analyze_with_langchain_agent(df: pd.DataFrame, company_name: str) -> str:
    """LangChain agent를 사용한 주식 분석"""
    llm = OpenAI(
        temperature=0,
        model_name="gpt-3.5-turbo-instruct"  # Changed to an instruction model
    )
    
    # DataFrame 전처리
    df = df.copy()
    df.index = df.index.strftime('%Y-%m-%d')
    
    try:
        # 보안 설정과 함께 agent 생성
        agent = create_pandas_dataframe_agent(
            llm,
            df,
            verbose=True,
            handle_parsing_errors=True,
            allow_dangerous_code=True,
            prefix="""
            당신은 주식 분석 전문가입니다. 주어진 데이터를 기반으로 분석을 수행하세요.
            데이터프레임에는 다음 컬럼이 포함되어 있습니다:
            - 시가: 장 시작시 가격
            - 고가: 장중 최고가
            - 저가: 장중 최저가
            - 종가: 장 마감 가격
            - 거래량: 거래된 주식 수
            """
        )
        
        prompt = f"""
        {company_name}의 주가 데이터를 분석해서 다음 형식으로 답변해주세요:
        
        1. 주가 변동 추이 (전반적인 추세와 특징)
        2. 거래량 분석 (거래량의 특징과 의미)
        3. 주요 변동 포인트 (중요한 가격 변동 시점)
        4. 투자 위험 요소
        5. 투자 추천 (매수/매도/관망 여부와 이유)
        
        한글로 답변해주세요.
        """
        
        response = agent.run(prompt)
        return response
        
    except Exception as e:
        return f"분석 중 오류가 발생했습니다: {str(e)}\n데이터를 확인하고 다시 시도해주세요."

# Sidebar에 입력 폼 배치
with st.sidebar:
    st.header("분석 설정")
    ticker = st.text_input("종목 코드", value="005930", help="예: 삼성전자(005930)")
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
    
    analyze_button = st.button("분석 시작", type="primary")

# 메인 화면 분석 결과 표시
if analyze_button:
    try:
        with st.spinner("데이터를 가져오는 중..."):
            # 날짜 형식 변환
            start_str = start_date.strftime("%Y%m%d")
            end_str = end_date.strftime("%Y%m%d")
            
            # 종목명 조회
            company_name = stock.get_market_ticker_name(ticker)
            
            # 데이터 가져오기
            df = get_stock_data(ticker, start_str, end_str)
            
            # 기본 정보 표시
            st.subheader(f"💰 {company_name}({ticker}) 기본 정보")
            col1, col2 = st.columns(2)
            with col1:
                current_price = df['종가'][-1]
                start_price = df['종가'][0]
                price_change = ((current_price - start_price) / start_price) * 100
                st.metric("현재가", f"{current_price:,}원", f"{price_change:.1f}%")
            with col2:
                volume = df['거래량'][-1]
                st.metric("거래량", f"{volume:,}")
            
            # 차트 표시
            st.subheader("📈 주가 차트")
            st.line_chart(df['종가'])
            
            # LangChain agent 분석
            with st.spinner("AI 분석 중..."):
                analysis = analyze_with_langchain_agent(df, company_name)
                st.subheader("🤖 AI 분석 결과")
                st.write(analysis)
            
            # 최근 데이터 표시
            st.subheader("📊 최근 5일 데이터")
            st.dataframe(df.tail(), use_container_width=True)
            
    except Exception as e:
        st.error(f"분석 중 오류가 발생했습니다: {str(e)}")
else:
    st.info("👈 왼쪽 사이드바에서 종목 코드와 기간을 입력하고 분석 버튼을 클릭하세요.")
    
    # 예시 종목 코드
    st.markdown("""
    ### 주요 종목 코드 예시
    - 삼성전자: 005930
    - SK하이닉스: 000660
    - NAVER: 035420
    - 카카오: 035720
    - LG에너지솔루션: 373220
    """)