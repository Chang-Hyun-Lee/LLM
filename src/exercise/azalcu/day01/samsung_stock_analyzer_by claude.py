"""
실습: 삼성전자 주가 데이터 분석 ChatGPT 어플리케이션

기능:
1. pykrx로 실제 삼성전자 주가 데이터 수집
2. OpenAI ChatGPT로 전문적인 주식 분석
3. 사용자 친화적인 메뉴 시스템
4. 분석 보고서 자동 생성

작성자: LLM 교육과정 1일차 실습
"""

import os
from datetime import datetime, timedelta
import json

class SamsungStockChatGPT:
    """삼성전자 주가 분석 ChatGPT 어플리케이션"""
    
    def __init__(self):
        self.company_name = "삼성전자"
        self.stock_code = "005930"
        self.openai_client = None
        self.stock_data = None
        
        print("🚀 삼성전자 주가 분석 ChatGPT 어플리케이션")
        print("=" * 50)
    
    def setup_openai_api(self):
        """OpenAI API 설정"""
        print("\n🔑 OpenAI API 설정")
        print("-" * 30)
        
        api_key = "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"
        
        if not api_key:
            print("❌ API 키가 필요합니다!")
            return False
        
        try:
            import openai
            self.openai_client = openai.OpenAI(api_key=api_key)
            
            # API 키 테스트
            print("🤖 API 연결 테스트 중...")
            test_response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            
            print("✅ OpenAI API 연결 성공!")
            return True
            
        except ImportError:
            print("❌ openai 라이브러리가 설치되지 않았습니다.")
            print("💡 설치 명령어: pip3 install openai")
            return False
        except Exception as e:
            print(f"❌ API 연결 실패: {e}")
            print("💡 API 키를 다시 확인해주세요.")
            return False
    
    def collect_stock_data(self, days=30):
        """pykrx로 삼성전자 주가 데이터 수집"""
        print(f"\n📊 {self.company_name} 주가 데이터 수집")
        print("-" * 30)
        
        try:
            from pykrx import stock
            
            # 날짜 설정
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
            
            print(f"📅 수집 기간: {start_date} ~ {end_date}")
            print("🔄 데이터 수집 중...")
            
            # pykrx로 주가 데이터 가져오기
            df = stock.get_market_ohlcv_by_date(start_date, end_date, self.stock_code)
            
            if df.empty:
                print("❌ 데이터를 가져올 수 없습니다.")
                return False
            
            # DataFrame을 리스트로 변환
            stock_list = []
            for date, row in df.iterrows():
                stock_list.append({
                    "날짜": date.strftime("%Y-%m-%d"),
                    "시가": int(row['시가']),
                    "고가": int(row['고가']),
                    "저가": int(row['저가']),
                    "종가": int(row['종가']),
                    "거래량": int(row['거래량'])
                })
            
            self.stock_data = stock_list
            print(f"✅ 총 {len(stock_list)}개 데이터 수집 완료!")
            
            # 최근 3일 데이터 미리보기
            print("\n📈 최근 3일 데이터 미리보기:")
            for item in stock_list[-3:]:
                print(f"  {item['날짜']}: {item['종가']:,}원")
            
            return True
            
        except ImportError:
            print("❌ pykrx 라이브러리가 설치되지 않았습니다.")
            print("💡 설치 명령어: pip3 install pykrx")
            return False
        except Exception as e:
            print(f"❌ 데이터 수집 오류: {e}")
            return False
    
    def calculate_statistics(self):
        """주가 데이터 통계 계산"""
        if not self.stock_data:
            return None
        
        prices = [item["종가"] for item in self.stock_data]
        volumes = [item["거래량"] for item in self.stock_data]
        
        # 기본 통계
        current_price = prices[-1]
        start_price = prices[0]
        max_price = max(prices)
        min_price = min(prices)
        
        # 수익률 계산
        total_return = ((current_price - start_price) / start_price) * 100
        
        # 일일 수익률들
        daily_returns = []
        for i in range(1, len(prices)):
            daily_return = ((prices[i] - prices[i-1]) / prices[i-1]) * 100
            daily_returns.append(daily_return)
        
        # 평균 일일 수익률 및 변동성
        avg_daily_return = sum(daily_returns) / len(daily_returns)
        volatility = (sum([(r - avg_daily_return) ** 2 for r in daily_returns]) / len(daily_returns)) ** 0.5
        
        # 이동평균 (간단 계산)
        ma5 = sum(prices[-5:]) / min(5, len(prices))
        ma20 = sum(prices[-20:]) / min(20, len(prices))
        
        return {
            "분석기간": f"{self.stock_data[0]['날짜']} ~ {self.stock_data[-1]['날짜']}",
            "현재가": current_price,
            "시작가": start_price,
            "최고가": max_price,
            "최저가": min_price,
            "총수익률": round(total_return, 2),
            "평균일일수익률": round(avg_daily_return, 2),
            "변동성": round(volatility, 2),
            "5일이동평균": round(ma5),
            "20일이동평균": round(ma20),
            "평균거래량": round(sum(volumes) / len(volumes)),
            "최대거래량": max(volumes),
            "최소거래량": min(volumes)
        }
    
    def create_analysis_prompt(self, stats):
        """ChatGPT 분석을 위한 프롬프트 생성"""
        
        # 최근 7일 데이터 준비
        recent_data = self.stock_data[-7:] if len(self.stock_data) >= 7 else self.stock_data
        
        prompt = f"""
당신은 20년 경력의 주식 투자 전문가입니다. 
다음 삼성전자 주가 데이터를 분석하고 전문적인 투자 의견을 제시해주세요.

== 기본 정보 ==
종목명: 삼성전자 (005930)
분석기간: {stats['분석기간']}
데이터 개수: {len(self.stock_data)}일

== 주요 지표 ==
현재 주가: {stats['현재가']:,}원
기간 시작가: {stats['시작가']:,}원
최고가: {stats['최고가']:,}원
최저가: {stats['최저가']:,}원

== 수익률 분석 ==
기간 총 수익률: {stats['총수익률']}%
평균 일일 수익률: {stats['평균일일수익률']}%
변동성(표준편차): {stats['변동성']}%

== 기술적 지표 ==
5일 이동평균: {stats['5일이동평균']:,}원
20일 이동평균: {stats['20일이동평균']:,}원
현재가 vs 5일선: {((stats['현재가']/stats['5일이동평균']-1)*100):+.1f}%
현재가 vs 20일선: {((stats['현재가']/stats['20일이동평균']-1)*100):+.1f}%

== 거래량 분석 ==
평균 거래량: {stats['평균거래량']:,}주
최대 거래량: {stats['최대거래량']:,}주
최소 거래량: {stats['최소거래량']:,}주

== 최근 7일 상세 데이터 =="""

        for item in recent_data:
            if recent_data.index(item) > 0:
                prev_price = recent_data[recent_data.index(item)-1]['종가']
                change = ((item['종가'] - prev_price) / prev_price) * 100
                change_text = f" ({change:+.1f}%)"
            else:
                change_text = ""
            
            prompt += f"""
{item['날짜']}: {item['종가']:,}원{change_text}, 거래량: {item['거래량']:,}주"""

        prompt += """

== 분석 요청 사항 ==
위 데이터를 바탕으로 다음 항목들에 대해 전문적으로 분석해주세요:

1. 📊 현재 주가 동향 및 추세 분석
2. 📈 기술적 분석 (이동평균, 지지/저항선, 거래량 패턴)
3. 💰 투자 관점 (매수/매도/관망 의견과 근거)
4. ⚠️ 주요 리스크 요소 및 주의사항
5. 🔮 단기 전망 (향후 1-2주)

객관적이고 균형잡힌 관점에서 분석해주시고, 
투자 결정에 도움이 되는 구체적인 인사이트를 제공해주세요.
"""
        
        return prompt
    
    def analyze_with_chatgpt(self, analysis_type="comprehensive"):
        """ChatGPT로 주식 분석 수행"""
        if not self.openai_client or not self.stock_data:
            print("❌ OpenAI API 또는 주가 데이터가 준비되지 않았습니다.")
            return None
        
        # 통계 계산
        stats = self.calculate_statistics()
        if not stats:
            print("❌ 통계 계산 실패")
            return None
        
        # 분석 타입별 프롬프트
        if analysis_type == "comprehensive":
            prompt = self.create_analysis_prompt(stats)
        elif analysis_type == "technical":
            prompt = f"""
기술적 분석 전문가로서 삼성전자 주가를 분석해주세요.

현재가: {stats['현재가']:,}원
5일 이평: {stats['5일이동평균']:,}원  
20일 이평: {stats['20일이동평균']:,}원
변동성: {stats['변동성']}%

기술적 관점에서:
1. 이동평균선 분석
2. 지지선/저항선 예측
3. 매매 시그널
4. 차트 패턴 분석
을 해주세요.
"""
        elif analysis_type == "risk":
            prompt = f"""
리스크 관리 전문가로서 삼성전자 투자 리스크를 분석해주세요.

총 수익률: {stats['총수익률']}%
변동성: {stats['변동성']}%
최고가: {stats['최고가']:,}원
최저가: {stats['최저가']:,}원

다음을 분석해주세요:
1. 현재 리스크 수준
2. 최대 손실 가능성
3. 적정 투자 비중
4. 리스크 관리 전략
"""
        
        try:
            print("🤖 ChatGPT 분석 중...")
            print("⏳ 잠시만 기다려주세요...")
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": "당신은 한국 주식시장에 정통한 전문 애널리스트입니다. 데이터에 기반한 객관적이고 실용적인 분석을 제공합니다."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            analysis_result = response.choices[0].message.content
            print("✅ ChatGPT 분석 완료!")
            return analysis_result
            
        except Exception as e:
            print(f"❌ ChatGPT 분석 오류: {e}")
            return None
    
    def display_basic_info(self):
        """기본 정보 출력"""
        if not self.stock_data:
            print("❌ 주가 데이터가 없습니다.")
            return
        
        stats = self.calculate_statistics()
        
        print(f"\n📊 {self.company_name} 기본 정보")
        print("=" * 40)
        print(f"📅 분석기간: {stats['분석기간']}")
        print(f"📈 현재 주가: {stats['현재가']:,}원")
        print(f"📈 기간 수익률: {stats['총수익률']:+.2f}%")
        print(f"📊 변동성: {stats['변동성']:.2f}%")
        print(f"📊 5일 이평선: {stats['5일이동평균']:,}원")
        print(f"📊 20일 이평선: {stats['20일이동평균']:,}원")
        
        # 간단한 추세 판단
        if stats['현재가'] > stats['5일이동평균']:
            trend = "🟢 단기 상승 추세"
        elif stats['현재가'] < stats['5일이동평균']:
            trend = "🔴 단기 하락 추세"
        else:
            trend = "🟡 보합세"
        
        print(f"📈 추세: {trend}")
    
    def save_report(self, analysis_result, analysis_type):
        """분석 보고서 저장"""
        stats = self.calculate_statistics()
        
        report = f"""
{'='*80}
🏢 {self.company_name} 주가 분석 보고서
📅 생성일시: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}
📊 분석 유형: {analysis_type}
{'='*80}

📊 기본 데이터
{'-'*40}
📅 분석 기간: {stats['분석기간']}
📈 현재 주가: {stats['현재가']:,}원
📈 기간 수익률: {stats['총수익률']:+.2f}%
📊 변동성: {stats['변동성']:.2f}%
📊 이동평균: 5일({stats['5일이동평균']:,}원), 20일({stats['20일이동평균']:,}원)
📊 거래량: 평균({stats['평균거래량']:,}주), 최대({stats['최대거래량']:,}주)

{'='*80}
🤖 ChatGPT 전문 분석
{'='*80}
{analysis_result}

{'='*80}
📌 보고서 정보
{'='*80}
- 데이터 출처: pykrx (한국거래소 공식)
- AI 분석: OpenAI ChatGPT-3.5-turbo
- 프로그램: 삼성전자 주가 분석 ChatGPT 어플리케이션
- 면책사항: 본 분석은 교육 및 참고 목적이며, 실제 투자 결정은 본인 책임입니다.
"""
        
        filename = f"samsung_analysis_{analysis_type}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"💾 보고서가 '{filename}' 파일로 저장되었습니다.")
        except Exception as e:
            print(f"❌ 파일 저장 오류: {e}")
    
    def run_application(self):
        """메인 어플리케이션 실행"""
        
        # 1. OpenAI API 설정
        if not self.setup_openai_api():
            print("👋 어플리케이션을 종료합니다.")
            return
        
        # 2. 분석 기간 설정
        print(f"\n📅 분석 기간 설정")
        print("-" * 30)
        days_input = input("분석할 일수를 입력하세요 (기본값: 30일): ").strip()
        days = int(days_input) if days_input.isdigit() and int(days_input) > 0 else 30
        
        # 3. 주가 데이터 수집
        if not self.collect_stock_data(days):
            print("👋 어플리케이션을 종료합니다.")
            return
        
        # 4. 기본 정보 표시
        self.display_basic_info()
        
        # 5. 메뉴 시스템
        while True:
            print(f"\n🎯 {self.company_name} 분석 메뉴")
            print("=" * 40)
            print("1. 📊 종합 분석 (추천)")
            print("2. 📈 기술적 분석")
            print("3. ⚠️ 리스크 분석")
            print("4. 📋 전체 보고서 생성")
            print("5. 🔄 새로운 기간으로 다시 분석")
            print("6. 👋 종료")
            
            choice = input("\n선택하세요 (1-6): ").strip()
            
            if choice == '1':
                print(f"\n🔍 {self.company_name} 종합 분석")
                print("=" * 50)
                result = self.analyze_with_chatgpt("comprehensive")
                if result:
                    print(result)
                    
                    save_choice = input("\n💾 보고서를 파일로 저장하시겠습니까? (y/n): ").strip().lower()
                    if save_choice == 'y':
                        self.save_report(result, "종합분석")
            
            elif choice == '2':
                print(f"\n📈 {self.company_name} 기술적 분석")
                print("=" * 50)
                result = self.analyze_with_chatgpt("technical")
                if result:
                    print(result)
                    
                    save_choice = input("\n💾 보고서를 파일로 저장하시겠습니까? (y/n): ").strip().lower()
                    if save_choice == 'y':
                        self.save_report(result, "기술적분석")
            
            elif choice == '3':
                print(f"\n⚠️ {self.company_name} 리스크 분석")
                print("=" * 50)
                result = self.analyze_with_chatgpt("risk")
                if result:
                    print(result)
                    
                    save_choice = input("\n💾 보고서를 파일로 저장하시겠습니까? (y/n): ").strip().lower()
                    if save_choice == 'y':
                        self.save_report(result, "리스크분석")
            
            elif choice == '4':
                print(f"\n📋 {self.company_name} 전체 보고서 생성")
                print("=" * 50)
                print("🤖 종합분석, 기술적분석, 리스크분석을 모두 수행합니다...")
                
                comprehensive = self.analyze_with_chatgpt("comprehensive")
                technical = self.analyze_with_chatgpt("technical")
                risk = self.analyze_with_chatgpt("risk")
                
                if all([comprehensive, technical, risk]):
                    combined_report = f"""
📊 종합 분석
{'='*60}
{comprehensive}

📈 기술적 분석  
{'='*60}
{technical}

⚠️ 리스크 분석
{'='*60}
{risk}
"""
                    print(combined_report)
                    self.save_report(combined_report, "전체보고서")
                else:
                    print("❌ 일부 분석에서 오류가 발생했습니다.")
            
            elif choice == '5':
                print("\n🔄 새로운 분석 시작")
                days_input = input("새로운 분석 일수를 입력하세요: ").strip()
                days = int(days_input) if days_input.isdigit() and int(days_input) > 0 else 30
                
                if self.collect_stock_data(days):
                    self.display_basic_info()
                else:
                    print("❌ 데이터 수집 실패")
            
            elif choice == '6':
                print("\n👋 삼성전자 주가 분석을 종료합니다.")
                print("💡 생성된 보고서 파일들을 확인해보세요!")
                break
            
            else:
                print("❌ 올바른 번호(1-6)를 선택해주세요.")

def main():
    """메인 함수"""
    try:
        app = SamsungStockChatGPT()
        app.run_application()
    except KeyboardInterrupt:
        print("\n\n👋 사용자가 프로그램을 중단했습니다.")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류가 발생했습니다: {e}")
        print("💡 프로그램을 다시 실행해보세요.")

if __name__ == "__main__":
    main()