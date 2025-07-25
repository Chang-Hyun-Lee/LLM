import os
import requests
from urllib.parse import quote
import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("❌ 'OPENAI_API_KEY' 환경변수가 설정되지 않았습니다.")
    st.stop()

llm = ChatOpenAI(model_name="gpt-4", openai_api_key=OPENAI_API_KEY)

GCAMP_API_KEY_RAW = "kuS/fQ3ICSDrvgpnSru44lJUxbyKbVSYRdGvIRMnoaJer7cd9/h5u42tN7XWrwH4FitT3uqYz+PQfoejRZdmkg=="
GCAMP_API_KEY = quote(GCAMP_API_KEY_RAW, safe='')

def search_campsites(keyword: str, limit: int = 5):
    try:
        encoded_keyword = quote(keyword)
        url = (
            f"https://apis.data.go.kr/B551011/GoCamping/searchList"
            f"?serviceKey={GCAMP_API_KEY}&MobileOS=ETC&MobileApp=CampingTest"
            f"&_type=json&keyword={encoded_keyword}&numOfRows={limit}"
        )
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])

        # 빈 문자열이면 빈 리스트로
        if isinstance(items, str) and items == "":
            items = []

        # 딕셔너리면 리스트로 감싸기
        if isinstance(items, dict):
            items = [items]

        # None 혹은 빈값이면 빈 리스트로 처리
        if not items:
            items = []

        return items
    except requests.exceptions.Timeout:
        st.warning("⏱️ 요청 시간이 초과되었습니다. 네트워크 상태를 확인하세요.")
        return []
    except Exception as e:
        st.error(f"❌ 캠핑장 검색 오류 발생: {e}")
        return []

st.set_page_config(page_title="캠핑장 추천기", layout="wide")
st.title("🏕️ 캠핑장 검색 및 GPT 추천기")

user_input = st.text_input("캠핑장 조건 입력 (예: 강원도 바다 근처)", value="강원도 바다")

if st.button("🔍 캠핑장 검색 및 추천 시작"):
    with st.spinner("캠핑장 검색 중..."):
        campsites = search_campsites(user_input, limit=5)

    if not campsites:
        st.warning("조건에 맞는 캠핑장을 찾을 수 없습니다.")
    else:
        summaries = []
        for site in campsites:
            name = site.get('facltNm', '이름 없음')
            addr = site.get('addr1', '주소 없음')
            theme = site.get('lctCl', '테마 없음')
            summaries.append(f"- {name} ({addr}) / 테마: {theme}")

        prompt = f"""
다음은 '{user_input}' 조건으로 검색된 캠핑장 목록입니다:

{chr(10).join(summaries)}

이 중 초보자나 가족 단위 여행자에게 적합한 2~3곳을 추천하고 간단한 이유를 설명해 주세요.
"""

        with st.spinner("GPT가 추천 중..."):
            response = llm([
                SystemMessage(content="당신은 캠핑장 추천 전문가입니다."),
                HumanMessage(content=prompt)
            ])

        st.subheader("🏕️ GPT 캠핑장 추천 결과")
        st.write(response.content)
