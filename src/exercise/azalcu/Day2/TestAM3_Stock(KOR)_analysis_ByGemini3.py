"""
실행방법 : Terminal에서 streamlit run "TestAM3_Stock(KOR)_analysis_ByGemini3.py" 명령을 실행하여 웹브라우져를 열어 실행해보세요.
"""

# market_analyzer_app.py

import streamlit as st
import pandas as pd
import plotly.express as px
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import io
import json
from openai import OpenAI
from pykrx import stock

# --- 페이지 기본 설정 ---
st.set_page_config(
    page_title="AI 시장 분석 리포팅 시스템",
    page_icon="🤖",
    layout="wide",
)

# --- 핵심 기능 함수들 ---

def get_data_for_market_map(codes, names):
    """pykrx를 이용해 마켓 맵에 필요한 시가총액과 등락률 정보를 가져옵니다."""
    today = pd.Timestamp.now().strftime('%Y%m%d')
    try:
        # OHLCV 데이터에 등락률이 포함되어 있습니다.
        df_all = stock.get_market_ohlcv(today)
        df_filtered = df_all.loc[[code for code in codes if code in df_all.index]].copy()

        if df_filtered.empty:
            return pd.DataFrame()

        # 종목명을 추가합니다.
        code_to_name = dict(zip(codes, names))
        df_filtered['종목명'] = df_filtered.index.map(code_to_name)

        # 시가총액 정보를 별도로 조회하여 추가합니다.
        market_cap_df = stock.get_market_cap(today)
        df_filtered['시가총액'] = df_filtered.index.map(market_cap_df['시가총액'])

        # 필요한 데이터가 없는 행은 제거합니다.
        df_filtered = df_filtered.dropna(subset=['시가총액', '등락률', '종목명'])
        
        # 등락률의 절대값을 계산하여 크기 기준으로 사용하기 위함입니다.
        df_filtered['등락률크기'] = df_filtered['등락률'].abs()

        return df_filtered

    except Exception as e:
        st.warning(f"마켓 맵 데이터 조회 중 오류가 발생했습니다: {e}")
        return pd.DataFrame()

def create_market_map(report_data, size_option):
    """Plotly를 이용해 마켓 맵 시각화를 생성합니다."""
    st.write("### 📊 마켓 맵 시각화")
    with st.spinner("종목별 시가총액 및 등락률 데이터를 조회 중입니다..."):
        stock_codes = [s['code'] for s in report_data['related_stocks']]
        stock_names = [s['name'] for s in report_data['related_stocks']]

        df = get_data_for_market_map(stock_codes, stock_names)

        if df.empty:
            st.warning("마켓 맵 데이터를 조회할 수 없어 시각화를 생성할 수 없습니다.")
            return
    
    if size_option == "시가총액":
        values_col = '시가총액'
    else: # 등락률
        values_col = '등락률크기'

    fig = px.treemap(
        df,
        path=[px.Constant("전체"), '종목명'],
        values=values_col,
        color='등락률',
        color_continuous_scale='RdBu_r', # 빨강-파랑 반전
        color_continuous_midpoint=0,
        hover_data={'등락률': ':.2f%', '시가총액': ':,'}
    )
    fig.update_layout(
        margin=dict(t=30, l=10, r=10, b=10),
        treemapcolorway = ["red", "blue"] # 색상 직접 지정 (일부 버전 호환성)
    )
    fig.data[0].textinfo = 'label+percent entry'
    st.plotly_chart(fig, use_container_width=True)

def create_network_graph(report_data):
    """pyvis를 이용해 테마-종목 간 네트워크 그래프를 생성하고 종목 간 관계를 표시합니다."""
    st.write("### 🕸️ 테마-종목 간 네트워크 그래프")
    topic = report_data.get('topic', '분석 테마')

    net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white", notebook=True, directed=False)
    
    net.add_node(topic, label=topic, color='#FF4B4B', size=30)
    
    stock_names = {stock['name'] for stock in report_data['related_stocks']}
    for stock in report_data['related_stocks']:
        net.add_node(stock['name'], label=stock['name'], color='#00C4FF', size=15)
        net.add_edge(topic, stock['name'], weight=1, color='#AAAAAA')

    relations = report_data.get('stock_relations', [])
    if isinstance(relations, list):
        for relation in relations:
            stock1 = relation.get('stock1')
            stock2 = relation.get('stock2')
            desc = relation.get('description', '관련')
            if stock1 in stock_names and stock2 in stock_names:
                net.add_edge(stock1, stock2, title=desc, weight=0.6, color='#999999')
    elif isinstance(relations, str):
        st.info(f"AI가 파악한 종목 간 관계 요약: {relations}")

    net.show_buttons(filter_=['physics'])
    
    try:
        net.save_graph("network.html")
        with open("network.html", 'r', encoding='utf-8') as f:
            html_source = f.read()
        components.html(html_source, height=770)
    except Exception as e:
        st.error(f"네트워크 그래프 생성에 실패했습니다: {e}")

