import os
import json
import requests
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from pykrx import stock
from openai import OpenAI
import xml.etree.ElementTree as ET

# LangChain 관련 임포트 (주가 분석 Agent에만 사용)
from langchain import hub
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import tool
from langchain.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
# TavilySearchResults는 주가 분석 Agent가 외부 웹 검색을 할 때 필요합니다.
# 만약 Tavily API를 사용하지 않으려면 이 라인과 Agent 초기화 부분에서 제거해야 합니다.
# from langchain_community.tools.tavily_search import TavilySearchResults

# ✅ API 키 설정 (기존 코드의 하드코딩 방식 유지)
# OpenAI API 키는 환경 변수에서 가져옴
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# 카카오 API 키 (하드코딩 유지)
KAKAO_REST_API_KEY = "c662192f1e74c3c14e16950ee0d6d5e1"
# GoCamping API 키 (하드코딩 유지)
CAMP_API_KEY = "DCvakj3KUyfmU0c%2FF7CbsLX4VXkEjGdcDfj1A0tFvZzJZL9h70OoFvmEeWVg54OdoXH7mOXwxIHM45Mx6IVxlA%3D%3D"

# --- Streamlit 앱 기본 설정 ---
st.set_page_config(page_title="GPT 통합 추천기", layout="wide")
st.title("🎯 GPT 기반 통합 추천기")

# 사이드바에서 기능 선택
option = st.sidebar.selectbox("기능 선택", ["맛집 추천", "캠핑장 추천", "주가 분석"])

# ==============================================================================
# --- 🍽️ 맛집 추천 기능 ---
# ==============================================================================
if option == "맛집 추천":
    st.header("🍽️ GPT 맛집 추천기")
    st.markdown("카카오 API와 GPT를 활용한 지역 기반 맛집 추천 시스템입니다.")

    def search_restaurants_kakao(query, location, size=7):
        url = "https://dapi.kakao.com/v2/local/search/keyword.json"
        headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
        params = {
            "query": f"{location} {query}",
            "size": size,
            "page": 1,
            "sort": "accuracy",
            "category_group_code": "FD6",
        }
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            results = response.json()
            return results.get("documents", [])
        except requests.exceptions.RequestException as e:
            st.error(f"카카오 맛집 검색 중 오류가 발생했습니다: {e}")
            return []

    def format_restaurants_for_gpt(restaurants):
        formatted = ""
        for r in restaurants:
            name = r.get("place_name", "이름 없음")
            address = r.get("address_name", "주소 없음")
            phone = r.get("phone", "번호 없음")
            category = r.get("category_name", "카테고리 없음")
            formatted += f"{name} | {category} | 주소: {address} | 전화: {phone}\n"
        return formatted

    def ask_gpt_to_recommend_restaurant(restaurants_text, location, user_question):
        prompt = (
            f"아래는 '{location}' 지역의 음식점 목록입니다:\n\n"
            f"{restaurants_text}\n\n"
            f"이 중에서 '{user_question}'에 맞게 3곳 추천하고, 간단한 설명도 덧붙여줘."
        )
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "너는 친절한 음식점 추천 도우미야."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=700
            )
            return response.choices[0].message.content
        except Exception as e:
            st.error(f"GPT 맛집 추천 중 오류가 발생했습니다: {e}")
            return "맛집 추천을 받지 못했습니다. 다시 시도해 주세요."

    with st.form("restaurant_search_form"):
        location = st.text_input("지역을 입력하세요 (예: 홍대, 판교 등)", "")
        query = st.text_input("어떤 음식점이 궁금한가요? (예: 분위기 좋은 이탈리안 식당)", "")
        submitted = st.form_submit_button("추천받기")

    if submitted:
        if not location or not query:
            st.warning("지역과 검색 조건을 모두 입력해주세요.")
        else:
            with st.spinner("🔎 카카오 API로 음식점 검색 중..."):
                restaurants = search_restaurants_kakao(query, location)
                if not restaurants:
                    st.error("검색된 음식점이 없습니다. 다른 조건을 시도해 보세요.")
                else:
                    restaurants_text = format_restaurants_for_gpt(restaurants)
                    st.subheader("📋 검색된 음식점 목록")
                    st.text(restaurants_text) # GPT 분석을 위한 원본 데이터 표시

                    with st.spinner("🤖 GPT에게 추천 요청 중..."):
                        recommendation = ask_gpt_to_recommend_restaurant(restaurants_text, location, query)
                        st.subheader("🍴 GPT 추천 결과")
                        st.success(recommendation)

