import streamlit as st
import requests
from langchain.agents import initialize_agent, Tool
from langchain.chat_models import ChatOpenAI
from langchain.agents.agent_types import AgentType
import os

# API 키 설정
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
KAPI_KEY = "f412e2dc68a71b3bdef7103db669eab9"

# 카카오맵 장소 검색 함수
def search_restaurants_kakao(query):
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {
        "Authorization": f"KakaoAK {KAPI_KEY}"
    }
    params = {
        "query": query,
        "category_group_code": "FD6",  # 음식점만 필터링
        "size": 5  # 결과 개수 제한
    }

    res = requests.get(url, headers=headers, params=params)
    if res.status_code != 200:
        return "카카오맵 API 호출 실패"

    data = res.json()["documents"]
    if not data:
        return "검색 결과가 없습니다."

    results = []
    for place in data:
        name = place["place_name"]
        address = place["road_address_name"]
        url = place["place_url"]
        results.append(f"🍽️ {name}\n📍 {address}\n🔗 [지도에서 보기]({url})\n")

    return "\n---\n".join(results)

# LangChain 툴 정의
restaurant_tool = Tool(
    name="KakaoMap Restaurant Finder",
    func=lambda query: search_restaurants_kakao(query),
    description="입력된 키워드(예: '강남 파스타')로 음식점을 검색합니다."
)

# LangChain Agent 구성
llm = ChatOpenAI(temperature=0.3, model="gpt-4o-mini")
agent = initialize_agent(
    tools=[restaurant_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=False
)

# Streamlit UI
st.set_page_config(page_title="AI 레스토랑 검색기", layout="centered")
st.title("🍽️ LangChain + 카카오맵 기반 레스토랑 검색기")

query = st.text_input("어떤 지역/음식점을 찾고 싶으신가요?", value="거제 국밥집")

if st.button("검색하기"):
    with st.spinner("AI 에이전트가 검색 중입니다..."):
        response = agent.run(f"{query} 근처의 맛집을 찾아줘")
        st.success("✅ 검색 완료!")
        st.markdown(response)