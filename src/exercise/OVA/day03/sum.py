import os
import streamlit as st
import openai
import json
import requests
from urllib.parse import quote
from pykrx import stock

from langchain import hub
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import tool
from langchain_core.callbacks import Callbacks
from langchain_core.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

# === 주식 관련 도구 ===
@tool
def get_market_ohlcv(start_date, end_date, ticker):
    """Return prices within given dates for ticker stock. start_date and end_date should be 'YYYYMMDD' format.
    For ticker, you can use either stock code (like '005930') or company name (like '삼성전자').
    """
    try:
        start_date = start_date.strip()
        end_date = end_date.strip()
        ticker = ticker.strip()
        
        # 종목명인 경우 코드로 변환
        if not ticker.isdigit():
            # 종목명으로 코드 찾기
            import pandas as pd
            ticker_list = stock.get_market_ticker_list()
            for code in ticker_list:
                name = stock.get_market_ticker_name(code)
                if ticker in name:
                    ticker = code
                    break
        
        stock_name = stock.get_market_ticker_name(ticker)
        df = stock.get_market_ohlcv(start_date, end_date, ticker)
        df['종목명'] = [stock_name] * len(df)

        return json.dumps(df.to_dict(orient='records'), ensure_ascii=False)
    except Exception as e:
        return f"주식 데이터 조회 오류: {str(e)}"

# === 레스토랑 관련 도구 ===
@tool
def get_restaurant_info(place, kind):
    """Return restaurant information for given place and kind."""
    searching = f"{place} {kind}"
    kakao_api_key = "zkuT4EWE3oQA0RS_F318_tG7VwmTgpyYAAAAAQoXEG8AAAGYOy2teU8FYMfcu4fs"
    url = 'https://dapi.kakao.com/v2/local/search/keyword.json?query={}'.format(searching)
    headers = {
        "Authorization": f"KakaoAK {kakao_api_key}"
    }
    places = requests.get(url, headers=headers).json()
    return places

# === 캠핑 관련 도구 ===
ServiceKey = "Cw/Ebj0gB2BAEfz2r9tWNqWSH0aszmbuIcanTHSX7NUgx1H3UEpFCXdGXvy+ZT3vU0KxKqXbQc9OUhu79BVFgw=="

def get_url_content(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            response.raise_for_status()

    except requests.exceptions.RequestException as e:
        print(f"Request Exception: {e}")
        return None

@tool
def get_camping_info_context(keyword):
    """Return camping information context for given keyword. keyword should be a word."""
    keyword = quote(keyword)
    url = f"http://apis.data.go.kr/B551011/GoCamping/searchList?serviceKey={ServiceKey}&keyword={keyword}&numOfRows=10&pageNo=1&MobileOS=ETC&MobileApp=TestApp&_type=json"

    result = get_url_content(url)
    data = json.loads(result)
    
    context = ''
    if data['response']['body']['numOfRows'] > 0:
        sites = data['response']['body']['items']['item']

        i = 1
        for site in sites:
            context = context + str(i) + ") " + site['facltNm'] + ":" + site['intro'] + "\n"
            i = i + 1
    else:
        context = '데이터 없음'
    return context

# === 통합 에이전트 초기화 ===
@st.cache_resource
def init_agent():
    # ⚠️ 여기에 새로운 OpenAI API 키를 입력하세요! ⚠️
    openai_api_key = "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"
    
    if openai_api_key == "여기에_새로운_OpenAI_API_키_입력":
        st.error("❌ OpenAI API 키를 입력해주세요!")
        st.stop()
    
    openai.api_key = openai_api_key
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0, streaming=True, api_key=openai_api_key)
    prompt = hub.pull("hwchase17/openai-tools-agent")
    
    # 통합된 시스템 프롬프트
    system_prompt = """당신은 다양한 서비스를 제공하는 전문 어시스턴트입니다. 
    사용자의 요청을 정확히 분석하고 적절한 도구를 사용해주세요:
    
    1. 주식 관련 질문 (예: "삼성전자", "005930", "주가", "주식"):
       - get_market_ohlcv 도구를 사용하세요
       - 종목 코드나 이름을 파악하고 적절한 날짜 범위로 조회하세요
    
    2. 레스토랑 관련 질문 (예: "식당", "맛집", "음식", 지역명 + 음식종류):
       - get_restaurant_info 도구를 사용하세요
       - 지역과 음식 종류를 명확히 파악하세요
    
    3. 캠핑 관련 질문 (예: "캠핑장", "캠핑", 지역명 + "캠핑"):
       - get_camping_info_context 도구를 사용하세요
       - 지역 키워드를 정확히 추출하세요
    
    사용자 질문의 핵심 키워드를 파악하여 올바른 도구를 선택하고, 
    도구 실행 결과를 바탕으로 정확하고 유용한 답변을 제공하세요."""
    
    prompt.messages[0] = SystemMessagePromptTemplate.from_template(system_prompt)

    # 모든 도구를 통합
    tools = [get_market_ohlcv, get_restaurant_info, get_camping_info_context]
    
    agent = create_openai_tools_agent(
        model.with_config({"tags": ["agent_llm"]}), tools, prompt
    )
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True).with_config(
        {"run_name": "IntegratedAgent"}
    )
    return model, prompt, tools, agent, agent_executor

