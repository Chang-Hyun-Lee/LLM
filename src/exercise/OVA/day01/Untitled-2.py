#!/usr/bin/env python3
"""
지역 음식점 추천 애플리케이션
사용자의 자연어 질문을 분석하여 OpenAI GPT와 Kakao Local API를 통해 음식점을 추천합니다.
"""

import os
import requests
import json
import openai
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import re

class RestaurantRecommender:
    def __init__(self, openai_api_key: str = None, kakao_api_key: str = None):
        """
        음식점 추천 시스템 초기화
        
        Args:
            openai_api_key (str): OpenAI API 키
            kakao_api_key (str): Kakao REST API 키
        """
        # OpenAI API 설정
        if openai_api_key:
            openai.api_key = openai_api_key
        else:
            openai.api_key = os.getenv('OPENAI_API_KEY')
            if not openai.api_key:
                raise ValueError("OpenAI API 키가 필요합니다. OPENAI_API_KEY 환경변수를 설정하거나 직접 전달해주세요.")
        
        # Kakao API 설정
        self.kakao_api_key = kakao_api_key or os.getenv('KAKAO_API_KEY')
        if not self.kakao_api_key:
            raise ValueError("Kakao API 키가 필요합니다. KAKAO_API_KEY 환경변수를 설정하거나 직접 전달해주세요.")
        
        self.kakao_headers = {
            'Authorization': f'KakaoAK {self.kakao_api_key}'
        }
        
        self.search_results = []

    def extract_location_and_category(self, user_query: str) -> Dict[str, str]:
        """
        OpenAI GPT를 사용하여 사용자 질문에서 지역명과 음식 종류를 추출
        
        Args:
            user_query (str): 사용자의 자연어 질문
            
        Returns:
            Dict[str, str]: 추출된 지역명과 음식 카테고리
        """
        try:
            print(f"🤖 사용자 질문 분석 중: '{user_query}'")
            
            # GPT에게 전달할 프롬프트 구성
            system_prompt = """
            당신은 음식점 검색을 위한 정보 추출 전문가입니다. 
            사용자의 질문에서 다음 정보를 정확히 추출해주세요:
            1. 지역명 (구체적인 동네, 구, 시 등)
            2. 음식 종류 (한식, 일식, 중식, 양식, 이탈리안, 카페, 치킨, 피자 등)
            
            응답은 반드시 다음 JSON 형식으로만 답변해주세요:
            {
                "location": "추출된 지역명",
                "category": "추출된 음식종류",
                "confidence": "high/medium/low"
            }
            
            만약 지역명이나 음식종류를 명확히 파악할 수 없다면 "unknown"으로 표시하세요.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            # GPT 응답에서 JSON 추출
            gpt_response = response.choices[0].message.content.strip()
            
            # JSON 파싱 시도
            try:
                # 혹시 마크다운 코드 블록이 있다면 제거
                if "```json" in gpt_response:
                    gpt_response = gpt_response.split("```json")[1].split("```")[0]
                elif "```" in gpt_response:
                    gpt_response = gpt_response.split("```")[1].split("```")[0]
                
                extracted_info = json.loads(gpt_response)
                
                print(f"📍 추출된 정보:")
                print(f"   - 지역: {extracted_info.get('location', 'unknown')}")
                print(f"   - 음식종류: {extracted_info.get('category', 'unknown')}")
                print(f"   - 신뢰도: {extracted_info.get('confidence', 'unknown')}")
                
                return extracted_info
                
            except json.JSONDecodeError:
                print("⚠️ GPT 응답을 JSON으로 파싱할 수 없습니다. 기본값 사용.")
                return {
                    "location": "unknown",
                    "category": "unknown", 
                    "confidence": "low"
                }
                
        except Exception as e:
            print(f"❌ 정보 추출 중 오류 발생: {e}")
            return {
                "location": "unknown",
                "category": "unknown",
                "confidence": "low"
            }

    def search_restaurants(self, location: str, category: str, size: int = 15) -> List[Dict]:
        """
        Kakao Local API를 사용하여 음식점 검색
        
        Args:
            location (str): 지역명
            category (str): 음식 카테고리
            size (int): 검색 결과 개수 (최대 15개)
            
        Returns:
            List[Dict]: 검색된 음식점 정보 리스트
        """
        try:
            print(f"🔍 카카오 API로 음식점 검색 중...")
            
            # 검색 쿼리 구성
            if location != "unknown" and category != "unknown":
                query = f"{location} {category}"
            elif location != "unknown":
                query = f"{location} 맛집"
            elif category != "unknown":
                query = f"{category} 맛집"
            else:
                query = "맛집"
            
            print(f"📝 검색 쿼리: '{query}'")
            
            # Kakao Local API 호출
            url = "https://dapi.kakao.com/v2/local/search/keyword.json"
            params = {
                'query': query,
                'category_group_code': 'FD6',  # 음식점 카테고리
                'size': min(size, 15),  # 최대 15개
                'sort': 'accuracy'  # 정확도순 정렬
            }
            
            response = requests.get(url, headers=self.kakao_headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            restaurants = data.get('documents', [])
            
            print(f"✅ {len(restaurants)}개의 음식점을 찾았습니다.")
            
            # 결과 저장
            self.search_results = restaurants
            return restaurants
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Kakao API 호출 중 오류 발생: {e}")
            return []
        except Exception as e:
            print(f"❌ 음식점 검색 중 오류 발생: {e}")
            return []

    def summarize_restaurants(self, restaurants: List[Dict], user_query: str) -> str:
        """
        OpenAI GPT를 사용하여 검색된 음식점 목록을 요약하고 추천 설명 생성
        
        Args:
            restaurants (List[Dict]): 검색된 음식점 정보
            user_query (str): 원래 사용자 질문
            
        Returns:
            str: GPT가 생성한 추천 요약
        """
        if not restaurants:
            return "죄송합니다. 검색 결과가 없습니다."
        
        try:
            print("🤖 GPT로 추천 요약 생성 중...")
            
            # 음식점 정보를 텍스트로 변환
            restaurant_info = []
            for i, restaurant in enumerate(restaurants[:10], 1):  # 상위 10개만 사용
                info = f"{i}. {restaurant.get('place_name', '이름없음')}"
                if restaurant.get('category_name'):
                    info += f" ({restaurant['category_name']})"
                if restaurant.get('road_address_name'):
                    info += f" - {restaurant['road_address_name']}"
                if restaurant.get('phone'):
                    info += f" - ☎️ {restaurant['phone']}"
                restaurant_info.append(info)
            
            restaurants_text = "\n".join(restaurant_info)
            
            system_prompt = """
            당신은 친근하고 전문적인 음식점 추천 전문가입니다. 
            사용자의 질문과 검색된 음식점 목록을 바탕으로 유용하고 매력적인 추천 요약을 작성해주세요.
            
            다음 사항을 포함해주세요:
            1. 사용자 질문에 대한 간단한 응답
            2. 추천 음식점들의 특징이나 장점
            3. 방문 시 참고사항이나 팁
            4. 친근하고 도움이 되는 톤
            
            너무 길지 않게 3-5문장 정도로 작성해주세요.
            """
            
            user_prompt = f"""
            사용자 질문: "{user_query}"
            
            검색된 음식점 목록:
            {restaurants_text}
            
            위 정보를 바탕으로 사용자에게 도움이 될 추천 요약을 작성해주세요.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            summary = response.choices[0].message.content.strip()
            print("✅ 추천 요약 생성 완료")
            return summary
            
        except Exception as e:
            print(f"❌ 추천 요약 생성 중 오류 발생: {e}")
            return f"'{user_query}'에 대한 검색 결과입니다. 아래 음식점들을 확인해보세요!"

    def format_restaurant_info(self, restaurants: List[Dict]) -> str:
        """
        음식점 정보를 보기 좋은 형식으로 포맷팅
        
        Args:
            restaurants (List[Dict]): 음식점 정보 리스트
            
        Returns:
            str: 포맷팅된 음식점 정보
        """
        if not restaurants:
            return "검색 결과가 없습니다."
        
        formatted_info = []
        formatted_info.append("=" * 80)
        formatted_info.append("🍴 추천 음식점 목록")
        formatted_info.append("=" * 80)
        
        for i, restaurant in enumerate(restaurants, 1):
            formatted_info.append(f"\n📍 {i}. {restaurant.get('place_name', '이름없음')}")
            
            # 카테고리 정보
            if restaurant.get('category_name'):
                category = restaurant['category_name'].replace('>', ' > ')
                formatted_info.append(f"   🏷️  카테고리: {category}")
            
            # 주소 정보
            if restaurant.get('road_address_name'):
                formatted_info.append(f"   📍 도로명주소: {restaurant['road_address_name']}")
            elif restaurant.get('address_name'):
                formatted_info.append(f"   📍 지번주소: {restaurant['address_name']}")
            
            # 전화번호
            if restaurant.get('phone'):
                formatted_info.append(f"   ☎️  전화번호: {restaurant['phone']}")
            
            # 거리 정보
            if restaurant.get('distance'):
                distance = int(restaurant['distance'])
                if distance < 1000:
                    formatted_info.append(f"   📏 거리: {distance}m")
                else:
                    formatted_info.append(f"   📏 거리: {distance/1000:.1f}km")
            
            # 웹사이트 링크
            if restaurant.get('place_url'):
                formatted_info.append(f"   🔗 상세정보: {restaurant['place_url']}")
            
            formatted_info.append("-" * 60)
        
        return "\n".join(formatted_info)

    def save_results_to_file(self, user_query: str, summary: str, formatted_results: str) -> str:
        """
        검색 결과를 텍스트 파일로 저장
        
        Args:
            user_query (str): 사용자 질문
            summary (str): GPT 요약
            formatted_results (str): 포맷팅된 결과
            
        Returns:
            str: 저장된 파일명
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"restaurant_recommendation_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("🍽️ 음식점 추천 결과\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"📝 사용자 질문: {user_query}\n")
                f.write(f"🕐 검색 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("🤖 AI 추천 요약:\n")
                f.write("-" * 30 + "\n")
                f.write(f"{summary}\n\n")
                f.write(formatted_results)
                f.write(f"\n\n💡 이 결과는 OpenAI GPT와 Kakao Local API를 활용하여 생성되었습니다.")
            
            print(f"📁 결과가 '{filename}' 파일로 저장되었습니다.")
            return filename
            
        except Exception as e:
            print(f"❌ 파일 저장 중 오류 발생: {e}")
            return ""

    def run_recommendation(self, user_query: str, save_to_file: bool = True) -> Dict:
        """
        전체 추천 과정을 실행하는 통합 메서드
        
        Args:
            user_query (str): 사용자 질문
            save_to_file (bool): 파일 저장 여부
            
        Returns:
            Dict: 실행 결과 정보
        """
        print("🚀 음식점 추천 시스템 시작")
        print("=" * 50)
        
        try:
            # 1단계: 지역과 카테고리 추출
            extracted_info = self.extract_location_and_category(user_query)
            
            # 2단계: 음식점 검색
            restaurants = self.search_restaurants(
                extracted_info.get('location', 'unknown'),
                extracted_info.get('category', 'unknown')
            )
            
            if not restaurants:
                print("😔 죄송합니다. 검색 결과가 없습니다.")
                return {
                    'success': False,
                    'message': '검색 결과가 없습니다.',
                    'restaurants': []
                }
            
            # 3단계: GPT 요약 생성
            summary = self.summarize_restaurants(restaurants, user_query)
            
            # 4단계: 결과 포맷팅
            formatted_results = self.format_restaurant_info(restaurants)
            
            # 5단계: 결과 출력
            print("\n🎯 AI 추천 요약:")
            print("=" * 50)
            print(summary)
            print("\n")
            print(formatted_results)
            
            # 6단계: 파일 저장 (선택사항)
            saved_file = ""
            if save_to_file:
                saved_file = self.save_results_to_file(user_query, summary, formatted_results)
            
            print("\n✅ 추천 완료!")
            return {
                'success': True,
                'extracted_info': extracted_info,
                'restaurants': restaurants,
                'summary': summary,
                'saved_file': saved_file
            }
            
        except Exception as e:
            print(f"❌ 추천 과정 중 오류 발생: {e}")
            return {
                'success': False,
                'error': str(e),
                'restaurants': []
            }


def main():
    """
    메인 함수 - 전체 애플리케이션 실행 흐름을 통합
    """
    print("🍽️ 지역 음식점 추천 시스템에 오신 것을 환영합니다!")
    print("=" * 60)
    print("💡 사용법: '강남에 있는 괜찮은 이탈리안 식당 추천해줘'와 같이 자연스럽게 질문해보세요.")
    print("💡 필요한 API 키: OPENAI_API_KEY, KAKAO_API_KEY (환경변수 설정)")
    print("=" * 60)
    
    try:
        # 추천 시스템 초기화
        openai_key = "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"
        kakao_key = "w3cxsuB1Hz83dEUpvpzkJbobkcSRW6MJAAAAAQoXEi0AAAGYL48Oj08FYMfcu4fs"
        
        while True:
            print("\n" + "🔍 음식점 검색" + "=" * 45)
            
            # 사용자 입력 받기
            user_query = input("👤 어떤 음식점을 찾고 계신가요? (종료하려면 'quit' 입력): ").strip()
            
            if user_query.lower() in ['quit', '종료', 'exit', 'q']:
                print("👋 음식점 추천 시스템을 종료합니다. 맛있는 식사 되세요!")
                break
            
            if not user_query:
                print("⚠️ 질문을 입력해주세요.")
                continue
            
            print(f"\n📝 질문: '{user_query}'")
            
            # 추천 실행
            result = recommender.run_recommendation(user_query, save_to_file=True)
            
            if not result['success']:
                print("😔 추천을 완료하지 못했습니다. 다른 질문을 시도해보세요.")
                continue
            
            # 추가 옵션 제공
            print("\n" + "🔄 추가 옵션" + "=" * 45)
            choice = input("다른 검색을 하시겠습니까? (y/n): ").strip().lower()
            
            if choice not in ['y', 'yes', '네', 'ㅇ']:
                print("👋 이용해 주셔서 감사합니다!")
                break
    
    except KeyboardInterrupt:
        print("\n\n👋 사용자에 의해 프로그램이 종료되었습니다.")
    except Exception as e:
        print(f"\n❌ 프로그램 실행 중 오류 발생: {e}")
        print("💡 API 키 설정을 확인해주세요:")
        print("   - export OPENAI_API_KEY='your-openai-key'")
        print("   - export KAKAO_API_KEY='your-kakao-key'")


if __name__ == "__main__":
    main()