import streamlit as st
import requests
import os
from langchain_openai import OpenAI
from langchain_experimental.agents import create_pandas_dataframe_agent
import pandas as pd
from typing import List, Dict

# API 키 설정
KAKAO_API_KEY = "YOUR_KAKAO_REST_API_KEY"  # 카카오 개발자 센터에서 발급
os.environ["OPENAI_API_KEY"] = "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"

# Streamlit 페이지 설정
st.set_page_config(page_title="맛집 검색 도우미", page_icon="🍽️")
st.title("🍽️ 맛집 검색 & 추천 시스템")

def search_restaurants(query: str) -> List[Dict]:
    """카카오 로컬 API로 음식점 검색"""
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {
        "query": query,
        "category_group_code": "FD6",  # 음식점 카테고리
        "size": 15  # 검색 결과 수
    }
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()["documents"]

def analyze_restaurants(df: pd.DataFrame, query: str) -> str:
    """LangChain agent를 사용한 음식점 분석 및 추천"""
    llm = OpenAI(
        temperature=0.7,
        model_name="gpt-3.5-turbo-instruct"
    )
    
    try:
        agent = create_pandas_dataframe_agent(
            llm,
            df,
            verbose=True,
            handle_parsing_errors=True,
            allow_dangerous_code=True,
            prefix="""
            당신은 맛집 추천 전문가입니다. 주어진 데이터를 기반으로 사용자의 요구사항에 맞는 맛집을 추천해주세요.
            데이터프레임에는 다음 정보가 포함되어 있습니다:
            - place_name: 음식점 이름
            - category_name: 음식점 카테고리
            - address_name: 주소
            - road_address_name: 도로명 주소
            - phone: 전화번호
            - place_url: 상세 정보 링크
            """
        )
        
        prompt = f"""
        검색어 "{query}"에 대한 음식점들을 분석하여 다음 형식으로 답변해주세요:

        1. 검색된 음식점들의 전반적인 특징
        2. 추천 맛집 TOP 3
           - 각 맛집별 추천 이유
           - 위치 및 접근성
           - 대표 메뉴 또는 특징
        3. 참고사항 (예약 필요 여부, 주차 가능 여부 등)

        한글로 친절하게 답변해주세요.
        """
        
        response = agent.run(prompt)
        return response
        
    except Exception as e:
        return f"분석 중 오류가 발생했습니다: {str(e)}"

# 사이드바에 검색 폼 배치
with st.sidebar:
    st.header("🔍 검색 설정")
    search_query = st.text_input(
        "검색어를 입력하세요",
        placeholder="예: 강남 파스타, 판교 한식",
        help="지역명과 음식 종류를 함께 입력하면 더 정확한 결과를 얻을 수 있습니다."
    )
    
    search_button = st.button("검색 시작", type="primary")

# 메인 화면에 결과 표시
if search_button and search_query:
    try:
        with st.spinner("맛집을 검색하는 중..."):
            # 음식점 검색
            restaurants = search_restaurants(search_query)
            
            if not restaurants:
                st.warning("검색 결과가 없습니다. 다른 검색어로 시도해보세요.")
            else:
                # 데이터프레임 생성
                df = pd.DataFrame(restaurants)
                
                # 기본 정보 표시
                st.subheader("📍 검색된 음식점 목록")
                st.dataframe(
                    df[['place_name', 'category_name', 'address_name', 'phone']],
                    use_container_width=True
                )
                
                # 지도 표시
                st.subheader("🗺️ 위치 정보")
                df['latitude'] = df['y'].astype(float)
                df['longitude'] = df['x'].astype(float)
                st.map(df[['latitude', 'longitude']])
                
                # AI 분석 결과
                with st.spinner("AI가 맛집을 분석하는 중..."):
                    analysis = analyze_restaurants(df, search_query)
                    st.subheader("🤖 AI 맛집 추천")
                    st.write(analysis)
                
    except Exception as e:
        st.error(f"오류가 발생했습니다: {str(e)}")
else:
    st.info("👈 왼쪽 사이드바에서 검색어를 입력하고 검색 버튼을 클릭하세요.")
    
    st.markdown("""
    ### 💡 검색 팁
    - 지역명과 음식 종류를 함께 입력해보세요
        - 예: "강남 스테이크"
        - 예: "판교 일식"
    - 특정 상황에 맞는 검색도 가능합니다
        - 예: "강남 데이트"
        - 예: "판교 회식"
    """)