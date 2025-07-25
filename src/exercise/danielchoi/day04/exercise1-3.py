import streamlit as st
import requests
import json
import os
from langchain_openai import OpenAI
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
import pandas as pd
from langchain.docstore.document import Document

# API 키 설정
GOCAMPING_API_KEY = "K2AYhwdzrV2Si6dE0o2o4teC1rALEVMixfdEP1Fqb8LwXQ52mSS1DMeBj8ZPhfMKr8ZguxMCI8L%2BYcFAgsLMiQ%3D%3D"
os.environ["OPENAI_API_KEY"] = "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"

# Streamlit 페이지 설정
st.set_page_config(page_title="캠핑장 추천 도우미", page_icon="⛺")
st.title("⛺ 캠핑장 추천 시스템")

def get_camping_data(keyword: str = ""):
    """고캠핑 API에서 캠핑장 정보를 가져오는 함수"""
    try:
        # 검색어가 있는 경우 searchList API 사용
        if keyword:
            url = f"http://apis.data.go.kr/B551011/GoCamping/searchList"
            params = {
                'serviceKey': GOCAMPING_API_KEY,
                'numOfRows': 50,  # 더 많은 결과
                'pageNo': 1,
                'MobileOS': 'ETC',
                'MobileApp': 'TestApp',
                '_type': 'json',
                'keyword': keyword
            }
        else:
            url = f"http://apis.data.go.kr/B551011/GoCamping/basedList"
            params = {
                'serviceKey': GOCAMPING_API_KEY,
                'numOfRows': 50,
                'pageNo': 1,
                'MobileOS': 'ETC',
                'MobileApp': 'TestApp',
                '_type': 'json'
            }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data['response']['body']['items']['item']
            
    except Exception as e:
        st.error(f"API 호출 중 오류가 발생했습니다: {e}")
        return []

def create_vectorstore(camping_data):
    """캠핑장 데이터로 벡터 스토어 생성"""
    # 캠핑장 데이터를 문서 형태로 변환
    documents = []
    for camp in camping_data:
        text = f"""
        캠핑장명: {camp['facltNm']}
        주소: {camp['addr1']}
        소개: {camp['lineIntro']}
        입지: {camp.get('lctCl', '')}
        업종: {camp.get('induty', '')}
        운영기간: {camp.get('operPdCl', '')}
        전화: {camp.get('tel', '')}
        홈페이지: {camp.get('homepage', '')}
        """
        documents.append(text)
    
    # 벡터 스토어 생성
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents([Document(page_content=doc) for doc in documents], embeddings)
    
    return vectorstore, documents

def analyze_camping_sites(query: str, camping_data: list) -> str:
    """LangChain 에이전트를 사용한 캠핑장 분석"""
    # 데이터프레임 생성
    df = pd.DataFrame(camping_data)
    
    # 필요한 컬럼만 선택
    df = df[['facltNm', 'addr1', 'lineIntro', 'tel', 'lctCl', 'induty', 'operPdCl', 'sbrsCl', 'posblFcltyCl']]
    
    # 에이전트 생성
    llm = OpenAI(temperature=0.7, model_name="gpt-3.5-turbo-instruct")
    agent = create_pandas_dataframe_agent(
        llm,
        df,
        verbose=True,
        handle_parsing_errors=True,
        allow_dangerous_code=True
    )
    
    # 분석 프롬프트
    prompt = f"""
사용자가 찾는 조건: {query}

다음 정보를 기반으로 가장 적합한 캠핑장을 찾아주세요:
1. facltNm: 캠핑장명
2. addr1: 주소
3. lineIntro: 한줄소개
4. lctCl: 입지 (산, 숲, 계곡, 해변 등)
5. induty: 업종 (일반야영장, 글램핑, 카라반 등)
6. sbrsCl: 부대시설
7. posblFcltyCl: 주변이용가능시설

분석 단계:
1. 사용자 조건과 가장 잘 맞는 캠핑장 3곳을 찾아주세요
2. 각 캠핑장의 장단점을 분석해주세요
3. 시설과 주변 환경을 고려한 추천 이유를 설명해주세요

한글로 친절하게 답변해주세요.
"""
    
    try:
        response = agent.run(prompt)
        return response
    except Exception as e:
        return f"분석 중 오류가 발생했습니다: {str(e)}"

# 사이드바에 검색 폼 배치
with st.sidebar:
    st.header("🔍 검색 설정")
    search_query = st.text_input(
        "원하는 캠핑장 조건을 입력하세요",
        placeholder="예: 바다가 보이는 조용한 캠핑장",
        help="자연환경, 시설, 분위기 등 원하는 조건을 자유롭게 입력하세요."
    )
    
    search_button = st.button("검색 시작", type="primary")

# 메인 화면에 결과 표시
if search_button and search_query:
    try:
        with st.spinner("캠핑장 정보를 가져오는 중..."):
            # 검색어로 캠핑장 데이터 가져오기
            camping_data = get_camping_data(search_query)
            
            if not camping_data:
                st.warning("검색 결과가 없습니다. 다른 검색어로 시도해보세요.")
            else:
                # 데이터프레임 생성
                df = pd.DataFrame(camping_data)
                
                # 검색 결과 수 표시
                st.success(f"총 {len(df)}개의 캠핑장이 검색되었습니다.")
                
                # 기본 정보 표시
                st.subheader("📍 검색된 캠핑장 목록")
                display_df = df[['facltNm', 'addr1', 'lineIntro', 'tel', 'lctCl', 'induty']].copy()
                display_df.columns = ['캠핑장명', '주소', '소개', '연락처', '입지', '업종']
                st.dataframe(display_df, use_container_width=True)
                
                # AI 분석 결과
                with st.spinner("AI가 캠핑장을 분석하는 중..."):
                    analysis = analyze_camping_sites(search_query, camping_data)
                    st.subheader("🤖 AI 캠핑장 추천")
                    st.write(analysis)
                    
    except Exception as e:
        st.error(f"오류가 발생했습니다: {str(e)}")
else:
    st.info("👈 왼쪽 사이드바에서 원하는 캠핑장 조건을 입력하고 검색 버튼을 클릭하세요.")
    
    st.markdown("""
    ### 💡 검색 팁
    - 자연환경을 구체적으로 명시해보세요
        - 예: "바다가 보이는 캠핑장"
        - 예: "산속 계곡 근처 캠핑장"
    - 원하는 시설이나 분위기를 설명해보세요
        - 예: "반려동물 동반 가능한 조용한 캠핑장"
        - 예: "글램핑 시설이 있는 가족 캠핑장"
    """)