##실습 #1: Streamlit과 LangChain agent를 사용하여 예전에 만들었던 특정 종목의 주가를 분석해주는 어플리케이션을 작성하시오.
##실습 #2: Streamlit과 LangChain agent를 사용하여 예전에 만들었던 레스토랑을 찾아서 검색해주는 어플리케이션을 작성하시오.
##실습 #3: Streamlit과 LangChain agent를 사용하여 예전에 만들었던 캠핑장을 추천해주는 어플리케이션을 작성하시오.

# 실습#1 미완성.
from pykrx import stock
from pykrx import bond

print("---- 삼성전자 주가 데이터 가져오기")
def get_stock_price(stDay, enDay, code):
    name = stock.get_market_ohlcv(stDay, enDay, code)
    print(name)
    return name.to_csv()

from langchain.chat_models import ChatOpenAI
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

from langchain.agents import initialize_agent, Tool
get_stock_price_tool = Tool(
    name="get_stock_price_tool",
    func= lambda query:get_stock_price(*map(str, query.split())),
    description="시작일, 끝일, 주식 코드 입력하이소"
)

tools = [get_stock_price_tool]
print(tools)


from langchain.agents import create_openai_functions_agent
agent = initialize_agent(llm, tools, agent="zero-shot-react-description", verbose=True)

queryText = "20240101, 20241231, 005930"
respones = agent.run(queryText)

print (respones)