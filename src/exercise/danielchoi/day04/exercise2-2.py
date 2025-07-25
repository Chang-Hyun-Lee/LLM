import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime, timedelta
from langchain_openai import OpenAI
from langchain_experimental.agents import create_pandas_dataframe_agent
from pykrx import stock
import re
from typing import List, Dict, Tuple

# 환경 설정
os.environ["OPENAI_API_KEY"] = "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"
st.set_page_config(page_title="🤖 Smart Multi-Agent Assistant", page_icon="🤖", layout="wide")

# 마스터 에이전트
class MasterAgent:
    def __init__(self):
        self.llm = OpenAI(temperature=0.1, model_name="gpt-3.5-turbo-instruct")
        self.restaurant_agent = RestaurantAgent()
        self.camping_agent = CampingAgent()
        self.stock_agent = StockAgent()

    def analyze_intent(self, user_input: str) -> Dict:
        """사용자 입력의 의도를 분석"""
        restaurant_keywords = ['맛집', '음식점', '레스토랑', '카페', '술집', '치킨', '피자', '파스타', '한식', '중식', '일식', '양식', '먹을곳', '식당']
        camping_keywords = ['캠핑', '캠핑장', '글램핑', '오토캠핑', '캐라반', '펜션', '야영', '텐트', '바베큐', '캠프']
        stock_keywords = ['주식', '종목', '투자', '매수', '매도', '차트', '주가', '코스피', '코스닥', '상장', '시가총액']
        company_patterns = [r'삼성전자|삼전', r'sk하이닉스|하닉', r'네이버|naver', r'카카오', r'\d{6}']

        user_lower = user_input.lower()
        is_stock = any(re.search(pattern, user_input) for pattern in company_patterns)
        restaurant_score = sum(1 for kw in restaurant_keywords if kw in user_lower)
        camping_score = sum(1 for kw in camping_keywords if kw in user_lower)
        stock_score = sum(1 for kw in stock_keywords if kw in user_lower)

        if is_stock or stock_score > max(restaurant_score, camping_score):
            intent = "stock"
        elif camping_score > restaurant_score:
            intent = "camping"
        elif restaurant_score > 0:
            intent = "restaurant"
        else:
            prompt = f"""
            사용자 입력: "{user_input}"
            다음 중 하나로 분류: restaurant, camping, stock, unknown
            결과만 반환:
            """
            intent = self.llm.invoke(prompt).strip().lower()
            if intent not in ['restaurant', 'camping', 'stock']:
                intent = 'unknown'

        return {'intent': intent, 'query': user_input}

    def process_request(self, user_input: str):
        """요청을 처리하고 적절한 에이전트로 라우팅"""
        analysis = self.analyze_intent(user_input)
        intent, query = analysis['intent'], analysis['query']
        st.write(f"🤖 **분석 결과**: {intent.upper()} 관련 질문으로 판단했습니다.")

        if intent == 'restaurant':
            self.restaurant_agent.search_and_analyze(query)
        elif intent == 'camping':
            self.camping_agent.search_and_analyze(query)
        elif intent == 'stock':
            self.stock_agent.search_and_analyze(query)
        else:
            st.warning("🤔 질문이 모호합니다. '맛집', '캠핑장', '주식' 관련 질문을 구체적으로 작성해주세요!")

# 레스토랑 에이전트
class RestaurantAgent:
    def __init__(self):
        self.api_key = "c662192f1e74c3c14e16950ee0d6d5e1"
        self.llm = OpenAI(temperature=0.7, model_name="gpt-3.5-turbo-instruct")

    def search_restaurants(self, query: str) -> List[Dict]:
        """Kakao Local API로 레스토랑 검색"""
        if not self.api_key:
            return self._get_dummy_data(query)
        
        url = "https://dapi.kakao.com/v2/local/search/keyword.json"
        headers = {"Authorization": f"KakaoAK {self.api_key}"}
        params = {"query": f"{query} 맛집", "category_group_code": "FD6", "size": 10}
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json().get("documents", [])
        except Exception as e:
            st.error(f"⚠️ 검색 오류: {e}")
            return self._get_dummy_data(query)

    def _get_dummy_data(self, query: str) -> List[Dict]:
        """API 오류 시 더미 데이터"""
        return [
            {"place_name": f"{query} 맛집", "category_name": "한식", "address_name": "서울 강남구", "x": "127.027", "y": "37.497"}
        ]

    def search_and_analyze(self, query: str):
        """레스토랑 검색 및 분석"""
        with st.spinner("🍽️ 맛집 검색 중..."):
            results = self.search_restaurants(query)
            if not results:
                st.warning("😕 검색 결과가 없습니다.")
                return
            
            st.success(f"🍽️ {len(results)}개의 맛집을 찾았습니다!")
            df = pd.DataFrame(results)
            st.dataframe(df[['place_name', 'category_name', 'address_name']].rename(
                columns={'place_name': '이름', 'category_name': '카테고리', 'address_name': '주소'}
            ))

            if 'x' in df and 'y' in df:
                map_data = pd.DataFrame({
                    'lat': pd.to_numeric(df['y'], errors='coerce'),
                    'lon': pd.to_numeric(df['x'], errors='coerce')
                }).dropna()
                if not map_data.empty:
                    st.map(map_data)

            agent = create_pandas_dataframe_agent(self.llm, df, handle_parsing_errors=True, allow_dangerous_code=True)
            analysis = agent.run(f"'{query}' 맛집을 분석하고 TOP 3 추천과 방문 팁을 한국어로 제공하세요.")
            st.subheader("🤖 AI 추천")
            st.markdown(analysis)

