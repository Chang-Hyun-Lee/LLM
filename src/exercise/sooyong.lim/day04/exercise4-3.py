import requests
import streamlit as st
from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, Tool, AgentType
import xml.etree.ElementTree as ET

# ✅ 공공데이터포털 GoCamping API Key
CAMP_API_KEY = "DCvakj3KUyfmU0c%2FF7CbsLX4VXkEjGdcDfj1A0tFvZzJZL9h70OoFvmEeWVg54OdoXH7mOXwxIHM45Mx6IVxlA%3D%3D"

# ✅ 캠핑장 데이터 가져오기
def fetch_campgrounds_from_api(num=10):
    url = (
        f"https://apis.data.go.kr/B551011/GoCamping/basedList"
        f"?serviceKey={CAMP_API_KEY}"
        f"&numOfRows={num}&pageNo=1&MobileOS=ETC&MobileApp=campApp&_type=xml"
    )
    response = requests.get(url)
    if response.status_code != 200:
        return []

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

# ✅ GPT가 읽기 좋은 포맷으로 정리
def format_campgrounds(camps):
    text = ""
    for c in camps:
        text += f"{c['이름']} | {c['주소']} | {c['특징']} | {c['설명']}\n"
    return text.strip()

# ✅ 캠핑장 추천 함수
def recommend_campgrounds(query: str) -> str:
    camps = fetch_campgrounds_from_api(15)
    if not camps:
        return "캠핑장 정보를 불러오지 못했습니다. 다시 시도해 주세요."

    formatted = format_campgrounds(camps)
    prompt = (
        f"아래는 최근 캠핑장 목록입니다:\n\n{formatted}\n\n"
        f"이 중 사용자가 '{query}' 조건에 맞는 캠핑장을 찾고 있어.\n"
        f"조건에 잘 맞는 곳 2~3곳을 추천해주고, 각각의 특징도 간단히 설명해줘."
    )

    llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
    response = llm.predict(prompt)
    return response

# ✅ LangChain Tool
tools = [
    Tool(
        name="CampgroundRecommender",
        func=recommend_campgrounds,
        description="한국의 캠핑장 중 사용자의 조건에 맞는 캠핑장을 추천해주는 도우미"
    )
]

# ✅ Agent 초기화
llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=False)

# ✅ Streamlit UI 구성
st.set_page_config(page_title="⛺ GoCamping 캠핑장 추천기", page_icon="🏕️")
st.title("🏕️ GPT 캠핑장 추천기 (공공데이터 기반)")
st.markdown("**공공데이터포털의 GoCamping 데이터를 기반으로 조건에 맞는 캠핑장을 추천해드립니다.**")

with st.form("camp_form"):
    user_query = st.text_input("캠핑장에 대한 조건을 입력하세요 (예: 강원도 조용한 계곡 근처)", "")
    submitted = st.form_submit_button("추천 받기")

if submitted:
    if not user_query.strip():
        st.warning("조건을 입력해 주세요.")
    else:
        with st.spinner("GPT가 캠핑장을 추천하는 중..."):
            result = agent.run(user_query)
            st.subheader("✅ 추천 캠핑장")
            st.success(result)
