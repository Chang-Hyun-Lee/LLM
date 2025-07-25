# utils_input_AIcheck.py

import difflib

def normalize_input(text: str) -> str:
    """사용자 입력을 검색에 용이하도록 정규화합니다 (공백제거, 소문자)."""
    return text.strip().lower().replace(" ", "")

def find_closest_stock(user_input: str, market_code: str, db: dict) -> dict:
    print(f"🤖 종목명 검색 실행: 입력='{user_input}', 시장='{market_code}'")
    
    if market_code == "KR":
        name_map = db.get("KR_name_map", {})
        ticker_map = db.get("KR_ticker_map", {})
    elif market_code == "US":
        name_map = db.get("US", {})
        ticker_map = {v: k for k, v in name_map.items()}
    else:
        return {"status": "error", "message": "알 수 없는 시장 코드입니다."}

    # ✨ 1. 정규화된 입력값 사용
    normalized_user_input = normalize_input(user_input)

    # 2. 티커/종목명 정확히 일치 확인 (정규화된 이름으로 비교)
    if market_code == "KR" and user_input.isdigit() and user_input in ticker_map:
        official_name = ticker_map[user_input]
        return {"status": "exact", "official_name": official_name, "ticker": user_input}

    for official_name, ticker in name_map.items():
        if normalized_user_input == normalize_input(official_name) or user_input.upper() == ticker:
            return {"status": "exact", "official_name": official_name, "ticker": ticker}

    # 3. 유사한 이름 검색 (cutoff 상향)
    all_names = list(name_map.keys())
    best_matches = difflib.get_close_matches(user_input, all_names, n=3, cutoff=0.7)
    
    if best_matches:
        return {"status": "suggestion", "suggestions": best_matches}
    else:
        market_name = "한국" if market_code == "KR" else "미국"
        example = "삼성전자" if market_code == "KR" else "NVDA"
        return {"status": "not_found", "message": f"'{user_input}'에 해당하는 종목을 {market_name} 시장에서 찾을 수 없습니다. (예: {example})"}