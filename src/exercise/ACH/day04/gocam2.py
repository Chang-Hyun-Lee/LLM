import streamlit as st
import requests
import json
import os
from datetime import datetime
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.tools import Tool
from langchain_community.tools import TavilySearchResults

# 페이지 설정
st.set_page_config(page_title="캠핑장 추천 AI", page_icon="🏕️", layout="wide")

# 제목
st.title("🏕️ 캠핑장 추천 AI Assistant")
st.markdown("**LangChain Agent를 활용한 지능형 캠핑장 추천 도구**")

# 사이드바 API 키 설정
with st.sidebar:
    st.header("🔑 API 설정")
    openai_key = st.text_input(
        "OpenAI API Key", 
        type="password", 
        value="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"
    )
    tavily_key = st.text_input(
        "Tavily API Key", 
        type="password", 
        value="asst_vKsnmuZX2sUZI9vhdSAEVCKT"
    )
    
    st.markdown("---")
    st.markdown("### 🏕️ 추천 지역")
    st.markdown("""
    **🗺️ 인기 지역:**
    - 제주도, 강원도
    - 경기도, 충청도
    - 전라도, 경상도
    
    **🌟 테마별:**
    - 바다 근처 캠핑장
    - 산속 캠핑장
    - 가족 캠핑장
    """)

# 고캠핑 API 설정
GOCAMPING_API_KEY = "Cw/Ebj0gB2BAEfz2r9tWNqWSH0aszmbuIcanTHSX7NUgx1H3UEpFCXdGXvy+ZT3vU0KxKqXbQc9OUhu79BVFgw=="
BASE_URL = "https://apis.data.go.kr/B551011/GoCamping/basedList"

