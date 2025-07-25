# 실습 #4: Streamlit과 LangChain agent를 사용하여 예전에 만들었던 특정 종목의 주가를 분석해주는 어플리케이션을 작성하시오. 티커코드가 아닌 종목명으로 주가를 찾을 수 있도록 하시오. 종목명이 약간 틀려도 주가를 찾을 수 있어야 한다.
# 예) 엘지전자, (주)엘지전자, 주식회사 LG전자, LG 전자, LG전자(주) ...
# 엘쥐전자

# 실습 #5: 실습 #2, #3, #4을 하나로 합치시오(레스토랑, 캠핑, 주식).

# 실습 #6: llama_index의 실습(RAG)를 하나로 합치시오.

from pykrx import stock
from pykrx import bond
import openai
import os
from langchain import hub
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import tool
from langchain_core.callbacks import Callbacks
from langchain_core.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from dotenv import load_dotenv, find_dotenv
import json

with open("./krx_code.json", 'r', encoding='utf-8') as f:
    krx_code_json = json.load(f)
all_company_names = [row['종목명'] for row in krx_code_json if '종목명' in row]

@tool
def get_stock_price(start_day, end_day, krx_code)->str:
    """Return prices within given dates for krx_code. 
    start_day and end_day shoule be 'YYYYMMDD' format."""
    stock_data = stock.get_market_ohlcv(start_day, end_day, krx_code, "d")
    return stock_data.to_string() 

@tool
def get_krx_code(compay_name)->str:
    """krx에 상장된 회사이름으로 krx_code를 찾는 툴입니다. 
    Example: '삼성전자' -> '005930'"""
    # with open("./krx_code.json", 'r', encoding='utf-8') as f:
    #     krx_code_json = json.load(f)
    #     print (krx_code_json)
    for row in krx_code_json:
        if row['종목명'] == compay_name:
            krx_code = row.get('코드')
            break
    return krx_code 


path = find_dotenv() 
load_dotenv(path)
# openai.api_key = os.getenv("OPENAI_API_KEY")

model = ChatOpenAI()
prompt = hub.pull("hwchase17/openai-tools-agent")
prompt.messages[0] = SystemMessagePromptTemplate.from_template(
    f"""
    당신은 주식 분석가입니다. 주어진 정보를 보고 주식에 대한 의견을 전달하세요.
    krx code는 회사명을 이용하여 'get_krx_code'를 사용하여 조회합니다.
    회사명은 {all_company_names}중에서 하나을 선택합니다.
    유사한 회사명을 찾을 수 없는 경우, 회사명은 '삼성전자'로 적용합니다.
    그다음으로, 'get_stock_price'툴를 이용하여 주가 정보를 조회하세요.
    """)

tools = [get_krx_code, get_stock_price]
agent = create_openai_tools_agent(model.with_config({"tags": ["agent_llm"]}),tools, prompt)
# print (agent)

agent_executor = AgentExecutor(agent=agent, tools=tools).with_config(
    {"run_name": "Agent"}
)

input_prompt = "hinix 2025년 1월 주가 분석해 주세요"
response = agent_executor.invoke({"input":input_prompt})
print('*'*100)
print('input:\n',response['input'])
print('output:\n',response['output'])