#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
한국 주식 분석기
- Function/Tool 기반 설계
- 종목코드, 시작날짜, 종료날짜 파라미터
- 다양한 분석 기능 제공
- OpenAI API 연동 가능
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import re
import json
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# 한국 주식 데이터 라이브러리
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

# 한글 폰트 설정
plt.rcParams['font.family'] = ['Malgun Gothic', 'Arial Unicode MS', 'AppleGothic']
plt.rcParams['axes.unicode_minus'] = False

class KoreanStockAnalyzer:
    def __init__(self, openai_api_key: Optional[str] = None):
        # OpenAI 설정
        if openai_api_key and OPENAI_AVAILABLE:
            try:
                self.client = OpenAI(api_key=openai_api_key)
                self.use_ai = True
                print("🤖 AI 분석 모드 활성화!")
            except Exception as e:
                print(f"❌ OpenAI 연결 실패: {e}")
                self.use_ai = False
        else:
            self.use_ai = False
        
        # 주요 종목 코드 사전
        self.stock_codes = {
            '삼성전자': '005930',
            'LG전자': '066570',
            'SK하이닉스': '000660',
            'NAVER': '035420',
            '카카오': '035720',
            '현대차': '005380',
            'LG화학': '051910',
            '셀트리온': '068270',
            '한국전력': '015760',
            'KB금융': '105560',
            '신한지주': '055550',
            'POSCO홀딩스': '005490',
            '에이피알': '278470',
            'APR': '278470'
        }
        
        # 데이터 소스 우선순위
        self.data_sources = []
        if FDR_AVAILABLE:
            self.data_sources.append('FDR')
        if YF_AVAILABLE:
            self.data_sources.append('YF')
        
        if not self.data_sources:
            print("❌ 주식 데이터 라이브러리가 설치되지 않았습니다.")
            print("🔧 설치: pip install FinanceDataReader yfinance")
    
    def parse_user_request(self, user_input: str) -> Dict:
        """사용자 입력을 파싱하여 종목, 날짜 정보 추출"""
        print(f"🔍 사용자 요청 분석: '{user_input}'")
        
        # 종목명/코드 추출
        stock_info = self.extract_stock_info(user_input)
        
        # 날짜 정보 추출
        date_info = self.extract_date_info(user_input)
        
        # 분석 타입 추출
        analysis_type = self.extract_analysis_type(user_input)
        
        result = {
            'stock_name': stock_info['name'],
            'stock_code': stock_info['code'],
            'start_date': date_info['start'],
            'end_date': date_info['end'],
            'analysis_type': analysis_type,
            'original_request': user_input
        }
        
        print(f"📊 분석 대상: {result['stock_name']}({result['stock_code']})")
        print(f"📅 기간: {result['start_date']} ~ {result['end_date']}")
        
        return result
    
    def extract_stock_info(self, text: str) -> Dict[str, str]:
        """텍스트에서 종목 정보 추출"""
        # 종목코드 패턴 (6자리 숫자)
        code_pattern = r'\b(\d{6})\b'
        code_match = re.search(code_pattern, text)
        
        if code_match:
            code = code_match.group(1)
            # 코드로 종목명 찾기 (역검색)
            name = next((k for k, v in self.stock_codes.items() if v == code), f"종목{code}")
            return {'name': name, 'code': code}
        
        # 종목명으로 검색
        for name, code in self.stock_codes.items():
            if name.lower() in text.lower() or name in text:
                return {'name': name, 'code': code}
        
        # 기본값 (삼성전자)
        return {'name': '삼성전자', 'code': '005930'}
    
    def extract_date_info(self, text: str) -> Dict[str, str]:
        """텍스트에서 날짜 정보 추출"""
        today = datetime.now()
        
        # 년월 패턴들
        patterns = [
            r'(\d{4})년\s*(\d{1,2})월',  # 2025년 6월
            r'(\d{4})-(\d{1,2})',        # 2025-06
            r'(\d{4})\.(\d{1,2})',       # 2025.06
            r'(\d{4})/(\d{1,2})',        # 2025/06
        ]
        
        dates_found = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                year, month = int(match[0]), int(match[1])
                dates_found.append(datetime(year, month, 1))
        
        # 기간 키워드 체크
        if '부터' in text and '까지' in text:
            if len(dates_found) >= 2:
                start_date = min(dates_found)
                end_date = max(dates_found)
                # 종료일을 해당 월의 마지막 날로
                if end_date.month == 12:
                    end_date = datetime(end_date.year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_date = datetime(end_date.year, end_date.month + 1, 1) - timedelta(days=1)
            else:
                start_date = today - timedelta(days=365)
                end_date = today
        elif dates_found:
            # 단일 년월인 경우
            target_date = dates_found[0]
            start_date = target_date
            # 해당 월의 마지막 날까지
            if target_date.month == 12:
                end_date = datetime(target_date.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(target_date.year, target_date.month + 1, 1) - timedelta(days=1)
        else:
            # 기본: 최근 1년
            start_date = today - timedelta(days=365)
            end_date = today
        
        return {
            'start': start_date.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d')
        }
    
    def extract_analysis_type(self, text: str) -> str:
        """분석 타입 추출"""
        if '차트' in text or '그래프' in text:
            return 'chart'
        elif '수익률' in text or '수익' in text:
            return 'return'
        elif '상세' in text or '자세' in text:
            return 'detailed'
        else:
            return 'basic'
    
    def get_stock_data(self, stock_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """주식 데이터 수집 (Tool Function)"""
        print(f"📈 주식 데이터 수집 중: {stock_code} ({start_date} ~ {end_date})")
        
        # FinanceDataReader 우선 시도
        if 'FDR' in self.data_sources:
            try:
                data = fdr.DataReader(stock_code, start_date, end_date)
                if not data.empty:
                    print(f"✅ FinanceDataReader로 {len(data)}일 데이터 수집 완료")
                    return data
            except Exception as e:
                print(f"⚠️ FinanceDataReader 실패: {e}")
        
        # yfinance 시도 (한국 주식은 .KS 접미사)
        if 'YF' in self.data_sources:
            try:
                ticker = f"{stock_code}.KS"
                stock = yf.Ticker(ticker)
                data = stock.history(start=start_date, end=end_date)
                if not data.empty:
                    print(f"✅ yfinance로 {len(data)}일 데이터 수집 완료")
                    return data
            except Exception as e:
                print(f"⚠️ yfinance 실패: {e}")
        
        # 데이터 수집 실패시 가상 데이터 생성
        print("⚠️ 실제 데이터 수집 실패 → 시뮬레이션 데이터 생성")
        return self.generate_sample_data(start_date, end_date)
    
    def generate_sample_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """시뮬레이션 데이터 생성"""
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        # 주말 제외
        business_days = [d for d in date_range if d.weekday() < 5]
        
        # 랜덤 워크로 주가 데이터 생성
        np.random.seed(42)
        base_price = 100000  # 10만원 기준
        returns = np.random.normal(0.001, 0.02, len(business_days))  # 일평균 0.1% 수익률, 변동성 2%
        
        prices = [base_price]
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        data = pd.DataFrame({
            'Open': [p * np.random.uniform(0.99, 1.01) for p in prices],
            'High': [p * np.random.uniform(1.00, 1.03) for p in prices],
            'Low': [p * np.random.uniform(0.97, 1.00) for p in prices],
            'Close': prices,
            'Volume': np.random.randint(100000, 1000000, len(business_days))
        }, index=business_days)
        
        # 정수로 변환
        for col in ['Open', 'High', 'Low', 'Close']:
            data[col] = data[col].astype(int)
        
        return data
    
    def calculate_basic_stats(self, data: pd.DataFrame) -> Dict:
        """기본 통계 계산 (Tool Function)"""
        if data.empty:
            return {}
        
        first_price = data['Close'].iloc[0]
        last_price = data['Close'].iloc[-1]
        total_return = (last_price - first_price) / first_price * 100
        
        stats = {
            'period_start': data.index[0].strftime('%Y-%m-%d'),
            'period_end': data.index[-1].strftime('%Y-%m-%d'),
            'trading_days': len(data),
            'start_price': int(first_price),
            'end_price': int(last_price),
            'highest_price': int(data['High'].max()),
            'lowest_price': int(data['Low'].min()),
            'total_return_pct': round(total_return, 2),
            'average_volume': int(data['Volume'].mean()),
            'total_volume': int(data['Volume'].sum()),
            'volatility': round(data['Close'].pct_change().std() * np.sqrt(252) * 100, 2)  # 연간 변동성
        }
        
        return stats
    
    def create_price_chart(self, data: pd.DataFrame, stock_name: str, stock_code: str) -> str:
        """주가 차트 생성 (Tool Function)"""
        if data.empty:
            return "데이터가 없어 차트를 생성할 수 없습니다."
        
        plt.figure(figsize=(12, 8))
        
        # 서브플롯 생성
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), height_ratios=[3, 1])
        
        # 주가 차트
        ax1.plot(data.index, data['Close'], linewidth=2, color='#1f77b4', label='종가')
        ax1.fill_between(data.index, data['Close'], alpha=0.3, color='#1f77b4')
        
        ax1.set_title(f'{stock_name}({stock_code}) 주가 차트', fontsize=16, fontweight='bold')
        ax1.set_ylabel('주가 (원)', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # 주가 포맷팅
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))
        
        # 거래량 차트
        ax2.bar(data.index, data['Volume'], color='orange', alpha=0.7)
        ax2.set_ylabel('거래량', fontsize=12)
        ax2.set_xlabel('날짜', fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        # 날짜 포맷팅
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax2.xaxis.set_major_locator(mdates.MonthLocator())
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        
        # 거래량 포맷팅
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x/1000):,}K'))
        
        plt.tight_layout()
        
        # 차트 저장
        chart_filename = f"{stock_code}_chart.png"
        plt.savefig(chart_filename, dpi=300, bbox_inches='tight')
        plt.show()
        
        return f"차트가 {chart_filename}로 저장되었습니다."
    
    def analyze_stock_performance(self, data: pd.DataFrame) -> Dict:
        """주식 성과 분석 (Tool Function)"""
        if data.empty:
            return {}
        
        # 일일 수익률 계산
        returns = data['Close'].pct_change().dropna()
        
        # 성과 지표들
        analysis = {
            'daily_returns_mean': round(returns.mean() * 100, 3),
            'daily_returns_std': round(returns.std() * 100, 3),
            'positive_days': len(returns[returns > 0]),
            'negative_days': len(returns[returns < 0]),
            'biggest_gain_day': round(returns.max() * 100, 2),
            'biggest_loss_day': round(returns.min() * 100, 2),
            'win_rate': round(len(returns[returns > 0]) / len(returns) * 100, 1)
        }
        
        return analysis
    
    def ai_generate_report(self, stats: Dict, analysis: Dict, stock_name: str, user_request: str) -> str:
        """AI 리포트 생성"""
        if not self.use_ai:
            return self.basic_generate_report(stats, analysis, stock_name)
        
        try:
            # AI에게 보낼 데이터 준비
            data_summary = {
                'stock_name': stock_name,
                'period': f"{stats.get('period_start', '')} ~ {stats.get('period_end', '')}",
                'price_change': f"{stats.get('start_price', 0):,}원 → {stats.get('end_price', 0):,}원",
                'total_return': f"{stats.get('total_return_pct', 0)}%",
                'volatility': f"{stats.get('volatility', 0)}%",
                'trading_volume': f"{stats.get('average_volume', 0):,}주",
                'win_rate': f"{analysis.get('win_rate', 0)}%",
                'user_request': user_request
            }
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """당신은 전문 주식 애널리스트입니다. 주식 분석 데이터를 바탕으로 투자자를 위한 리포트를 작성하세요.

형식:
## 📊 {종목명} 주가 분석 리포트

### 🎯 핵심 요약
- 주요 성과 지표들을 한눈에 보기 쉽게

### 📈 상세 분석
- 가격 변동 분석
- 거래량 분석  
- 위험도 평가

### 💡 투자 관점
- 긍정적 요인
- 주의할 점
- 향후 전망

**주의: 투자 권유가 아닌 정보 제공 목적**"""
                    },
                    {
                        "role": "user", 
                        "content": f"다음 데이터로 주식 분석 리포트를 작성해주세요:\n\n{json.dumps(data_summary, ensure_ascii=False, indent=2)}"
                    }
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ AI 리포트 생성 실패: {e}")
            return self.basic_generate_report(stats, analysis, stock_name)
    
    def basic_generate_report(self, stats: Dict, analysis: Dict, stock_name: str) -> str:
        """기본 리포트 생성"""
        report = f"## 📊 {stock_name} 주가 분석 리포트\n\n"
        
        report += "### 🎯 핵심 요약\n"
        report += f"- **분석 기간**: {stats.get('period_start', '')} ~ {stats.get('period_end', '')}\n"
        report += f"- **가격 변화**: {stats.get('start_price', 0):,}원 → {stats.get('end_price', 0):,}원\n"
        report += f"- **총 수익률**: {stats.get('total_return_pct', 0)}%\n"
        report += f"- **최고가**: {stats.get('highest_price', 0):,}원\n"
        report += f"- **최저가**: {stats.get('lowest_price', 0):,}원\n\n"
        
        report += "### 📈 상세 분석\n"
        report += f"- **거래일수**: {stats.get('trading_days', 0)}일\n"
        report += f"- **평균 거래량**: {stats.get('average_volume', 0):,}주\n"
        report += f"- **변동성**: {stats.get('volatility', 0)}% (연간)\n"
        report += f"- **상승일 비율**: {analysis.get('win_rate', 0)}%\n"
        report += f"- **최대 상승**: {analysis.get('biggest_gain_day', 0)}%\n"
        report += f"- **최대 하락**: {analysis.get('biggest_loss_day', 0)}%\n\n"
        
        # 간단한 평가
        return_pct = stats.get('total_return_pct', 0)
        if return_pct > 10:
            performance = "📈 **우수한 성과**"
        elif return_pct > 0:
            performance = "📊 **양호한 성과**"
        elif return_pct > -10:
            performance = "📉 **보합세**"
        else:
            performance = "📉 **부진한 성과**"
        
        report += f"### 💡 성과 평가\n{performance}\n\n"
        report += "**주의**: 이 분석은 정보 제공 목적이며 투자 권유가 아닙니다.\n"
        
        return report
    
    def run_analysis(self, user_request: str) -> str:
        """통합 분석 실행 (메인 Tool Function)"""
        print(f"\n🚀 주식 분석 시작: '{user_request}'")
        
        # 1. 사용자 요청 파싱
        request_info = self.parse_user_request(user_request)
        
        # 2. 주식 데이터 수집
        stock_data = self.get_stock_data(
            request_info['stock_code'],
            request_info['start_date'], 
            request_info['end_date']
        )
        
        if stock_data is None or stock_data.empty:
            return "❌ 주식 데이터를 가져올 수 없습니다."
        
        # 3. 기본 통계 계산
        basic_stats = self.calculate_basic_stats(stock_data)
        
        # 4. 성과 분석
        performance_analysis = self.analyze_stock_performance(stock_data)
        
        # 5. 차트 생성 (요청시)
        if request_info['analysis_type'] == 'chart':
            chart_result = self.create_price_chart(
                stock_data, 
                request_info['stock_name'], 
                request_info['stock_code']
            )
            print(f"📊 {chart_result}")
        
        # 6. AI 리포트 생성
        report = self.ai_generate_report(
            basic_stats, 
            performance_analysis, 
            request_info['stock_name'],
            user_request
        )
        
        return report
    
    def run_interactive_mode(self):
        """대화형 모드 실행"""
        print("📈 **한국 주식 분석기**")
        print("=" * 50)
        print("🔧 Function/Tool 기반 주식 분석 시스템")
        print()
        print("📝 사용 예시:")
        print("• 'LG전자(066570)의 2025년 6월 주가는 어땠지?'")
        print("• '에이피알(278470)의 2024년 12월부터 2025년 1월까지 주가를 분석해줘'")
        print("• '삼성전자 차트 보여줘'")
        print()
        print("💡 지원 종목:", ', '.join(list(self.stock_codes.keys())[:10]))
        
        while True:
            try:
                user_input = input("\n🤔 분석할 주식을 말씀해주세요 (종료: quit): ").strip()
                
                if user_input.lower() in ['quit', 'exit', '종료', 'q']:
                    print("👋 주식 분석을 종료합니다. 성공적인 투자하세요!")
                    break
                
                if not user_input:
                    print("❌ 분석할 주식을 입력해주세요.")
                    continue
                
                # 분석 실행
                result = self.run_analysis(user_input)
                print(f"\n{result}")
                
            except KeyboardInterrupt:
                print("\n👋 프로그램을 종료합니다.")
                break
            except Exception as e:
                print(f"❌ 오류 발생: {e}")

def main():
    """메인 실행 함수"""
    print("🚀 한국 주식 분석기를 시작합니다!")
    
    # 필요한 라이브러리 체크
    missing_libs = []
    if not FDR_AVAILABLE:
        missing_libs.append("FinanceDataReader")
    if not YF_AVAILABLE:
        missing_libs.append("yfinance")
    
    if missing_libs:
        print(f"⚠️ 다음 라이브러리 설치 권장: {', '.join(missing_libs)}")
        print(f"🔧 설치 명령어: pip install {' '.join(missing_libs)}")
        print("📝 시뮬레이션 데이터로 실행됩니다.\n")
    
    # OpenAI API 키 입력
    use_ai = input("🤖 AI 분석 리포트 사용 (y/n): ").lower() == 'y'
    
    if use_ai:
        api_key = input("🔑 OpenAI API 키 입력: ").strip()
        analyzer = KoreanStockAnalyzer(openai_api_key=api_key if api_key else None)
    else:
        analyzer = KoreanStockAnalyzer()
    
    # 대화형 모드 실행
    analyzer.run_interactive_mode()

if __name__ == "__main__":
    main()