def search_camping_sites(keyword="", num_rows=10):
    """
    고캠핑 API를 사용하여 캠핑장 데이터를 검색하는 함수
    API가 작동하지 않을 경우 더미 데이터 제공
    """
    params = {
        'serviceKey': GOCAMPING_API_KEY,
        'numOfRows': num_rows,
        'pageNo': 1,
        'MobileOS': 'ETC',
        'MobileApp': 'CampingApp',
        '_type': 'json'
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.encoding = 'utf-8'
        
        st.write(f"🔍 API 요청 상태: {response.status_code}")
        st.write(f"📄 응답 길이: {len(response.text)} 문자")
        
        if response.status_code != 200:
            st.warning(f"API 요청 실패 (상태: {response.status_code}), 더미 데이터를 사용합니다.")
            return get_dummy_camping_data(keyword)
        
        if not response.text.strip():
            st.warning("API 응답이 비어있습니다. 더미 데이터를 사용합니다.")
            return get_dummy_camping_data(keyword)
            
        data = response.json()
        items = data.get('response', {}).get('body', {}).get('items', {}).get('item', [])
        
        if isinstance(items, dict):
            items = [items]
        elif not items:
            st.warning("API에서 데이터를 찾을 수 없습니다. 더미 데이터를 사용합니다.")
            return get_dummy_camping_data(keyword)
            
        # 키워드 필터링
        if keyword and items:
            filtered_items = []
            for item in items:
                name = item.get('facltNm', '')
                addr = item.get('addr1', '')
                if keyword in name or keyword in addr:
                    filtered_items.append(item)
            if filtered_items:
                items = filtered_items
        
        st.success(f"✅ {len(items)}개의 캠핑장 데이터를 찾았습니다!")
        return items
        
    except json.JSONDecodeError:
        st.warning("API 응답 파싱 오류. 더미 데이터를 사용합니다.")
        return get_dummy_camping_data(keyword)
    except Exception as e:
        st.warning(f"API 오류 ({str(e)}). 더미 데이터를 사용합니다.")
        return get_dummy_camping_data(keyword)

def get_dummy_camping_data(keyword=""):
    """더미 캠핑장 데이터 제공"""
    dummy_data = [
        {
            'facltNm': '제주 한라산 오토캠핑장',
            'addr1': '제주특별자치도 제주시 1100로 2070-61',
            'themaEnvrnCl': '산,계곡,호수',
            'intro': '한라산 자락에 위치한 자연친화적 캠핑장으로 맑은 공기와 아름다운 풍경을 자랑합니다.'
        },
        {
            'facltNm': '제주 협재해수욕장 캠핑장',
            'addr1': '제주특별자치도 제주시 한림읍 협재리',
            'themaEnvrnCl': '바다,해변',
            'intro': '에메랄드빛 바다가 한눈에 보이는 해변 캠핑장으로 일몰이 아름답습니다.'
        },
        {
            'facltNm': '강원 설악산 국립공원 캠핑장',
            'addr1': '강원특별자치도 속초시 설악동',
            'themaEnvrnCl': '산,계곡,국립공원',
            'intro': '설악산의 웅장한 자연 속에서 즐기는 힐링 캠핑의 명소입니다.'
        },
        {
            'facltNm': '강원 춘천 의암호 캠핑장',
            'addr1': '강원특별자치도 춘천시 신북읍',
            'themaEnvrnCl': '호수,물놀이',
            'intro': '의암호 호수가 내려다보이는 전망 좋은 캠핑장으로 가족 단위 이용객에게 인기입니다.'
        },
        {
            'facltNm': '경기 가평 자라섬 오토캠핑장',
            'addr1': '경기도 가평군 가평읍 자라섬로 60',
            'themaEnvrnCl': '섬,강,음악축제',
            'intro': '자라섬 재즈페스티벌로 유명한 섬에 위치한 특별한 캠핑장입니다.'
        },
        {
            'facltNm': '전남 순천만 국가정원 캠핑장',
            'addr1': '전라남도 순천시 국가정원1호길',
            'themaEnvrnCl': '습지,정원,생태',
            'intro': '순천만 갈대밭과 국가정원을 함께 즐길 수 있는 생태 친화적 캠핑장입니다.'
        },
        {
            'facltNm': '경북 경주 불국사 힐링캠프',
            'addr1': '경상북도 경주시 진현동 불국로',
            'themaEnvrnCl': '문화유적,산,휴양',
            'intro': '불국사와 석굴암 근처에 위치하여 역사와 자연을 동시에 체험할 수 있습니다.'
        },
        {
            'facltNm': '충북 단양 도담삼봉 캠핑장',
            'addr1': '충청북도 단양군 매포읍 도담상선길',
            'themaEnvrnCl': '강,절경,명승',
            'intro': '도담삼봉의 절경을 감상하며 남한강변에서 즐기는 캠핑의 진수를 느낄 수 있습니다.'
        }
    ]
    
    # 키워드가 있으면 필터링
    if keyword:
        filtered_data = []
        for camp in dummy_data:
            if (keyword in camp['facltNm'] or 
                keyword in camp['addr1'] or 
                keyword in camp['themaEnvrnCl']):
                filtered_data.append(camp)
        return filtered_data if filtered_data else dummy_data[:3]
    
    return dummy_data

def camping_recommendation_tool(query: str) -> str:
    """
    사용자 질문을 분석하여 적절한 캠핑장을 추천하는 도구
    """
    try:
        # OpenAI를 사용해 사용자 질문에서 키워드 추출
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=openai_key)
        
        extract_prompt = f"""
사용자의 캠핑장 추천 요청에서 검색 키워드를 추출해주세요:

사용자 질문: "{query}"

다음 JSON 형식으로만 응답해주세요:
{{
    "keyword": "검색_키워드",
    "region": "지역명",
    "theme": "테마"
}}

추출 규칙:
1. 지역명이 명시된 경우 해당 지역을 keyword로 사용 (예: 제주, 강원, 경기)
2. 테마가 있으면 theme에 기록 (예: 바다, 산, 가족, 펜션형)
3. 특별한 키워드가 없으면 keyword를 ""로 설정
"""
        
        response = llm.invoke(extract_prompt)
        params = json.loads(response.content)
        
        # 캠핑장 데이터 검색
        keyword = params.get("keyword", "")
        camping_data = search_camping_sites(keyword=keyword, num_rows=15)
        
        if not camping_data:
            return "❌ 캠핑장 데이터를 찾을 수 없습니다. 다른 키워드로 시도해보세요."
        
        # 캠핑장 정보를 텍스트로 변환
        camping_text = ""
        for i, item in enumerate(camping_data[:10], 1):  # 상위 10개만 사용
            name = item.get('facltNm', '정보 없음')
            addr = item.get('addr1', '주소 없음')
            feat = item.get('themaEnvrnCl', '특징 없음')
            intro = item.get('intro', '소개 없음')[:50] + "..." if item.get('intro') else '소개 없음'
            
            camp_info = f"{i}. **{name}**\n   - 주소: {addr}\n   - 특징: {feat}\n   - 소개: {intro}\n"
            camping_text += camp_info + "\n"
        
        # GPT로 추천 분석
        recommendation_prompt = f"""
사용자 질문: "{query}"

다음은 검색된 캠핑장 목록입니다:
{camping_text}

사용자의 요청에 가장 적합한 캠핑장 3곳을 선별하여 추천해주세요.

다음 형식으로 답변해주세요:
🏕️ **추천 캠핑장**

**1순위: [캠핑장명]**
- 📍 위치: [주소]
- ⭐ 추천 이유: [구체적인 이유]
- 🎯 특징: [주요 특징]

**2순위: [캠핑장명]**
- 📍 위치: [주소]  
- ⭐ 추천 이유: [구체적인 이유]
- 🎯 특징: [주요 특징]

**3순위: [캠핑장명]**
- 📍 위치: [주소]
- ⭐ 추천 이유: [구체적인 이유] 
- 🎯 특징: [주요 특징]

💡 **추가 팁**: [캠핑 관련 유용한 정보]
"""
        
        recommendation_response = llm.invoke(recommendation_prompt)
        return recommendation_response.content
        
    except Exception as e:
        return f"❌ 캠핑장 추천 중 오류가 발생했습니다: {str(e)}"