# ==============================================================================
# --- 🏕️ 캠핑장 추천 기능 ---
# ==============================================================================
elif option == "캠핑장 추천":
    st.header("🏕️ GPT 캠핑장 추천기 (공공데이터 기반)")
    st.markdown("**공공데이터포털의 GoCamping 데이터를 기반으로 조건에 맞는 캠핑장을 추천해드립니다.**")

    @st.cache_data
    def fetch_campgrounds_from_api(num=15):
        url = (
            f"https://apis.data.go.kr/B551011/GoCamping/basedList"
            f"?serviceKey={CAMP_API_KEY}"
            f"&numOfRows={num}&pageNo=1&MobileOS=ETC&MobileApp=campApp&_type=xml"
        )
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            items = root.findall(".//item")

            campgrounds = []
            for item in items:
                name = item.findtext("facltNm", default="이름 없음")
                addr = item.findtext("addr1", default="주소 없음")
                line_intro = item.findtext("lineIntro", default="설명 없음")
                feature = item.findtext("featureNm", default="특징 정보 없음")
                campgrounds.append({
                    "이름": name,
                    "주소": addr,
                    "설명": line_intro,
                    "특징": feature,
                })
            return campgrounds
        except requests.exceptions.RequestException as e:
            st.error(f"캠핑장 데이터 가져오기 중 오류가 발생했습니다: {e}")
            return []
        except ET.ParseError as e:
            st.error(f"캠핑장 데이터 XML 파싱 중 오류가 발생했습니다: {e}")
            return []

    def format_campgrounds(camps):
        if not camps:
            return "사용 가능한 캠핑장 데이터가 없습니다."
        text = ""
        for c in camps:
            text += f"{c['이름']} | {c['주소']} | {c['특징']} | {c['설명']}\n"
        return text.strip()

    def ask_gpt_to_recommend_camp(query: str) -> str:
        camps = fetch_campgrounds_from_api(15)
        if not camps:
            return "캠핑장 정보를 불러오지 못했습니다. 다시 시도해 주세요."

        formatted = format_campgrounds(camps)
        prompt = (
            f"아래는 최근 캠핑장 목록입니다:\n\n{formatted}\n\n"
            f"이 중 사용자가 '{query}' 조건에 맞는 캠핑장을 찾고 있어.\n"
            f"조건에 잘 맞는 곳 2~3곳을 추천해주고, 각각의 특징도 간단히 설명해줘."
        )
        try:
            # LangChain ChatOpenAI 대신 직접 OpenAI 클라이언트 사용 (코드 일관성 유지)
            response = client.chat.completions.create(
                model="gpt-4o-mini", # 비용 효율적인 모델 사용
                messages=[
                    {"role": "system", "content": "너는 친절한 캠핑장 추천 전문가야."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=700
            )
            return response.choices[0].message.content
        except Exception as e:
            st.error(f"GPT 캠핑장 추천 중 오류가 발생했습니다: {e}")
            return "캠핑장 추천을 받지 못했습니다. 다시 시도해 주세요."

    with st.form("camp_search_form"):
        user_query = st.text_input("캠핑장에 대한 조건을 입력하세요 (예: 강원도 조용한 계곡 근처)", "")
        submitted_camp = st.form_submit_button("추천 받기")

    if submitted_camp:
        if not user_query.strip():
            st.warning("조건을 입력해 주세요.")
        else:
            with st.spinner("🤖 GPT가 캠핑장을 추천하는 중..."):
                result = ask_gpt_to_recommend_camp(user_query)
                st.subheader("✅ 추천 캠핑장")
                st.success(result)

# ==============================================================================
# --- 📈 주가 분석 기능 ---
# ==============================================================================
elif option == "주가 분석":
    st.header("📈 GPT 주가 분석기")
    st.markdown("한국 주식 종목의 주가 데이터를 기반으로 GPT가 분석 결과를 제공합니다.")

    # ✅ 종목명 → 티커 자동 변환용 딕셔너리 생성
    @st.cache_data
    def get_ticker_dict():
        tickers = stock.get_market_ticker_list("KOSPI") + stock.get_market_ticker_list("KOSDAQ")
        # 종목명에 한글이 많으므로 ensure_ascii=False로 설정하여 한글 깨짐 방지
        return {stock.get_market_ticker_name(t): t for t in tickers}

    # ✅ 주가 조회 Tool (LangChain Agent가 사용할 수 있음)
    @tool
    def get_stock_price_data(ticker: str, days: int = 30):
        """지정한 티커에 대해 최근 N일간 주가 데이터(OHLVC)를 조회합니다.
        날짜는 YYYY-MM-DD 형식으로, 시가, 고가, 저가, 종가, 거래량 정보를 포함합니다.
        """
        end_date = datetime.today()
        # pykrx는 영업일만 반환하므로, 요청 일수를 여유 있게 잡고 나중에 자름
        start_date = end_date - timedelta(days=days * 1.5)

        try:
            df = stock.get_market_ohlcv_by_date(
                start_date.strftime('%Y%m%d'),
                end_date.strftime('%Y%m%d'),
                ticker
            )
            if df.empty:
                return f"종목 코드 {ticker}에 대한 주가 데이터를 찾을 수 없습니다."

            df = df.tail(days) # 최근 days 일 데이터만 사용
            df = df.reset_index()
            df["날짜"] = df["날짜"].dt.strftime("%Y-%m-%d")
            # JSON 직렬화 오류 방지를 위해 int/float 값을 문자열로 변환 (선택 사항, 그러나 안전)
            df['시가'] = df['시가'].apply(lambda x: f"{int(x):,}")
            df['고가'] = df['고가'].apply(lambda x: f"{int(x):,}")
            df['저가'] = df['저가'].apply(lambda x: f"{int(x):,}")
            df['종가'] = df['종가'].apply(lambda x: f"{int(x):,}")
            df['거래량'] = df['거래량'].apply(lambda x: f"{int(x):,}")

            return json.dumps(df.to_dict(orient="records"), ensure_ascii=False)
        except Exception as e:
            return f"주가 데이터 조회 중 오류가 발생했습니다: {e}"

    # ✅ 에이전트 초기화 (Streamlit 세션 전역에서 한 번만 실행되도록 캐싱)
    @st.cache_resource
    def init_agent():
        # ChatOpenAI 모델은 OpenAI 클라이언트와 별개로 LangChain Agent에서 사용됩니다.
        # 따라서 OPENAI_API_KEY 환경 변수가 필요합니다.
        model = ChatOpenAI(model="gpt-4o-mini", temperature=0, streaming=True)
        prompt = hub.pull("hwchase17/openai-tools-agent")

        prompt.messages[0].prompt.template = (
            "너는 주식 분석 전문가야. 사용자의 메시지에서 한국 주식 종목명을 추출하고 주가 데이터를 기반으로 분석해줘."
            " 항상 가장 관련성 높은 정보를 제공하고, 필요 시 주가 조회 도구(get_stock_price_data)를 활용해."
            " 최신 정보는 get_stock_price_data 도구를 통해서만 얻을 수 있어."
            " 답변은 항상 친절하고 유익하게 제공해줘."
        )

        tools = [get_stock_price_data] # TavilySearchResults는 선택 사항이므로 제거
        agent = create_openai_tools_agent(model, tools, prompt)
        executor = AgentExecutor(agent=agent, tools=tools, verbose=False, handle_parsing_errors=True)
        return executor

    # ✅ Chat 수행 함수
    def chat_with_agent(agent_executor, user_input):
        # LangChain Agent는 종목명 매칭 로직을 직접 포함하지 않으므로, 여기서 처리
        ticker_dict = get_ticker_dict()
        matched_ticker = None
        matched_name = None

        # 사용자 입력에서 종목명 또는 티커를 찾아서 실제 티커로 변환
        # rapidfuzz 같은 라이브러리를 사용하여 유사 종목 매칭을 추가할 수 있지만,
        # 여기서는 단순 포함 여부로 확인
        for name, ticker in ticker_dict.items():
            if name in user_input or ticker in user_input:
                matched_ticker = ticker
                matched_name = name
                break

        if matched_ticker:
            # 사용자의 질문에 실제 티커와 종목명을 포함시켜 Agent가 더 잘 이해하도록 유도
            modified_input = f"종목명 '{matched_name}' (티커: {matched_ticker})에 대한 질문입니다: {user_input}"
        else:
            modified_input = user_input # 매칭되는 종목이 없으면 원본 입력 사용

        return agent_executor.invoke({"input": modified_input})["output"]

    # 🔹 Streamlit UI
    ticker_dict = get_ticker_dict() # 종목명-티커 딕셔너리 로드
    agent_executor = init_agent() # Agent 초기화

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 🔹 대화 기록 출력
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 🔹 사용자 입력 처리
    user_input = st.chat_input("분석할 종목명이나 질문을 입력하세요 (예: '삼성전자 최근 주가 어때?', '카카오 1년치 주가 분석해줘')")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.spinner("🤖 GPT가 분석 중입니다..."):
            try:
                response = chat_with_agent(agent_executor, user_input)
            except Exception as e:
                response = f"❌ 오류 발생: {e}"

        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)