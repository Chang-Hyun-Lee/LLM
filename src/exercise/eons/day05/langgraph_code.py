# filename: code_review_graph.
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import os
import openai
from typing import TypedDict

# LangGraph에서 상태 타입 명시
class CodeReviewState(TypedDict):
    code: str
    style_feedback: str
    bug_feedback: str
    opt_feedback: str
    final_code: str

openai.api_key = os.getenv("OPENAI_API_KEY")

# 💬 LLM 설정
llm = ChatOpenAI(model="gpt-4", temperature=0)

# 🧩 Node 함수 정의

def input_code_node(state):
    return state

def style_check_node(state):
    code = state["code"]
    prompt = f"""아래 파이썬 코드의 스타일을 점검해 주세요.
- PEP8 스타일 위반을 찾아 수정 제안
- 변수명, 함수명 등 네이밍 개선
- 불필요한 줄바꿈, 들여쓰기 문제 등
수정된 코드를 반환해주세요."""
    result = llm.invoke([HumanMessage(content=prompt)])
    return {**state, "style_feedback": result.content}

def bug_check_node(state):
    code = state["code"]
    prompt = f"""아래 파이썬 코드에서 버그 가능성이 있는 부분을 찾아주세요.
- 예외처리 누락
- 변수 초기화 오류
- 논리적 오류
- 경고 발생 가능성 등
문제가 되는 부분과 그 이유, 그리고 수정 제안 코드를 함께 제시해주세요."""
    result = llm.invoke([HumanMessage(content=prompt)])
    return {**state, "bug_feedback": result.content}

def optimize_check_node(state):
    code = state["code"]
    prompt = f"""아래 파이썬 코드의 성능을 개선할 수 있는 부분을 찾아주세요.
- 반복문 최적화
- 불필요한 연산 제거
- 효율적 알고리즘 제안 등
개선 사항과 함께 최적화된 코드 예시를 보여주세요."""
    result = llm.invoke([HumanMessage(content=prompt)])
    return {**state, "opt_feedback": result.content}

def merge_fix_node(state):
    code = state["code"]
    style = state.get("style_feedback", "")
    bug = state.get("bug_feedback", "")
    opt = state.get("opt_feedback", "")

    prompt = f"""다음은 한 파이썬 코드에 대해 스타일, 버그, 성능 분석을 각각 수행한 결과입니다.

원본 코드:

[스타일 피드백]
{style}

[버그 피드백]
{bug}

[성능 최적화 피드백]
{opt}

위 피드백들을 모두 반영한 최종 개선 코드를 만들어주세요. 주석 없이 코드만 출력하세요."""
    result = llm.invoke([HumanMessage(content=prompt)])
    return {**state, "final_code": result.content}

def final_output_node(state):
    print("\n💡 최종 개선된 코드:\n")
    print(state["final_code"])
    return state

# 🧱 LangGraph 구성
builder = StateGraph(state_type=dict)

builder.add_node("InputCode", RunnableLambda(input_code_node))
builder.add_node("StyleCheck", RunnableLambda(style_check_node))
builder.add_node("BugCheck", RunnableLambda(bug_check_node))
builder.add_node("OptimizeCheck", RunnableLambda(optimize_check_node))
builder.add_node("MergeFix", RunnableLambda(merge_fix_node))
builder.add_node("FinalOutput", RunnableLambda(final_output_node))

builder.set_entry_point("InputCode")

builder.add_edge("InputCode", "StyleCheck")
builder.add_edge("StyleCheck", "BugCheck")
builder.add_edge("BugCheck", "OptimizeCheck")
builder.add_edge("OptimizeCheck", "MergeFix")
builder.add_edge("MergeFix", "FinalOutput")
builder.add_edge("FinalOutput", END)

graph = builder.compile()

# 🚀 테스트 실행
if __name__ == "__main__":
    user_code = """
def add(a,b):
 return a+  b
"""
    print("📝 입력 코드:\n", user_code)
    graph.invoke({"code": user_code})