def analyze_camping_with_agent(user_query):
    """
    LangChain Agent를 사용하여 사용자 질문을 분석하고 적절한 도구를 호출
    """
    if not openai_key or not tavily_key:
        return "❌ API 키를 모두 입력해주세요."
    
    try:
        # 환경변수로 API 키 설정
        os.environ["TAVILY_API_KEY"] = tavily_key
        
        # LLM 초기화
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=openai_key)
        
        # 도구 정의
        camping_tool = Tool(
            name="camping_recommendation",
            description="캠핑장을 추천합니다. 지역, 테마, 조건이 포함된 질문에 사용하세요.",
            func=camping_recommendation_tool
        )
        
        search_tool = TavilySearchResults(
            max_results=3,
            description="최신 캠핑 정보나 캠핑 팁을 검색합니다."
        )
        
        tools = [camping_tool, search_tool]
        
        # 에이전트 프롬프트
        prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 전문적인 캠핑장 추천 AI입니다.

사용 가능한 도구:
1. camping_recommendation: 고캠핑 API 기반 캠핑장 추천
2. tavily_search_results_json: 최신 캠핑 정보나 팁 검색

사용자 질문을 분석하여:
- 특정 지역이나 조건의 캠핑장 추천 요청 → camping_recommendation 도구 사용
- 캠핑 팁, 최신 캠핑 트렌드, 장비 정보 등 → tavily_search_results_json 도구 사용
- 필요시 두 도구를 모두 사용하여 종합적인 추천 제공

