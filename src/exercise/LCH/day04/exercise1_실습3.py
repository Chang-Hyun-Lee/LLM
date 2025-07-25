import streamlit as st
import requests
import xml.etree.ElementTree as ET
from langchain.agents import initialize_agent, Tool
from langchain.chat_models import ChatOpenAI
from langchain.agents.agent_types import AgentType
import os

# API 키 설정
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
GOCAMPING_API_KEY = 'qVIFfwvBFGmr6r4QBzTX1wKVxP6KHx7UpB6SE2Iyho8%2Bn071XEofG4zjwTk39hDktTo%2Fii91yaPRg10Psldjlg%3D%3D'

# 고캠핑 검색 함수
def search_camping_sites(keyword):
    url = "https://apis.data.go.kr/B551011/GoCamping/searchList"
    params = {
        'serviceKey': 'qVIFfwvBFGmr6r4QBzTX1wKVxP6KHx7UpB6SE2Iyho8%2Bn071XEofG4zjwTk39hDktTo%2Fii91yaPRg10Psldjlg%3D%3D',
        'numOfRows': 3,  # 추천할 캠핑장 수
        'pageNo': 1,
        'MobileOS': 'AND',
        'MobileApp': 'AppTest',
        'keyword' : '계곡'
    }

    res = requests.get(url, params=params)
    if res.status_code != 200:
        return "고캠핑 API 호출에 실패했습니다."

    root = ET.fromstring(res.content)
    items = root.findall(".//item")

    if not items:
        return "검색 결과가 없습니다."

    results = []
    for item in items:
        name = item.findtext("facltNm")
        addr = item.findtext("addr1")
        intro = item.findtext("lineIntro") or ""
        link = item.findtext("homepage") or "홈페이지 없음"
        results.append(f"🏕️ {name}\n📍 {addr}\n📝 {intro}\n🔗 {link}\n")

    return "\n---\n".join(results)

# LangChain Tool 정의
camping_tool = Tool(
    name="GoCamping API Search",
    func=lambda x: search_camping_sites(x),
    description="입력된 키워드로 고캠핑 API에서 캠핑장을 검색합니다. (예: '강원도 계곡')"
)

# LangChain Agent 구성
llm = ChatOpenAI(temperature=0.3, model="gpt-4o-mini")
agent = initialize_agent(
    tools=[camping_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=False
)

# Streamlit UI 구성
st.set_page_config(page_title="캠핑장 추천기", layout="centered")
st.title("LangChain + 고캠핑 API 기반 캠핑장 추천")

query = st.text_input("🌲 캠핑장을 어떻게 찾고 싶으신가요?", value="부산 바다 근처 캠핑장 추천해줘")

if st.button("추천받기"):
    with st.spinner("AI 에이전트가 캠핑장을 찾고 있습니다..."):
        response = agent.run(query)
        st.success("✅ 추천 완료!")
        st.markdown(response)