# 캠핑 에이전트
class CampingAgent:
    def __init__(self):
        self.api_key = "K2AYhwdzrV2Si6dE0o2o4teC1rALEVMixfdEP1Fqb8LwXQ52mSS1DMeBj8ZPhfMKr8ZguxMCI8L%2BYcFAgsLMiQ%3D%3D"
        self.llm = OpenAI(temperature=0.7, model_name="gpt-3.5-turbo-instruct")

    def search_camping_sites(self, query: str) -> List[Dict]:
        """GoCamping API로 캠핑장 검색"""
        url = "http://apis.data.go.kr/B551011/GoCamping/searchList"
        params = {
            'serviceKey': self.api_key, 'numOfRows': 50, 'pageNo': 1,
            'MobileOS': 'ETC', 'MobileApp': 'App', '_type': 'json', 'keyword': query
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            items = response.json().get('response', {}).get('body', {}).get('items', {}).get('item', [])
            return items if items else []
        except Exception as e:
            st.error(f"⚠️ 검색 오류: {e}")
            return self._get_dummy_data(query)

    def _get_dummy_data(self, query: str) -> List[Dict]:
        """API 오류 시 더미 데이터"""
        return [{"facltNm": f"{query} 캠핑장", "addr1": "경기도 가평", "lineIntro": "자연 속 캠핑"}]

    def search_and_analyze(self, query: str):
        """캠핑장 검색 및 분석"""
        with st.spinner("🏕️ 캠핑장 검색 중..."):
            results = self.search_camping_sites(query)
            if not results:
                st.warning("😕 검색 결과가 없습니다.")
                return
            
            st.success(f"🏕️ {len(results)}개의 캠핑장을 찾았습니다!")
            df = pd.DataFrame(results)
            st.dataframe(df[['facltNm', 'addr1', 'lineIntro']].rename(
                columns={'facltNm': '이름', 'addr1': '주소', 'lineIntro': '소개'}
            ))

            agent = create_pandas_dataframe_agent(self.llm, df, handle_parsing_errors=True, allow_dangerous_code=True)
            analysis = agent.run(f"'{query}' 캠핑장을 분석하고 TOP 3 추천과 캠핑 팁을 한국어로 제공하세요.")
            st.subheader("🤖 AI 추천")
            st.markdown(analysis)

# 주식 에이전트
class StockAgent:
    def __init__(self):
        self.llm = OpenAI(temperature=0, model_name="gpt-3.5-turbo-instruct")
        self.stock_aliases = {"삼성전자": "005930", "카카오": "035720", "네이버": "035420"}

    def find_ticker(self, query: str) -> Tuple[str, str]:
        """종목 코드 찾기"""
        for alias, ticker in self.stock_aliases.items():
            if alias in query:
                return ticker, alias
        if re.match(r'\d{6}', query):
            return query, stock.get_market_ticker_name(query)
        return "", ""

    def get_stock_data(self, ticker: str) -> pd.DataFrame:
        """PyKRX로 주식 데이터 가져오기"""
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=90)).strftime("%Y%m%d")
        try:
            df = stock.get_market_ohlcv_by_date(start_date, end_date, ticker)
            df['5일평균'] = df['종가'].rolling(window=5).mean()
            return df
        except Exception as e:
            st.error(f"⚠️ 데이터 오류: {e}")
            return pd.DataFrame()

    def search_and_analyze(self, query: str):
        """주식 검색 및 분석"""
        with st.spinner("📈 주식 분석 중..."):
            ticker, name = self.find_ticker(query)
            if not ticker:
                st.warning("😕 종목을 찾을 수 없습니다. (예: 삼성전자, 005930)")
                return
            
            df = self.get_stock_data(ticker)
            if df.empty:
                st.warning("😕 주식 데이터를 가져올 수 없습니다.")
                return
            
            st.success(f"📈 {name} ({ticker}) 분석 완료!")
            st.line_chart(df[['종가', '5일평균']])
            agent = create_pandas_dataframe_agent(self.llm, df, handle_parsing_errors=True, allow_dangerous_code=True)
            analysis = agent.run(f"'{name}' 주식 데이터를 분석하고 주가 동향과 투자 의견을 한국어로 제공하세요.")
            st.subheader("🤖 AI 분석")
            st.markdown(analysis)

# 메인 함수
def main():
    st.title("🤖 Smart Multi-Agent Assistant")
    st.markdown("**말만 하세요! AI가 맛집, 캠핑장, 주식을 알아서 찾아드립니다.**")

    if 'master_agent' not in st.session_state:
        st.session_state.master_agent = MasterAgent()

    user_input = st.text_input("질문을 입력하세요:", placeholder="강남 맛집, 바다 캠핑장, 삼성전자 주식 등")
    if st.button("🔍 검색") and user_input:
        st.session_state.master_agent.process_request(user_input)

    with st.expander("💡 사용법"):
        st.markdown("""
        - **맛집**: "강남 파스타 맛집"
        - **캠핑**: "바다 근처 캠핑장"
        - **주식**: "삼성전자 주식"
        """)

if __name__ == "__main__":
    main()