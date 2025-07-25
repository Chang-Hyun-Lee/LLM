import os
import streamlit as st
import requests
from langchain.agents import initialize_agent, Tool
from langchain.agents.agent_types import AgentType
from langchain.chat_models import ChatOpenAI
from dotenv import load_dotenv
import json
from langchain.tools import StructuredTool

# 환경변수 불러오기
load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
kakao_api_key = "fec0d451a44400e161bb68d466933d9d"


def get_kakao_places(api_key: str, location: str, cuisine_type: str):
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {
        "Authorization": f"KakaoAK {api_key}"
    }
    params = {
        "query": f"{location} {cuisine_type}",
        "size": 5
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        return []

    data = response.json()
    return data.get("documents", [])

def recommend_restaurants(location: str, cuisine_type: str) -> str:
    # kakao_api_key는 미리 선언되어 있어야 함
    places = get_kakao_places(kakao_api_key, location, cuisine_type)
    
    if not places:
        return f"{location}에 {cuisine_type} 음식점이 없습니다."

    results = []
    for i, place in enumerate(places, 1):
        info = {
            "이름": place['place_name'],
            "주소": place['address_name'],
            "카테고리": place['category_name'],
            "전화번호": place.get('phone', '없음'),
            "링크": place.get('place_url', '없음')
        }
        results.append(info)

    return json.dumps(results, indent=2, ensure_ascii=False)

# LangChain용 OpenAI LLM 초기화
llm = ChatOpenAI(openai_api_key=openai_api_key, temperature=0.7, model_name="gpt-3.5-turbo")

# 에이전트 정의 (Kakao Tool만 사용)
tools = [StructuredTool.from_function(
        name="RecommendRestaurants",
        func=recommend_restaurants,
        description=(
            "사용자가 입력한 지역과 음식 종류(location, cuisine_type)를 기반으로 "
            "카카오 API에서 음식점 목록을 검색합니다. "
            "음식점 이름, 주소, 전화번호, 링크 정보를 포함한 JSON을 반환합니다. "
            "예: RecommendRestaurants(location='판교', cuisine_type='이탈리안')"
        )
    )]
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True,
    agent_kwargs={
        "prefix": "너는 음식점 정보를 추천해주는 도우미야. 결과는 JSON 형식으로 요약해줘.",
    }
)


# Streamlit UI
st.title("🍽️ 음식점 추천 챗봇 (LangChain + Kakao API)")

location = st.text_input("지역 입력 (예: 판교, 강남 등)")
cuisine_type = st.text_input("음식 종류 입력 (예: 중식, 일식, 치킨 등)")

if st.button("추천받기"):
    if not location or not cuisine_type:
        st.warning("지역과 음식 종류를 모두 입력해주세요.")
    else:
        with st.spinner("음식점 추천 중..."):
            prompt = f"{location}에서 {cuisine_type} 음식점 알려줘."
            result = agent.run(prompt)
            st.subheader("추천 결과:")
            st.code(result, language="json")