항상 친절하고 전문적으로 답변하세요."""),
            ("user", "{input}"),
            ("assistant", "{agent_scratchpad}")
        ])
        
        # 에이전트 생성 및 실행
        agent = create_openai_tools_agent(llm, tools, prompt)
        executor = AgentExecutor(agent=agent, tools=tools, verbose=False)
        
        result = executor.invoke({"input": user_query})
        return result["output"]
        
    except Exception as e:
        return f"❌ Agent 실행 오류: {str(e)}"

# 메인 UI
st.markdown("---")

# 예제 질문 섹션
st.subheader("💡 예제 질문")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("제주도 캠핑장", use_container_width=True):
        st.session_state.query = "제주도에서 바다가 보이는 캠핑장 추천해줘"

with col2:
    if st.button("강원도 산속", use_container_width=True):
        st.session_state.query = "강원도 산속에 있는 조용한 캠핑장 찾아줘"

with col3:
    if st.button("가족 캠핑장", use_container_width=True):
        st.session_state.query = "아이들과 함께 가기 좋은 가족 캠핑장 추천해줘"

with col4:
    if st.button("캠핑 팁", use_container_width=True):
        st.session_state.query = "겨울 캠핑할 때 주의사항과 팁 알려줘"

# 사용자 입력
st.markdown("### 🎯 캠핑장 추천 질문")
user_input = st.text_input(
    "원하는 캠핑장 조건을 입력하세요:",
    value=st.session_state.get('query', ''),
    placeholder="예: 제주도 바다 근처 캠핑장 / 강원도 산속 조용한 곳 / 가족과 함께 갈 만한 곳"
)

# 분석 실행
if st.button("🔍 AI 추천 시작", type="primary", use_container_width=True):
    if user_input.strip():
        with st.spinner("🤖 AI Agent가 최적의 캠핑장을 찾고 있습니다..."):
            result = analyze_camping_with_agent(user_input)
            
        st.markdown("### 🏕️ 추천 결과")
        st.markdown(result)
    else:
        st.warning("⚠️ 원하는 캠핑장 조건을 입력해주세요.")

# 캠핑장 직접 검색 기능
st.markdown("---")
with st.expander("🔍 캠핑장 직접 검색"):
    search_keyword = st.text_input("검색 키워드 (지역명 등):", placeholder="예: 제주, 강원, 경기")
    
    if st.button("검색", key="direct_search"):
        if search_keyword:
            with st.spinner("검색 중..."):
                camping_data = search_camping_sites(keyword=search_keyword, num_rows=5)
                
            if camping_data:
                st.success(f"🎯 '{search_keyword}' 검색 결과: {len(camping_data)}개")
                
                for i, camp in enumerate(camping_data, 1):
                    with st.container():
                        st.markdown(f"**{i}. {camp.get('facltNm', '이름 없음')}**")
                        st.write(f"📍 주소: {camp.get('addr1', '주소 없음')}")
                        st.write(f"🏕️ 특징: {camp.get('themaEnvrnCl', '특징 없음')}")
                        if camp.get('intro'):
                            st.write(f"ℹ️ 소개: {camp.get('intro')[:100]}...")
                        st.markdown("---")
            else:
                st.error("❌ 검색 결과가 없습니다.")

# 하단 정보
st.markdown("---")
with st.expander("ℹ️ 사용법 및 정보"):
    st.markdown("""
    ### 🚀 사용법
    1. **지역 지정**: "제주도", "강원도", "경기도" 등으로 표현
    2. **테마 설정**: "바다 근처", "산속", "가족 캠핑" 등으로 표현
    3. **질문 형태**: "제주도에서 바다가 보이는 캠핑장 추천해줘" 형태로 입력
    
    ### 🏕️ 제공 정보
    - 캠핑장 이름, 주소
    - 주요 특징 및 테마
    - 추천 순위 및 이유
    - 캠핑 관련 팁
    
    ### 🔧 기술 스택
    - **Streamlit**: 웹 인터페이스
    - **LangChain Agent**: 지능형 질문 처리
    - **고캠핑 API**: 실시간 캠핑장 데이터
    - **OpenAI GPT**: 자연어 처리 및 추천
    - **Tavily**: 최신 캠핑 정보 검색
    
    ### 📋 데이터 출처
    - **고캠핑**: 한국관광공사 캠핑장 정보 서비스
    """)

# API 키 상태 표시
if openai_key and tavily_key:
    st.success("✅ 모든 API 키가 설정되었습니다. 캠핑장 추천을 시작할 수 있습니다!")
else:
    st.error("❌ 사이드바에서 API 키를 입력해주세요.")