from datetime import datetime
import pytz

# 한국시간 타임존 설정
KST = pytz.timezone('Asia/Seoul')

def get_now_kst():
    """현재 한국시간 반환"""
    return datetime.now(KST)

def get_analysis_type():
    """현재 시간에 맞는 분석 타입 결정 (한국시간 기준)"""
    now = get_now_kst()
    current_hour = now.hour
    current_weekday = now.weekday()  # 0=월요일, 6=일요일
    
    if current_weekday == 6 and 17 <= current_hour <= 19:  # 일요일 오후 6-7시
        return "sunday_analysis"
    elif 5 <= current_hour <= 8:  # 오전 6-8시
        return "morning_analysis"
    elif 21 <= current_hour <= 23:  # 오후 9-11시  
        return "pre_market_analysis"
    else:
        return "general_analysis"

def is_market_day():
    """거래일 여부 확인"""
    now = get_now_kst()
    weekday = now.weekday()
    
    # 월요일(0) ~ 금요일(4)만 거래일
    return 0 <= weekday <= 4

def get_next_analysis_time():
    """다음 분석 시간 계산"""
    now = get_now_kst()
    current_hour = now.hour
    
    if current_hour < 6:
        return "오늘 06:07"
    elif current_hour < 22:
        return "오늘 22:13"
    else:
        return "내일 06:07"

# 모듈 로드 확인
print("✅ TimeUtils 모듈 로드 완료 (한국시간 적용)")
