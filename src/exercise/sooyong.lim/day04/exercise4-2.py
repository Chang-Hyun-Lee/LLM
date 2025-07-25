import os
import streamlit as st
import requests
from openai import OpenAI

# 환경변수에서 OpenAI API 키 가져오기
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 카카오 API 키 (보안을 위해 환경변수 사용 권장)
KAKAO_REST_API_KEY = "c662192f1e74c3c14e16950ee0d6d5e1"

def search_restaurants_kakao(query, location, size=5):
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
    params = {
        "query": f"{location} {query}",
        "size": size,
        "page": 1,
        "sort": "accuracy",
        "category_group_code": "FD6",  # 음식점 카테고리
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    results = response.json()
    return results.get("documents", [])

def format_restaurants_for_gpt(restaurants):
    formatted = ""
    for r in restaurants:
        name = r.get("place_name", "이름 없음")
        address = r.get("address_name", "주소 없음")
        phone = r.get("phone", "번호 없음")
        category = r.get("category_name", "카테고리 없음")
        formatted += f"{name} | {category} | 주소: {address} | 전화: {phone}\n"
    return formatted

def ask_gpt_to_recommend(restaurants_text, location, user_question):
    prompt = (
        f"아래는 '{location}' 지역의 음식점 목록입니다:\n\n"
        f"{restaurants_text}\n\n"
        f"이 중에서 '{user_question}'에 맞게 3곳 추천하고, 간단한 설명도 덧붙여줘."
    )

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

# ✅ Streamlit 앱 인터페이스 시작
st.set_page_config(page_title="맛집 추천 GPT", page_icon="🍴")
st.title("🍽️ GPT 맛집 추천기")
st.markdown("카카오 API와 GPT를 활용한 지역 기반 맛집 추천 시스템입니다.")

with st.form("search_form"):
    location = st.text_input("지역을 입력하세요 (예: 홍대, 판교 등)", "")
    query = st.text_input("어떤 음식점이 궁금한가요? (예: 괜찮은 이탈리안 식당)", "")
    submitted = st.form_submit_button("추천받기")

if submitted:
    if not location or not query:
        st.warning("지역과 검색 조건을 모두 입력해주세요.")
    else:
        with st.spinner("🔎 카카오 API로 음식점 검색 중..."):
            try:
                restaurants = search_restaurants_kakao(query, location, size=7)
                if not restaurants:
                    st.error("검색된 음식점이 없습니다. 다른 조건을 시도해 보세요.")
                else:
                    restaurants_text = format_restaurants_for_gpt(restaurants)
                    st.subheader("📋 검색된 음식점 목록")
                    st.text(restaurants_text)

                    with st.spinner("🤖 GPT에게 추천 요청 중..."):
                        recommendation = ask_gpt_to_recommend(restaurants_text, location, query)
                        st.subheader("🍴 GPT 추천 결과")
                        st.success(recommendation)
            except Exception as e:
                st.error(f"오류 발생: {e}")
