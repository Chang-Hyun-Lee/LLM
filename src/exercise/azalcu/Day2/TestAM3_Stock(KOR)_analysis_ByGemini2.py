# app.py

import streamlit as st
import pandas as pd
import plotly.express as px
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import io

from openai import OpenAI
import json
from pykrx import stock

# --- 페이지 기본 설정 ---
st.set_page_config(
    page_title="AI 시장 분석 리포팅 시스템",
    page_icon="🤖",
    layout="wide",
)

# --- 핵심 기능 함수들 ---

def get_data_for_treemap(codes, names):
    """[수정됨] pykrx를 이용해 트리맵에 필요한 시가총액과 등락률 정보를 한번에 가져옵니다."""
    today = pd.Timestamp.now().strftime('%Y%m%d')
    try:
        # OHLCV 데이터에 시가총액과 등락률이 모두 포함되어 있습니다.
        df_all = stock.get_market_ohlcv(today)
        
        # 필요한 종목만 필터링합니다.
        df_filtered = df_all[df_all.index.isin(codes)].copy()
        
        if df_filtered.empty:
            return pd.DataFrame()

        # 종목명을 추가합니다.
        code_to_name = dict(zip(codes, names))
        df_filtered['종목명'] = df_filtered.index.map(code_to_name)
        
        return df_filtered
        
    except Exception as e:
        st.warning(f"트리맵 데이터 조회 중 오류가 발생했습니다: {e}")
        return pd.DataFrame()

def create_treemap(report_data):
    """[수정됨] Plotly를 이용해 트리맵을 생성합니다."""
    st.write("### 📊 종목별 트리맵 시각화")
    with st.spinner("종목별 시가총액 및 등락률 데이터를 조회 중입니다..."):
        stock_codes = [s['code'] for s in report_data['related_stocks']]
        stock_names = [s['name'] for s in report_data['related_stocks']]
        
        # 수정된 함수를 호출합니다.
        df = get_data_for_treemap(stock_codes, stock_names)
        
        if df.empty:
            st.warning("시가총액 정보를 조회할 수 없어 트리맵을 생성할 수 없습니다.")
            return

    # 이제 df에는 '시가총액' 컬럼이 확실하게 존재합니다.
    fig = px.treemap(
        df,
        path=[px.Constant("전체"), '종목명'],
        values='시가총액',
        color='등락률',
        color_continuous_scale='RdBu',
        color_continuous_midpoint=0,
        hover_data={'등락률': ':.2f%'}
    )
    fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))
    st.plotly_chart(fig, use_container_width=True)


def create_network_graph(report_data):
    """pyvis를 이용해 네트워크 그래프를 생성합니다."""
    st.write("### 🕸️ 테마-종목 간 네트워크 그래프")
    topic = report_data.get('topic', '분석 테마')
    
    net = Network(height="600px", width="100%", bgcolor="#222222", font_color="white", notebook=True, directed=True)
    
    # 중심 노드 (테마) 추가
    net.add_node(topic, label=topic, color='#FF4B4B', size=30)
    
    # 종목 노드 추가
    for stock in report_data['related_stocks']:
        net.add_node(stock['name'], label=stock['name'], color='#00C4FF', size=15)
        net.add_edge(topic, stock['name'], weight=0.8)

    net.show_buttons(filter_=['physics'])
    
    try:
        net.save_graph("network.html")
        with open("network.html", 'r', encoding='utf-8') as f:
            html_source = f.read()
        components.html(html_source, height=620)
    except Exception as e:
        st.error(f"네트워크 그래프 생성에 실패했습니다: {e}")