def chat_with_bot(agent_executor, history):
    try:
        user_input = history[-1]["content"]
        response = agent_executor.invoke({"input": user_input})
        return response["output"]
    except Exception as e:
        return f"죄송합니다. 오류가 발생했습니다: {str(e)}"

def main():
    st.title("🤖 통합 멀티 서비스 챗봇")
    st.subheader("📈 주식 분석 | 🍽️ 레스토랑 추천 | 🏕️ 캠핑장 정보")
    
    # 사이드바에 사용법 안내
    with st.sidebar:
        st.header("💡 사용법")
        st.markdown("""
        **주식 정보 조회:**
        - "삼성전자 주가 알려줘"
        - "005930 최근 1개월 주가"
        
        **레스토랑 추천:**
        - "강남 이탈리안 식당 추천해줘"
        - "부산 해물탕 맛집"
        
        **캠핑장 정보:**
        - "제주도 캠핑장 알려줘"
        - "강원도 캠핑장 정보"
        """)
        
        st.header("✅ 상태")
        st.success("모든 API 키가 설정되었습니다!")
    
    # 채팅 입력
    st.chat_input(placeholder="무엇을 도와드릴까요? (주식, 레스토랑, 캠핑 정보를 물어보세요)", key="chat_input")

    try:
        # 에이전트 초기화
        model, prompt, tools, agent, agent_executor = init_agent()

        # 메시지 히스토리 초기화
        if "messages" not in st.session_state:
            st.session_state.messages = []
            # 웰컴 메시지
            welcome_msg = """안녕하세요! 저는 다양한 서비스를 제공하는 통합 어시스턴트입니다. 😊

다음과 같은 도움을 드릴 수 있습니다:
- 📈 **주식 정보**: 종목 코드나 이름으로 주가 정보 조회
- 🍽️ **레스토랑 추천**: 지역과 음식 종류별 맛집 추천  
- 🏕️ **캠핑장 안내**: 지역별 캠핑장 정보 검색

무엇을 도와드릴까요?"""
            st.session_state.messages.append({"role": "assistant", "content": welcome_msg})

        # 메시지 히스토리 표시
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # 사용자 입력 처리
        if user_input := st.session_state["chat_input"]:
            with st.chat_message("user"):
                st.markdown(user_input)
            st.session_state.messages.append({"role": "user", "content": user_input})

            with st.spinner('답변을 준비중입니다... 🤔'):
                try:
                    response = chat_with_bot(agent_executor, st.session_state.messages)
                except Exception as e:
                    response = f"죄송합니다. 처리 중 오류가 발생했습니다: {str(e)}"
            
            with st.chat_message("assistant"):
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
    except Exception as e:
        st.error(f"초기화 오류: {str(e)}")

if __name__ == "__main__":
    main()