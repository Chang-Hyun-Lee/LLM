# stock_database.py

import streamlit as st
from pykrx import stock
import json
import os

DB_FILE = "stock_db.json"
US_STOCKS_MAP = {
    "엔비디아": "NVDA", "마이크로소프트": "MSFT", "테슬라": "TSLA",
    "애플": "AAPL", "구글": "GOOGL", "아마존": "AMZN",
}

def validate_db(db: dict) -> bool:
    """DB 파일의 형식이 올바른지 검증합니다."""
    required_keys = ["KR_name_map", "KR_ticker_map", "US"]
    return all(key in db for key in required_keys)

def create_new_db():
    print("📚 네트워크에서 주식 데이터베이스를 최초 다운로드합니다... (2~5분 소요)")
    db = {"KR_name_map": {}, "KR_ticker_map": {}, "US": US_STOCKS_MAP}
    try:
        tickers = stock.get_market_ticker_list(market="ALL")
        names = [stock.get_market_ticker_name(t) for t in tickers]
        db["KR_name_map"] = dict(zip(names, tickers))
        db["KR_ticker_map"] = dict(zip(tickers, names))
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(db, f, ensure_ascii=False, indent=4)
        print("📚 주식 데이터베이스 파일 생성 완료!")
        return db, True
    except Exception as e:
        print(f"주식 목록을 불러오는 데 실패했습니다: {e}")
        return None, False

def get_stock_database():
    if os.path.exists(DB_FILE):
        print(f"📚 로컬 파일({DB_FILE})에서 주식 데이터베이스를 로드합니다.")
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            db = json.load(f)
            # ✨ 1. DB 파일 유효성 검사
            if validate_db(db):
                return db, False
            else:
                print("⚠️ 데이터베이스 형식이 올바르지 않습니다. 새로 생성합니다.")
                return create_new_db()
    else:
        return create_new_db()