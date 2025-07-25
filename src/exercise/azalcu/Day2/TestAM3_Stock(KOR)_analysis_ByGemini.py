#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
한국 주식 분석기 (v11.0 - 최종 코드 리뷰 및 리팩토링)
- 띄어쓰기가 포함된 종목명 인식 문제 해결
- 데이터 소스 이중화 (FinanceDataReader -> yfinance)
- 전체 코드 스타일 통일 및 가독성 향상
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import re
import json
from typing import Dict, Optional
import warnings
import traceback

warnings.filterwarnings('ignore')

# --- 필수 라이브러리 임포트 ---
try:
    import FinanceDataReader as fdr
    FDR_AVAILABLE = True
except ImportError:
    FDR_AVAILABLE = False
try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    YF_AVAILABLE = False
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
try:
    from thefuzz import fuzz
    THEFUZZ_AVAILABLE = True
except ImportError:
    THEFUZZ_AVAILABLE = False

# 한글 폰트 설정
plt.rcParams['font.family'] = ['Malgun Gothic', 'Arial Unicode MS', 'AppleGothic']
plt.rcParams['axes.unicode_minus'] = False


class KoreanStockAnalyzer:
    def __init__(self, openai_api_key: Optional[str] = None):
        self.use_ai = False
        if openai_api_key and OPENAI_AVAILABLE:
            try:
                self.client = OpenAI(api_key=openai_api_key)
                self.use_ai = True
                print("🤖 AI 기반 검색 및 리포트 모드가 활성화되었습니다!")
            except Exception as e:
                print(f"❌ OpenAI 연결 실패: {e}. AI 기능 없이 작동합니다.")
        
        self.eng_to_kor_map = {'q':'ㅂ','w':'ㅈ','e':'ㄷ','r':'ㄱ','t':'ㅅ','y':'ㅛ','u':'ㅕ','i':'ㅑ','o':'ㅐ','p':'ㅔ','a':'ㅁ','s':'ㄴ','d':'ㅇ','f':'ㄹ','g':'ㅎ','h':'ㅗ','j':'ㅓ','k':'ㅏ','l':'ㅣ','z':'ㅋ','x':'ㅌ','c':'ㅊ','v':'ㅍ','b':'ㅠ','n':'ㅜ','m':'ㅡ','Q':'ㅃ','W':'ㅉ','E':'ㄸ','R':'ㄲ','T':'ㅆ','O':'ㅒ','P':'ㅖ','sus':'년','dnjf':'월','dlf':'일'}
        self.krx_stocks = self._load_stock_list()

    def _load_stock_list(self) -> Optional[pd.DataFrame]:
        if not FDR_AVAILABLE: return None
        try:
            print("\n📚 한국거래소(KRX) 전체 종목 리스트를 불러오는 중입니다...")
            krx = fdr.StockListing('KRX')
            krx['Name'] = krx['Name'].str.strip()
            print(f"✅ 총 {len(krx)}개의 종목 정보를 성공적으로 불러왔습니다.")
            return krx
        except Exception as e:
            print(f"⚠️ 전체 종목 리스트 로딩 실패: {e}")
        return None

    def _normalize_keyboard_typos(self, text: str) -> str:
        for eng, kor in [('sus', '년'), ('dnjf', '월'), ('dlf', '일')]:
            text = text.replace(eng, kor)
        return "".join([self.eng_to_kor_map.get(char, char) for char in text])

    def _ask_openai_for_stock_name(self, text: str) -> Optional[str]:
        if not self.use_ai: return None
        print("...🤖 AI에게 정확한 종목명을 물어보는 중입니다.")
        system_prompt = "당신은 한국 주식 시장 전문가입니다. 사용자의 입력에 오타나 불분명한 표현이 있더라도, 당신의 지식을 이용해 실제 한국 주식 시장에 상장된 가장 가능성 높은 단일 종목명으로 '수정'하고 '추론'해주세요. 다른 설명 없이 JSON 형식으로만 응답해야 합니다. 예: {\"corrected_name\": \"두산로보틱스\"}"
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": f"다음 사용자 입력에서 종목명을 추론해줘: '{text}'"}],
                response_format={"type": "json_object"}, temperature=0.1)
            result = json.loads(response.choices[0].message.content)
            corrected_name = result.get("corrected_name")
            if corrected_name:
                print(f"🤖 AI의 답변: '{corrected_name}'")
                return corrected_name
        except Exception as e:
            print(f"❌ AI 종목명 추론 실패: {e}")
        return None

    def _find_similar_stocks_local(self, text: str, limit: int = 5) -> Dict:
        if not THEFUZZ_AVAILABLE or self.krx_stocks is None: return {'error': '종목을 찾을 수 없습니다.'}
        print("...로컬 유사도 검색을 수행합니다.")
        scores = self.krx_stocks['Name'].apply(lambda name: fuzz.WRatio(text, name))
        similar_stocks = self.krx_stocks.assign(score=scores).nlargest(limit, 'score')
        similar_stocks = similar_stocks[similar_stocks['score'] >= 80]
        if similar_stocks.empty: return {'error': '유사한 종목도 찾을 수 없습니다.'}
        return {'suggestions': similar_stocks[['Name', 'Code']].to_dict('records')}

    def extract_stock_info(self, text: str) -> Optional[Dict]:
        """AI를 우선으로 사용하여 텍스트에서 종목 정보를 추출합니다."""
        # 1. 종목 코드로 검색
        code_match = re.search(r'\b(\d{6})\b', text)
        if code_match:
            code = code_match.group(1)
            stock_match = self.krx_stocks[self.krx_stocks['Code'] == code] if self.krx_stocks is not None else pd.DataFrame()
            name = stock_match.iloc[0]['Name'] if not stock_match.empty else f"종목 {code}"
            return {'name': name, 'code': code}
        
        # ✨ [개선] 띄어쓰기 종목명 인식을 위해, 불필요한 단어를 먼저 제거
        stop_words = ['주가', '차트', '그래프', '분석', '알려줘', '어때']
        search_term = text
        for word in stop_words:
            search_term = search_term.replace(word, '')
        # 날짜 관련 표현도 제거
        search_term = re.sub(r'(\d{2,4}년|\d{1,2}월|\d{1,2}일)', '', search_term).strip()

        # 2. 정제된 이름으로 정확히 일치하는지 검색
        if self.krx_stocks is not None:
            exact_match = self.krx_stocks[self.krx_stocks['Name'] == search_term]
            if not exact_match.empty:
                return {'name': exact_match.iloc[0]['Name'], 'code': exact_match.iloc[0]['Code']}

        # 3. AI에게 추론 요청
        corrected_name = self._ask_openai_for_stock_name(text) # AI에게는 원본 텍스트를 제공하여 문맥 파악
        if corrected_name and self.krx_stocks is not None:
            ai_match = self.krx_stocks[self.krx_stocks['Name'] == corrected_name]
            if not ai_match.empty:
                return {'name': ai_match.iloc[0]['Name'], 'code': ai_match.iloc[0]['Code']}

        # 4. 모든 방법 실패 시, 로컬 유사도 검색
        return self._find_similar_stocks_local(search_term)

    def extract_date_info(self, text: str) -> Dict[str, str]:
        """텍스트에서 날짜 정보를 추출합니다."""
        today = datetime.now()
        patterns = [r'(\d{2,4})년\s*(\d{1,2})월', r'(\d{4})-(\d{1,2})', r'(\d{4})\.(\d{1,2})', r'(\d{4})/(\d{1,2})']
        dates_found = []
        for p in patterns:
            for match in re.findall(p, text):
                year_str, month_str = match
                year = int(year_str)
                if year < 100: year += 2000
                dates_found.append(datetime(year, int(month_str), 1))

        start_date, end_date = None, None
        if '부터' in text and '까지' in text and len(dates_found) >= 2:
            start_date, end_date = min(dates_found), max(dates_found)
        elif dates_found:
            start_date = end_date = dates_found[0]

        if start_date is None: start_date = today - timedelta(days=365)
        if end_date is None: end_date = today

        if end_date.month == 12:
            end_date = datetime(end_date.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(end_date.year, end_date.month + 1, 1) - timedelta(days=1)
        
        return {'start_date': start_date.strftime('%Y-%m-%d'), 'end_date': end_date.strftime('%Y-%m-%d')}

    def get_stock_data(self, stock_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """주가 데이터를 수집합니다. (yfinance 예비 소스 추가)"""
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        if start_datetime > datetime.now():
            print(f"⚠️ 시작일({start_date})이 오늘보다 미래입니다. 조회할 데이터가 없습니다.")
            return None

        print(f"📈 주식 데이터 수집 중: {stock_code} ({start_date} ~ {end_date})")
        # 1. FinanceDataReader 시도
        if FDR_AVAILABLE:
            try:
                data = fdr.DataReader(stock_code, start_date, end_date)
                if not data.empty:
                    print(f"✅ FinanceDataReader로 {len(data)}일 데이터 수집 완료")
                    return data
            except Exception as e:
                print(f"⚠️ FinanceDataReader 실패: {e}")
        
        # ✨ [개선] 2. yfinance 시도 (예비)
        if YF_AVAILABLE:
            print("... 예비 데이터 소스(yfinance)로 재시도합니다.")
            try:
                data = yf.download(f"{stock_code}.KS", start=start_date, end=end_date, progress=False)
                if not data.empty:
                    print(f"✅ yfinance로 {len(data)}일 데이터 수집 완료")
                    return data
            except Exception as e:
                print(f"⚠️ yfinance 실패: {e}")

        print("❌ 모든 데이터 소스에서 데이터 수집에 실패했습니다.")
        return None

    def calculate_basic_stats(self, data: pd.DataFrame) -> Dict:
        if data.empty: return {}
        return {'period_start': data.index[0].strftime('%Y-%m-%d'), 'period_end': data.index[-1].strftime('%Y-%m-%d'), 'start_price': int(data['Close'].iloc[0]), 'end_price': int(data['Close'].iloc[-1]), 'highest_price': int(data['High'].max()), 'lowest_price': int(data['Low'].min()), 'total_return_pct': round((data['Close'].iloc[-1] / data['Close'].iloc[0] - 1) * 100, 2), 'volatility': round(data['Close'].pct_change().std() * np.sqrt(252) * 100, 2)}

    def create_price_chart(self, data: pd.DataFrame, stock_name: str, stock_code: str):
        """주가 및 거래량 차트를 생성하고 보여줍니다."""
        if data.empty:
            print("데이터가 없어 차트를 생성할 수 없습니다.")
            return

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[3, 1], sharex=True)
        
        ax1.plot(data.index, data['Close'], color='#1f77b4', label='종가')
        ax1.set_title(f'{stock_name}({stock_code}) 주가 차트', fontsize=16, weight='bold')
        ax1.set_ylabel('주가 (원)')
        ax1.grid(True, linestyle='--', alpha=0.5)
        ax1.legend()
        
        ax2.bar(data.index, data['Volume'], color='orange', alpha=0.7)
        ax2.set_ylabel('거래량')
        
        fig.autofmt_xdate()
        plt.tight_layout()
        plt.show(block=False)

    def basic_generate_report(self, stats: Dict, stock_name: str) -> str:
        return (f"## 📊 {stock_name} 주가 분석 리포트 (기본)\n\n"
            f"### 🎯 핵심 요약\n"
            f"- **분석 기간**: {stats.get('period_start', 'N/A')} ~ {stats.get('period_end', 'N/A')}\n"
            f"- **가격 변화**: {stats.get('start_price', 0):,}원 → {stats.get('end_price', 0):,}원\n"
            f"- **기간 수익률**: **{stats.get('total_return_pct', 0)}%**\n"
            f"- **연간 변동성**: {stats.get('volatility', 0)}%\n\n"
            f"**주의**: 본 분석은 정보 제공 목적으로, 투자 권유가 아닙니다.\n")

    def ai_generate_report(self, stats: Dict, stock_name: str, user_request: str) -> str:
        if not self.use_ai: return self.basic_generate_report(stats, stock_name)
        print("🤖 AI가 분석 리포트를 생성 중입니다...")
        prompt = f"당신은 전문 주식 애널리스트입니다. 다음 데이터를 바탕으로 '{stock_name}'에 대한 주가 분석 리포트를 작성해주세요. 친절하고 이해하기 쉬운 말투를 사용하고, 핵심 요약, 상세 분석, 투자 관점 순서로 구성해주세요. 마지막에는 투자 권유가 아님을 명시하세요.\n\n- 분석 데이터: {json.dumps(stats, ensure_ascii=False, indent=2)}\n- 사용자의 원본 요청: \"{user_request}\""
        try:
            response = self.client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}], temperature=0.5)
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ AI 리포트 생성 실패: {e}")
            return self.basic_generate_report(stats, stock_name)

    def _execute_analysis(self, request_info: Dict):
        """확정된 종목 정보로 실제 분석을 수행하는 내부 함수"""
        try:
            code = request_info['code']
            name = request_info['name']
            start = request_info['start_date']
            end = request_info['end_date']
            original_req = request_info['original_request']

            stock_data = self.get_stock_data(code, start, end)
            if stock_data is None: return

            basic_stats = self.calculate_basic_stats(stock_data)
            final_report = self.ai_generate_report(basic_stats, name, original_req) if self.use_ai else self.basic_generate_report(basic_stats, name)
            print(f"\n{final_report}")

            if '차트' in original_req or '그래프' in original_req:
                self.create_price_chart(stock_data, name, code)

        except Exception:
            print(f"\n❌ 분석 실행 중 예상치 못한 오류가 발생했습니다:")
            traceback.print_exc()

    def run_analysis_flow(self, user_request: str):
        """사용자 요청부터 분석까지의 전체 흐름을 관리"""
        normalized_request = self._normalize_keyboard_typos(user_request)
        print(f"🔍 '{user_request}' -> '{normalized_request}' (으)로 변환 후 분석을 시작합니다.")
        
        stock_info = self.extract_stock_info(normalized_request)

        if not stock_info or 'error' in stock_info:
            print(f"❌ 분석 중단: {stock_info.get('error', '알 수 없는 오류')}"); return

        if 'suggestions' in stock_info:
            print("\n🤔 혹시 이 종목을 찾으시나요? 번호를 선택해주세요. (취소: 0)")
            for i, item in enumerate(stock_info['suggestions'], 1):
                print(f"  {i}. {item['Name']} ({item['Code']})")
            while True:
                try:
                    choice = int(input("선택 (번호): ").strip())
                    if 0 <= choice <= len(stock_info['suggestions']): break
                    else: print("⚠️ 잘못된 번호입니다.")
                except ValueError: print("⚠️ 숫자로 입력해주세요.")
            if choice == 0: print("분석을 취소했습니다."); return
            stock_info = {'name': stock_info['suggestions'][choice - 1]['Name'], 'code': stock_info['suggestions'][choice - 1]['Code']}

        date_info = self.extract_date_info(normalized_request)
        request_info = stock_info.copy()
        request_info.update(date_info)
        request_info['original_request'] = user_request
        print(f"📊 분석 대상 확정: {request_info['name']}({request_info['code']})")
        
        self._execute_analysis(request_info)

    def run_interactive_mode(self):
        """대화형 모드 실행"""
        print("\n" + "="*50 + "\n📈 **한국 주식 분석기 (v11.0 - 최종 리팩토링)**\n" + "="*50)
        print("어떤 종목이든, 어떤 오타든 분석해 드립니다.")
        print("📝 사용 예시: 'SK 이노베이션 1년 차트', '삼성전자 25sus 7dnjf'")
        
        while True:
            try:
                user_input = input("\n🤔 분석할 내용을 말씀해주세요 (종료: q 또는 quit): ").strip()
                if user_input.lower() in ['q', 'quit', 'exit', '종료']:
                    print("\n👋 분석을 종료합니다."); break
                if user_input: self.run_analysis_flow(user_input)
            except Exception:
                print(f"\n❌ 프로그램 실행 중 예상치 못한 오류가 발생했습니다:")
                traceback.print_exc()

def main():
    """메인 실행 함수"""
    print("🚀 한국 주식 분석기를 시작합니다!")
    libs = {'FinanceDataReader': FDR_AVAILABLE, 'yfinance': YF_AVAILABLE, 'OpenAI': OPENAI_AVAILABLE, 'thefuzz': THEFUZZ_AVAILABLE}
    missing_libs = [name for name, available in libs.items() if not available]
    if missing_libs:
        print(f"⚠️ 필수 라이브러리가 설치되지 않았습니다: {', '.join(missing_libs)}")
        return

    api_key = None
    use_ai_input = input("🤖 AI 기반 검색/리포트를 사용하시겠습니까? (y/n, 기본값 n): ").lower()
    if use_ai_input == 'y':
        api_key = input("🔑 OpenAI API 키를 입력하세요: ").strip()
        if not api_key: print("⚠️ API 키가 입력되지 않아 AI 기능 없이 작동합니다.")
    
    analyzer = KoreanStockAnalyzer(openai_api_key=api_key)
    analyzer.run_interactive_mode()

if __name__ == "__main__":
    main()