from langchain.tools import tool
import os
import requests
import json
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.chat_models import ChatOpenAI
from langchain import hub
from langchain.prompts.chat import SystemMessagePromptTemplate
import streamlit as st

@tool
def search_kakao_local_from_natural(natural_query: str) -> str:
    """
    사용자 자연어를 지역 + 장소 키워드로 분석한 후,
    카카오 API를 호출해 상위 5개 장소를 추천합니다.
    예: '거제도 파스타 맛집 추천해줘' → '거제 파스타'
    """
    # Step 1: LLM을 사용해 keyword 추출
    from langchain.output_parsers import StrOutputParser
    from langchain.prompts import PromptTemplate

    extraction_prompt = PromptTemplate.from_template("""
    다음 문장에서 지역명과 장소(또는 음식) 키워드를 추출해서 검색 가능한 형태로 만들어줘.
    예: '거제도 파스타 맛집 추천해줘' → 거제 파스타

    문장: {query}
    결과:""")
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    keyword_query = (extraction_prompt | llm | StrOutputParser()).invoke({"query": natural_query})

    # Step 2: 카카오 API 호출
    kakao_api_key = os.getenv("KAKAO_API_KEY")
    url = f"https://dapi.kakao.com/v2/local/search/keyword.json?query={keyword_query}"
    headers = { "Authorization": f"KakaoAK {kakao_api_key}" }
    res = requests.get(url, headers=headers).json()

    if "documents" not in res or len(res["documents"]) == 0:
        return f"[{keyword_query}]에 대한 검색 결과가 없습니다."

    results = [f"{doc['place_name']} - {doc['address_name']}" for doc in res["documents"][:5]]
    return "\n".join(results)


@st.cache_resource
def init_agent():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, streaming=True)
    prompt = hub.pull("hwchase17/openai-tools-agent")
    prompt.messages[0] = SystemMessagePromptTemplate.from_template(
    """
    너는 지역 기반 장소를 추천하는 똑똑한 도우미야.
    사용자가 입력한 문장에서 '지역'과 '장소 유형(또는 음식)'을 추출해서 반드시 search_kakao_local 툴을 사용해야 해.
    예를 들어 '거제도 파스타 맛집 추천해줘'라는 입력이 들어오면, query는 '거제도 파스타'가 되어야 해.
    반드시 search_kakao_local(query="지역+장소") 툴을 사용해서 결과를 보여줘.
    """
)

    
    tools = [search_kakao_local_from_natural]

    agent = create_openai_tools_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    return agent_executor

def main():
    st.title("카카오 로컬 추천 에이전트 🤖")
    user_input = st.chat_input("어디 주변에 뭐 찾을까요? (예: 판교동 레스토랑)")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.chat_message("assistant"):
            with st.spinner("검색 중..."):
                agent_executor = init_agent()
                response = agent_executor.invoke({"input": user_input})
                result = response["output"]
                st.markdown(result)
                st.session_state.messages.append({"role": "assistant", "content": result})

if __name__ == "__main__":
    main()
