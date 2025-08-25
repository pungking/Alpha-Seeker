from datetime import datetime, timedelta
import pytz

# 한국시간 타임존 설정
KST = pytz.timezone('Asia/Seoul')
EST = pytz.timezone('US/Eastern')

def get_now_kst():
    """현재 한국시간 반환"""
    return datetime.now(KST)

def get_now_est():
    """현재 미국 동부시간 반환 (NYSE 기준)"""
    return datetime.now(EST)

def get_analysis_type():
    """현재 시간에 맞는 분석 타입 결정 (개선된 버전)"""
    now = get_now_kst()
    current_hour = now.hour
    current_minute = now.minute
    current_weekday = now.weekday()  # 0=월요일, 6=일요일
    
    # 일요일 오후 5-7시: 주간 분석
    if current_weekday == 6 and 17 <= current_hour <= 19:
        return "sunday_analysis"
    # 평일 오전 5-8시: 오전 분석
    elif 0 <= current_weekday <= 4 and 5 <= current_hour <= 8:
        return "morning_analysis"
    # 평일 오후 11:25-11:35: 프리마켓 분석 (개선됨 - 23:30 KST)
    elif 0 <= current_weekday <= 4 and current_hour == 23 and 25 <= current_minute <= 35:
        return "pre_market_analysis"
    else:
        return "general_analysis"

def is_market_day():
    """거래일 여부 확인"""
    now = get_now_kst()
    weekday = now.weekday()
    return 0 <= weekday <= 4

def get_next_analysis_time():
    """다음 분석 시간 계산"""
    now = get_now_kst()
    current_hour = now.hour
    current_weekday = now.weekday()
    
    if current_weekday == 6:  # 일요일
        if current_hour < 18:
            return "오늘 18:23"
        else:
            return "내일 06:07"
    elif 0 <= current_weekday <= 4:  # 평일
        if current_hour < 6:
            return "오늘 06:07"
        elif current_hour < 23:
            return "오늘 23:30"  # 개선된 시간
        else:
            return "내일 06:07"
    else:  # 토요일
        return "내일 18:23"

def get_us_market_status():
    """미국 시장 상태 상세 정보"""
    try:
        now_est = get_now_est()
        current_hour = now_est.hour
        current_minute = now_est.minute
        weekday = now_est.weekday()
        
        if weekday > 4:  # 주말
            return {
                'status': 'closed',
                'reason': 'weekend',
                'next_open': '월요일 09:30 EST'
            }
        
        current_minutes = current_hour * 60 + current_minute
        
        if current_minutes < 4 * 60:  # 새벽 4시 이전
            return {
                'status': 'closed',
                'reason': 'pre_pre_market',
                'next_event': 'pre_market_04:00'
            }
        elif current_minutes < 9 * 60 + 30:  # 9:30 이전
            return {
                'status': 'pre_market',
                'reason': 'pre_market_trading',
                'next_event': 'market_open_09:30'
            }
        elif current_minutes <= 16 * 60:  # 4시 이전
            return {
                'status': 'open',
                'reason': 'regular_trading',
                'next_event': 'market_close_16:00'
            }
        elif current_minutes <= 20 * 60:  # 8시 이전
            return {
                'status': 'after_market',
                'reason': 'after_market_trading', 
                'next_event': 'market_closed_20:00'
            }
        else:
            return {
                'status': 'closed',
                'reason': 'overnight',
                'next_event': 'pre_market_04:00'
            }
            
    except Exception:
        return {
            'status': 'unknown',
            'reason': 'error',
            'next_event': 'unknown'
        }

print("✅ TimeUtils Enhanced 모듈 로드 완료 (한국시간 + 미국시장 연동)")
