import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# 한글 폰트 설정 (Windows)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# Mac이나 Linux라면 이걸 사용:
# plt.rcParams['font.family'] = 'AppleGothic'  # Mac
# plt.rcParams['font.family'] = 'DejaVu Sans'  # Linux

# 엔비디아 주식 정보 가져오기
nvda = yf.Ticker("NVDA")

# 기본 정보 출력
print("=== 엔비디아 기본 정보 ===")
info = nvda.info
print(f"회사명: {info.get('longName', 'N/A')}")
print(f"현재 주가: ${info.get('currentPrice', 'N/A')}")
print(f"시가총액: ${info.get('marketCap', 'N/A'):,}")
print(f"52주 최고가: ${info.get('fiftyTwoWeekHigh', 'N/A')}")
print(f"52주 최저가: ${info.get('fiftyTwoWeekLow', 'N/A')}")

# 최근 30일 주가 데이터 가져오기
print("\n=== 최근 30일 주가 데이터 ===")
hist_data = nvda.history(period="1mo")
print(hist_data.tail())

# 최근 1년 주가 차트 그리기
print("\n=== 주가 차트 생성 중... ===")
hist_1year = nvda.history(period="1y")

plt.figure(figsize=(12, 6))
plt.plot(hist_1year.index, hist_1year['Close'], linewidth=2)
plt.title('엔비디아 (NVDA) 1년 주가 차트', fontsize=16)
plt.xlabel('날짜')
plt.ylabel('주가 ($)')
plt.grid(True, alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# 월별 수익률 계산
monthly_data = hist_1year['Close'].resample('M').last()
monthly_returns = monthly_data.pct_change().dropna() * 100

print("\n=== 월별 수익률 (%) ===")
for date, return_rate in monthly_returns.items():
    print(f"{date.strftime('%Y-%m')}: {return_rate:.2f}%")

# 간단한 통계
print(f"\n=== 1년간 통계 ===")
print(f"평균 수익률: {monthly_returns.mean():.2f}%")
print(f"수익률 표준편차: {monthly_returns.std():.2f}%")
print(f"최대 상승: {monthly_returns.max():.2f}%")
print(f"최대 하락: {monthly_returns.min():.2f}%")
