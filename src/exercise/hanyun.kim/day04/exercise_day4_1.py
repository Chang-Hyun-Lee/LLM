# 실습 #1: Streamlit과 LangChain agent를 사용하여 예전에 만들었던 특정 종목의 주가를 분석해주는 
#         어플리케이션을 작성하시오.
# 실습 #2: Streamlit과 LangChain agent를 사용하여 예전에 만들었던 레스토랑을 찾아서 검색해주는 
#         어플리케이션을 작성하시오.
# 실습 #3: Streamlit과 LangChain agent를 사용하여 예전에 만들었던 캠핑장을 추천해주는 
#         어플리케이션을 작성하시오.

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


@tool
def get_stock_price(start_day, end_day, krx_code)->str:
    """Return prices within given dates for krx_code. 
    start_day and end_day shoule be 'YYYYMMDD' format."""
    stock_data = stock.get_market_ohlcv(start_day, end_day, krx_code, "d")
    return stock_data.to_string() 


path = find_dotenv() 
load_dotenv(path)
# openai.api_key = os.getenv("OPENAI_API_KEY")

model = ChatOpenAI()
prompt = hub.pull("hwchase17/openai-tools-agent")
prompt.messages[0] = SystemMessagePromptTemplate.from_template("당신은 주식 분석가입니다. 주어진 정보를 보고 주식에 대한 의견을 전달하세요.")

tools = [get_stock_price]
agent = create_openai_tools_agent(model.with_config({"tags": ["agent_llm"]}),tools, prompt)
# print (agent)

agent_executor = AgentExecutor(agent=agent, tools=tools).with_config(
    {"run_name": "Agent"}
)

input_prompt = "삼성전자(005930)의 2025년 1월 주가 분석해 주세요"
response = agent_executor.invoke({"input":input_prompt})
print('*'*100)
print('input:\n',response['input'])
print('output:\n',response['output'])