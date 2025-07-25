# streamlit_app.py
# -------------------------------------------------
#  Master Schedule Docs – Streamlit Single‑Page App
# -------------------------------------------------
import os
import json
import time
import requests
import pandas as pd
import streamlit as st
from typing import Dict, List, Optional
from datetime import datetime, timedelta

# ---------- 1) 기본 설정 ----------------------------------------------------
st.set_page_config(
    page_title="생산 스케줄 API 문서",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- 2) 개선된 스타일 ----------------------------------------------------
st.markdown("""
<style>
/* 사이드바 스타일링 */
.css-1d391kg {
    padding-top: 2rem;
}

/* 네비게이션 메뉴 스타일 */
.nav-link {
    padding: 0.5rem 1rem;
    color: #1A1A1A;
    text-decoration: none;
    border-radius: 4px;
    margin: 0.2rem 0;
    transition: all 0.2s;
}

.nav-link:hover {
    background-color: #F0F2F6;
}

.nav-link.active {
    background-color: #E6E9EF;
    font-weight: bold;
}

/* 코드 블록 스타일링 */
.codehilite {
    background: #F6F8FA;
    border: 1px solid #E1E4E8;
    border-radius: 6px;
    padding: 1rem;
    position: relative;
}

/* 메서드 뱃지 */
.method {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
    font-weight: bold;
    font-size: 0.8rem;
}

.get { background: #61AFFE; color: white; }
.post { background: #49CC90; color: white; }
.put { background: #FCA130; color: white; }
.delete { background: #F93E3E; color: white; }

/* 검색창 스타일링 */
.search-container {
    padding: 1rem;
    border-bottom: 1px solid #E1E4E8;
}
</style>
""", unsafe_allow_html=True)

# ---------- 3) 개선된 사이드바 ----------------------------------------------------
# 페이지 상태 초기화
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'overview'

with st.sidebar:
    st.title("📚 생산 스케줄 API")
    
    # 검색 기능
    st.text_input("문서 검색...", key="docs_search", placeholder="검색어를 입력하세요...")
    
    st.markdown("---")

    # 계층적 네비게이션 메뉴
    MENU_STRUCTURE = {
        "시작하기": {
            "소개": "overview",
            "빠른 시작": "quickstart",
            "인증": "authentication"
        },
        "API 레퍼런스": {
            "API 개요": "api_spec",
            "스케줄 조회": "schedules",
            "스냅샷": "snapshots",
            "변경 이력": "changes"
        },
        "가이드": {
            "모범 사례": "best_practices",
            "에러 처리": "error_handling",
            "성능 최적화": "optimization"
        },
        "대시보드": {
            "스케줄 조회": "dashboard",
            "모니터링": "monitoring"
        },
        "지원": {
            "문의하기": "support",
            "FAQ": "faq"
        }
    }

    # 메뉴 렌더링
    for category, items in MENU_STRUCTURE.items():
        with st.expander(category, expanded=True):
            for item_name, item_key in items.items():
                if st.button(
                    item_name, 
                    key=f"nav_{item_key}", 
                    use_container_width=True,
                    type="secondary" if st.session_state.current_page != item_key else "primary"
                ):
                    st.session_state.current_page = item_key
                    st.rerun()

    st.markdown("---")
    
    # 버전 정보
    version = "1.0.0"
    last_updated = datetime.now().strftime("%Y-%m-%d")
    st.markdown(f"""
        **버전:** {version}  
        **최근 업데이트:** {last_updated}  
        **상태:** 🟢 정상 운영중
    """)

