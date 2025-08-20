import os
from datetime import datetime
import sys

def test_environment():
    """환경 및 API 키 테스트"""
    print("=" * 50)
    print("🚀 Alpha Seeker 시스템 테스트")
    print("=" * 50)
    
    # 현재 시간
    current_time = datetime.now()
    print(f"⏰ 실행 시간: {current_time}")
    print(f"🐍 Python 버전: {sys.version}")
    
    # API 키 확인
    api_status = {}
    
    # Telegram
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if telegram_token and len(telegram_token) > 10:
        print("✅ Telegram Bot Token: 설정됨")
        api_status['telegram'] = True
    else:
        print("❌ Telegram Bot Token: 없음")
        api_status['telegram'] = False
    
    # Telegram Chat ID
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if chat_id:
        print("✅ Telegram Chat ID: 설정됨")
        api_status['chat_id'] = True
    else:
        print("❌ Telegram Chat ID: 없음")
        api_status['chat_id'] = False
    
    # Alpaca
    alpaca_key = os.getenv('ALPACA_API_KEY')
    if alpaca_key and len(alpaca_key) > 10:
        print("✅ Alpaca API Key: 설정됨")
        api_status['alpaca'] = True
    else:
        print("❌ Alpaca API Key: 없음")
        api_status['alpaca'] = False
    
    # Perplexity
    perplexity_key = os.getenv('PERPLEXITY_API_KEY')
    if perplexity_key and len(perplexity_key) > 10:
        print("✅ Perplexity API Key: 설정됨")
        api_status['perplexity'] = True
    else:
        print("❌ Perplexity API Key: 없음")
        api_status['perplexity'] = False
    
    print("=" * 50)
    
    # 전체 결과
    total_apis = len(api_status)
    working_apis = sum(api_status.values())
    
    if working_apis == total_apis:
        print("🎉 모든 API 키가 정상적으로 설정되었습니다!")
        print("🚀 다음 단계로 진행할 준비가 완료되었습니다.")
    else:
        print(f"⚠️  {total_apis}개 중 {working_apis}개 API 키가 설정됨")
        print("❗ 누락된 API 키를 GitHub Secrets에 추가해주세요.")
    
    print("=" * 50)
    print("✨ STEP 2 테스트 완료!")

if __name__ == "__main__":
    test_environment()