def call_openai_engine(query, api_key):
    """OpenAI API를 호출하여 시장 분석 리포트를 생성합니다."""
    client = OpenAI(api_key=api_key)
    system_prompt = """
    당신은 최고의 금융 애널리스트입니다. 사용자의 요청에 따라 한국 주식 시장의 특정 테마나 산업에 대한 분석 보고서를 작성해야 합니다.
    응답은 반드시 다음의 키를 포함한 JSON 형식이어야 합니다:
    1. 'topic': 분석한 주제나 테마 (예: '2025년 7월 반도체 시장 트렌드')
    2. 'summary': 분석 결과에 대한 2~3문단의 핵심 요약.
    3. 'positive_factors': 시장이나 테마에 대한 3가지 긍정적 요인 (리스트 형태).
    4. 'negative_factors': 시장이나 테마에 대한 3가지 부정적 요인 (리스트 형태).
    5. 'related_stocks': 해당 테마와 가장 관련이 깊은 15~20개의 종목 리스트. 각 종목은 'name'과 'code' 키를 가져야 합니다 (예: [{"name": "삼성전자", "code": "005930"}]).
    6. 'stock_relations': 관련 종목들 사이의 중요한 관계 3~5개를 리스트 형태로 제공. 각 관계는 'stock1', 'stock2', 'description' 키를 가져야 합니다. (예: [{"stock1": "삼성전자", "stock2": "SK하이닉스", "description": "메모리 반도체 경쟁사"}]).
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
        summary_df = pd.DataFrame({
            '구분': ['주제 요약'] + ['긍정 요인'] * len(report_data.get('positive_factors',[])) + ['부정 요인'] * len(report_data.get('negative_factors',[])),
            '내용': [report_data.get('summary', '')] + report_data.get('positive_factors', []) + report_data.get('negative_factors', [])
        })
        summary_df.to_excel(writer, sheet_name='분석 요약', index=False)
        
        stocks_df = pd.DataFrame(report_data.get('related_stocks', []))
        stocks_df.to_excel(writer, sheet_name='관련 종목', index=False)
    
    processed_data = output.getvalue()
    return processed_data

# --- Streamlit UI 구성 ---

st.title("🤖 AI 기반 시장 분석 리포팅 시스템")
st.caption("v2.0 (고급 시각화 탑재)")

# --- 사이드바: 옵션 설정 ---
with st.sidebar:
    st.header("⚙️ 분석 옵션")
    
    openai_api_key = st.text_input("OpenAI API 키를 입력하세요", type="password", help="OpenAI 웹사이트에서 발급받은 API 키를 입력하세요.")
    
    visualization_option = st.radio(
        "시각화 옵션 선택",
        ["시각화 없음", "마켓 맵", "네트워크 그래프"],
        help="분석 결과와 함께 보여줄 그래프를 선택합니다."
    )

    size_option = st.radio(
        "마켓 맵 크기 기준",
        ["시가총액", "등락률"],
        disabled=(visualization_option != "마켓 맵"),
        help="마켓 맵에서 사각형의 크기를 결정하는 기준을 선택합니다."
    )

# --- 메인 화면: 입력 및 결과 출력 ---
user_query = st.text_area(
    "분석할 주제나 테마를 입력하세요",
    placeholder="예시) 반도체 분야 7월 트렌드\n자동차 관련주 25년 분석\n원자재 관련주 25년 하반기 전망",
    height=150
)

if st.button("분석 실행", type="primary", use_container_width=True):
    if not openai_api_key:
        st.error("사이드바에 OpenAI API 키를 먼저 입력해주세요.")
    elif not user_query:
        st.warning("분석할 주제를 입력해주세요.")
    else:
        with st.spinner("AI가 시장 데이터를 분석하고 리포트를 생성 중입니다... 잠시만 기다려주세요."):
            report_data = call_openai_engine(user_query, openai_api_key)

        if report_data:
            st.session_state.report_data = report_data
        else:
            if 'report_data' in st.session_state:
                del st.session_state.report_data
        
if 'report_data' in st.session_state:
    report_data = st.session_state.report_data
    
    st.markdown("---")
    st.header(f"📈 분석 리포트: {report_data.get('topic', 'N/A')}")
    
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

    if visualization_option == "마켓 맵":
        create_market_map(report_data, size_option)
    elif visualization_option == "네트워크 그래프":
        create_network_graph(report_data)
        
    st.markdown("---")
    st.subheader("📄 리포트 저장")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        excel_data = convert_to_excel(report_data)
        st.download_button(
            label="📥 Excel로 저장",
            data=excel_data,
            file_name=f"report_{report_data.get('topic', 'data').replace(' ', '_')}.xlsx",
            mime="application/vnd.ms-excel",
            use_container_width=True
        )
        
    with col2:
        st.download_button("📥 PDF로 저장 (구현 예정)", "준비 중", disabled=True, use_container_width=True)
    
    with col3:
        st.download_button("📥 Word로 저장 (구현 예정)", "준비 중", disabled=True, use_container_width=True)

"""
실행방법 : Terminal에서 streamlit run "TestAM3_Stock(KOR)_analysis_ByGemini3.py" 명령을 실행하여 웹브라우져를 열어 실행해보세요.
"""