# ---------- 3) API CLIENT ----------------------------------------------------
class MasterScheduleClient:
    def __init__(self):
        self.base_url = "https://intranet.example.com/api/v1/master-schedule"
        self.token = os.getenv("MSCHED_TOKEN", "demo-token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
    @st.cache_data(ttl=600)
    def get_latest_snapshot(self) -> Optional[pd.DataFrame]:
        try:
            with st.spinner("Fetching latest schedule data..."):
                meta = requests.get(
                    f"{self.base_url}/snapshot/latest",
                    headers=self.headers,
                    timeout=10
                ).json()
                
                data = requests.get(
                    f"{self.base_url}/snapshot/{meta['id']}", 
                    headers=self.headers,
                    timeout=30
                ).json()
                
                return pd.DataFrame(data)
        except requests.RequestException as e:
            st.error(f"API Error: {str(e)}")
            return None
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            return None

# ---------- 4) PAGE RENDERERS -----------------------------------------------
def render_overview() -> None:
    st.header("Master Schedule API Overview")
    
    # Key features section
    st.subheader("🎯 Key Features")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        - Real-time schedule access
        - Role-based authentication
        - Delta sync support
        - Bulk data export
        """)
    
    with col2:
        st.markdown("""
        - Project/Block filtering
        - Historical snapshots
        - Rate limiting
        - API versioning
        """)
    
    # Quick stats
    st.subheader("📊 API Stats")
    stat1, stat2, stat3, stat4 = st.columns(4)
    stat1.metric("Uptime", "99.9%")
    stat2.metric("Avg Response", "280ms")
    stat3.metric("Daily Users", "1.2K")
    stat4.metric("API Calls/Day", "250K")

def render_api_spec() -> None:
    st.header("API Reference")
    
    # Authentication section
    st.subheader("🔐 Authentication")
    with st.expander("How to get your API token"):
        st.code("""
curl -X POST https://intranet.example.com/auth/token \
     -H "Content-Type: application/json" \
     -d '{"username": "<USER>", "password": "<PASS>"}' 
""", language="bash")
    
    # Endpoints
    st.subheader("📡 Endpoints")
    endpoints = [
        {
            "method": "GET",
            "path": "/snapshots",
            "desc": "List all schedule snapshots",
            "auth": "Required"
        },
        {
            "method": "GET", 
            "path": "/snapshot/{id}",
            "desc": "Get specific snapshot",
            "auth": "Required"
        },
        {
            "method": "GET",
            "path": "/snapshot/latest",
            "desc": "Get latest schedule",
            "auth": "Required" 
        },
        {
            "method": "GET",
            "path": "/delta?since={ts}",
            "desc": "Get changes since timestamp",
            "auth": "Required"
        }
    ]
    
    st.table(pd.DataFrame(endpoints))

def render_quickstart() -> None:
    st.header("Quick Start Guide")
    
    tabs = st.tabs(["Python", "curl", "JavaScript"])
    
    with tabs[0]:
        st.markdown("""
        ### Python SDK 사용하기
        
        1. 환경 설정
        """)
        
        with st.expander("Requirements", expanded=True):
            st.code("""
pip install requests pandas
export MSCHED_TOKEN='your-api-token'
""", language="bash")
            
        st.markdown("2. 기본 사용법")
        st.code("""
import os
import requests
import pandas as pd

class MasterScheduleAPI:
    def __init__(self, token=None):
        self.token = token or os.getenv('MSCHED_TOKEN')
        self.base_url = 'https://intranet.example.com/api/v1'
        self.headers = {'Authorization': f'Bearer {self.token}'}
    
    def get_latest_schedule(self):
        response = requests.get(
            f'{self.base_url}/snapshot/latest',
            headers=self.headers
        )
        return pd.DataFrame(response.json())

# 사용 예시
api = MasterScheduleAPI()
schedule_df = api.get_latest_schedule()
print(schedule_df.head())
""", language="python")

    with tabs[1]:
        st.markdown("""
        ### cURL로 API 사용하기
        
        1. 인증 토큰 받기
        """)
        
        st.code("""
curl -X POST https://intranet.example.com/auth/token \
     -H "Content-Type: application/json" \
     -d '{"username": "<USER>", "password": "<PASS>"}' 
""", language="bash")
        
        st.markdown("2. 최신 스케줄 가져오기")
        st.code("""
curl -X GET https://intranet.example.com/api/v1/master-schedule/snapshot/latest \
     -H "Authorization: Bearer <YOUR_TOKEN>"
""", language="bash")
    
    with tabs[2]:
        st.markdown("""
        ### JavaScript로 API 사용하기
        
        1. 인증 토큰 받기
        """)
        
        st.code("""
fetch('https://intranet.example.com/auth/token', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        username: '<USER>',
        password: '<PASS>'
    })
})
.then(response => response.json())
.then(data => console.log('Token:', data.token))
.catch(error => console.error('Error:', error));
""", language="javascript")
        
        st.markdown("2. 최신 스케줄 가져오기")
        st.code("""
fetch('https://intranet.example.com/api/v1/master-schedule/snapshot/latest', {
    method: 'GET',
    headers: {
        'Authorization': 'Bearer <YOUR_TOKEN>',
    }
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));
""", language="javascript")

def render_dashboard() -> None:
    st.header("Interactive Schedule Explorer")
    
    # Use client instance instead of undefined function
    df = client.get_latest_snapshot()
    if df is None or df.empty:
        st.warning("스케줄 데이터를 불러올 수 없습니다.")
        return

    # Add tabs for different views
    tab1, tab2 = st.tabs(["📊 Schedule View", "📈 Analytics"])
    
    with tab1:
        # Filters
        with st.expander("🔍 Filters", expanded=True):
            cols = ["project", "block", "department"]
            filters = {}
            cols_container = st.columns(len(cols))
            
            for idx, col in enumerate(cols):
                with cols_container[idx]:
                    options = sorted(df[col].dropna().unique())
                    filters[col] = st.selectbox(
                        f"Select {col}",
                        options=['All'] + list(options)
                    )

        # Apply filters
        filtered_df = df.copy()
        for col, value in filters.items():
            if value != 'All':
                filtered_df = filtered_df[filtered_df[col] == value]

        # Display data with pagination
        rows_per_page = st.select_slider("Rows per page", options=[10, 25, 50, 100])
        start_idx = st.number_input("Page", min_value=1, value=1) - 1
        
        start = start_idx * rows_per_page
        end = start + rows_per_page
        
        st.dataframe(
            filtered_df.iloc[start:end],
            use_container_width=True
        )

    with tab2:
        st.info("Analytics features coming soon!")

def render_support() -> None:
    st.header("Need Help ❓")
    st.markdown(
        """
        * Dept. : `생산DT센터`  
        * Email : **j-ho.choi@samsung.com**  
        * Office hours : Tue & Thu 13:00‑16:00
        """
    )


# ---------- 5) MAIN ROUTER -------------------------------------------------
client = MasterScheduleClient()

# 현재 페이지에 따라 렌더링
if st.session_state.current_page == "overview":
    render_overview()
elif st.session_state.current_page == "api_spec":
    render_api_spec()
elif st.session_state.current_page == "quickstart":
    render_quickstart()
elif st.session_state.current_page == "dashboard":
    render_dashboard()
elif st.session_state.current_page == "support":
    render_support()
else:
    st.info("🚧 해당 페이지는 준비 중입니다.")
