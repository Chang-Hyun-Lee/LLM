import os
import streamlit as st
import openai
import requests
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import tool
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain_core.prompts import MessagesPlaceholder

# Kakao 지도 API 도구
@tool
def get_restaurant_info(place: str, kind: str):
    """지역과 음식 종류를 받아 식당 정보 반환"""
    query = f"{place} {kind}"
    kakao_api_key = os.getenv("KAKAO_API_KEY")
    url = f"https://dapi.kakao.com/v2/local/search/keyword.json?query={query}"
    headers = {"Authorization": f"KakaoAK {kakao_api_key}"}
    response = requests.get(url, headers=headers).json()
    return response

# Agent 프롬프트
prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        "당신은 식당 추천 전문가입니다. 장소와 종류를 받아서 식당을 추천하세요. 추천할 식당이 없으면 없다고 답하세요."
    ),
    HumanMessagePromptTemplate.from_template("{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad")  # 필수
])

# Agent 초기화
@st.cache_resource
def init_agent():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    tools = [get_restaurant_info]
    agent = create_openai_tools_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    return executor

# GPT 응답에서 식당 정보 추출 및 카드 출력
def show_restaurants(data):
    for doc in data.get("documents", []):
        name = doc.get("place_name", "이름 없음")
        address = doc.get("road_address_name", doc.get("address_name", "주소 없음"))
        category = doc.get("category_name", "카테고리 없음")
        url = f"https://search.naver.com/search.naver?query={name}"

        with st.container():
            st.markdown(f"### [{name}]({url})")
            st.write(f"📍 {address}")
            st.write(f"🍴 카테고리: {category}")
            st.markdown("---")

# Streamlit 앱
def main():
    st.set_page_config(page_title="맛집 GPT 챗봇", page_icon="🍜")
    st.title("🍜 GPT 기반 카드형 맛집 추천 챗봇")
    agent_executor = init_agent()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("지역과 음식 종류를 입력해주세요 (예: 거제 해산물)")
    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.spinner("GPT가 식당을 찾고 있어요..."):
            response = agent_executor.invoke({"input": user_input})
            output = response["output"]

        with st.chat_message("assistant"):
            if isinstance(output, dict) and "documents" in output:
                show_restaurants(output)
            else:
                st.markdown(output)
        st.session_state.messages.append({"role": "assistant", "content": str(output)})

if __name__ == "__main__":
    main()