def call_openai_engine(query, api_key):
    """OpenAI API를 호출하여 시장 분석 리포트를 생성합니다."""
    client = OpenAI(api_key=api_key)
    system_prompt = """
    당신은 최고의 금융 애널리스트입니다. 사용자의 요청에 따라 한국 주식 시장의 특정 테마나 산업에 대한 분석 보고서를 작성해야 합니다.
    응답은 반드시 다음의 키를 포함한 JSON 형식이어야 합니다:
    1. 'topic': 분석한 주제나 테마 (예: '2025년 7월 반도체 시장 트렌드')
    2. 'summary': 분석 결과에 대한 1~2문단의 핵심 요약.
    3. 'positive_factors': 시장이나 테마에 대한 3가지 긍정적 요인 (리스트 형태).
    4. 'negative_factors': 시장이나 테마에 대한 3가지 부정적 요인 (리스트 형태).
    5. 'related_stocks': 해당 테마와 가장 관련이 깊은 5~10개의 종목 리스트. 각 종목은 'name'과 'code' 키를 가져야 합니다 (예: [{"name": "삼성전자", "code": "005930"}]).
    모든 텍스트는 한국어로 작성해주세요.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            response_format={"type": "json_object"}
        )
        report_data = json.loads(response.choices[0].message.content)
        return report_data
    except Exception as e:
        st.error(f"OpenAI API 호출 중 오류가 발생했습니다: {e}")
        return None

def convert_to_excel(report_data):
    """분석 결과를 엑셀 파일로 변환합니다."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # 요약 및 요인 시트
        summary_df = pd.DataFrame({
            '구분': ['주제 요약'] + ['긍정 요인'] * 3 + ['부정 요인'] * 3,
            '내용': [report_data['summary']] + report_data['positive_factors'] + report_data['negative_factors']
        })
        summary_df.to_excel(writer, sheet_name='분석 요약', index=False)
        
        # 관련 종목 시트
        stocks_df = pd.DataFrame(report_data['related_stocks'])
        stocks_df.to_excel(writer, sheet_name='관련 종목', index=False)
    
    processed_data = output.getvalue()
    return processed_data

# --- Streamlit UI 구성 ---

st.title("🤖 AI 기반 시장 분석 리포팅 시스템")
st.caption("v1.0 Prototype")

# --- 사이드바: 옵션 설정 ---
with st.sidebar:
    st.header("⚙️ 분석 옵션")
    
    openai_api_key = st.text_input("OpenAI API 키를 입력하세요", type="password")
    
    visualization_option = st.radio(
        "시각화 옵션 선택",
        ["시각화 없음", "트리맵 (종목 현황)", "네트워크 그래프 (테마 관계)"],
        help="분석 결과와 함께 보여줄 그래프를 선택합니다."
    )

# --- 메인 화면: 입력 및 결과 출력 ---
user_query = st.text_area(
    "분석할 주제나 테마를 입력하세요",
    placeholder="예시) 반도체 분야 7월 트렌드\n자동차 관련주 25년 분석\n원자재 관련주 25년 하반기 전망",
    height=150
)

if st.button("분석 실행", type="primary"):
    if not openai_api_key:
        st.error("사이드바에 OpenAI API 키를 먼저 입력해주세요.")
    elif not user_query:
        st.warning("분석할 주제를 입력해주세요.")
    else:
        with st.spinner("AI가 시장 데이터를 분석하고 리포트를 생성 중입니다... 잠시만 기다려주세요."):
            report_data = call_openai_engine(user_query, openai_api_key)

        if report_data:
            st.session_state.report_data = report_data # 나중에 사용하기 위해 세션에 저장
        
if 'report_data' in st.session_state:
    report_data = st.session_state.report_data
    
    st.markdown("---")
    st.header(f"📈 분석 리포트: {report_data.get('topic', 'N/A')}")
    
    # 1. 텍스트 분석 결과 출력
    st.subheader("📝 핵심 요약")
    st.write(report_data.get('summary', ''))
    
    col1, col2 = st.columns(2)
    with col1:
        st.success("👍 긍정적 요인")
        for factor in report_data.get('positive_factors', []):
            st.markdown(f"- {factor}")
            
    with col2:
        st.error("👎 부정적 요인")
        for factor in report_data.get('negative_factors', []):
            st.markdown(f"- {factor}")
            
    st.subheader("🔗 관련 주요 종목")
    st.dataframe(pd.DataFrame(report_data.get('related_stocks', [])), use_container_width=True)

    # 2. 시각화 옵션에 따라 그래프 출력
    if visualization_option == "트리맵 (종목 현황)":
        create_treemap(report_data)
    elif visualization_option == "네트워크 그래프 (테마 관계)":
        create_network_graph(report_data)
        
    # 3. 파일 저장 버튼
    st.markdown("---")
    st.subheader("📄 리포트 저장")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        excel_data = convert_to_excel(report_data)
        st.download_button(
            label="📥 Excel로 저장",
            data=excel_data,
            file_name=f"report_{report_data.get('topic', 'data')}.xlsx",
            mime="application/vnd.ms-excel"
        )
        
    with col2:
        st.download_button("📥 PDF로 저장 (구현 예정)", "준비 중", disabled=True)
    
    with col3:
        st.download_button("📥 Word로 저장 (구현 예정)", "준비 중", disabled=True)
