
import openai
from pykrx import stock
from langchain.agents import initialize_agent, Tool
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
import os
import streamlit as st

openai.api_key = os.getenv("OPENAI_API_KEY")

# def get_stock(start_date="20250701", end_date="20250720", company_code="005930"):
#     df = stock.get_market_trading_value_by_date(start_date, end_date, company_code)
#     return df.head().to_string()
def get_stock(start_date, end_date, company_code):
    
    start_date = start_date.strip()
    end_date = end_date.strip()
    company_code = company_code.strip()
    stock_name = stock.get_market_ticker_name(company_code)
    # print(f"Analyzing stock: {stock_name} ({company_code}) from {start_date} to {end_date}")
    
    df = stock.get_market_trading_value_by_date(start_date, end_date, company_code)
    st.write(df)
    return df.head().to_string()

analyze_stock = Tool(
    name="Analyze Stock",
    func=lambda query: get_stock(*query.split(",")),
    # func=lambda query: get_stock(query),
    description="stock analyze"
)

st.title("삼성전자 주가 분석")

llm = OpenAI(temperature=0, streaming=True)

tools = [analyze_stock]
query =  "20250701, 20250720, 005930"

agent = initialize_agent(tools, llm, agent="zero-shot-react-description", verbose=True)

prompt = f"{query} 에 대한 주가를 한국어로 분석해줘."
st.write(prompt)

response = agent.run(prompt)

st.markdown("주가분석결과")
st.write(response)