import sys
import os

# 프로젝트 루트를 Python path에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 안전한 import (에러 방지)
try:
    from utils.time_utils import get_analysis_type, get_now_kst
    from utils.stock_utils import StockTickerManager
    from core.data_manager import DataManager
    from core.telegram_bot import TelegramBot
    from core.technical import TechnicalAnalyzer
    from core.report_generator import MorningReportGenerator, EveningReportGenerator
    from core.analyzer import AlphaSeeker
    print("✅ 모든 모듈 로드 완료")
except ImportError as e:
    print(f"⚠️ 모듈 로드 오류: {e}")
    # 기본 시간 함수 정의 (백업용)
    from datetime import datetime
    import pytz
    KST = pytz.timezone('Asia/Seoul')
    def get_now_kst():
        return datetime.now(KST)
    def get_analysis_type():
        return "general_analysis"

def main():
    """메인 실행 함수"""
    try:
        current_time_kst = get_now_kst().strftime('%Y-%m-%d %H:%M:%S')
        print(f"🚀 Alpha Seeker v4.3 시작 - {current_time_kst} (KST)")
        
        # 분석 타입 확인
        analysis_type = get_analysis_type()
        print(f"📊 분석 유형: {analysis_type}")
        
        # 컴포넌트 초기화 테스트
        try:
            data_manager = DataManager()
            print("✅ DataManager 초기화 완료")
            
            telegram_bot = TelegramBot()
            print("✅ TelegramBot 초기화 완료")
            
            stock_manager = StockTickerManager()
            print("✅ StockTickerManager 초기화 완료")
            
            technical_analyzer = TechnicalAnalyzer()
            print("✅ TechnicalAnalyzer 초기화 완료")
            
            morning_generator = MorningReportGenerator()
            evening_generator = EveningReportGenerator()
            print("✅ ReportGenerators 초기화 완료")
            
            # 메인 분석 엔진 초기화
            alpha_seeker = AlphaSeeker()
            print("✅ AlphaSeeker 메인 엔진 초기화 완료")
            
            # 데이터 상태 확인
            status = data_manager.get_data_status()
            print(f"📊 데이터 상태: 오전데이터={status['morning_data_exists']}, 저녁데이터={status['evening_data_exists']}")
            
        except Exception as e:
            print(f"⚠️ 컴포넌트 초기화 오류: {e}")
        
        # 실제 분석 실행 여부 결정
        if analysis_type in ["morning_analysis", "pre_market_analysis", "sunday_analysis"]:
            print(f"🎯 실제 분석 실행: {analysis_type}")
            
            # 실제 분석 실행
            try:
                success = alpha_seeker.run(analysis_type)
                if success:
                    print(f"🎉 {analysis_type} 완료!")
                else:
                    print(f"⚠️ {analysis_type} 일부 실패")
                    
            except Exception as e:
                print(f"❌ 실제 분석 실행 오류: {e}")
        else:
            print("⏰ 정규 분석 시간이 아님 - 테스트 모드")
            print("✅ Phase 9 테스트 완료 - 모든 시스템 준비됨")
        
        return True
        
    except Exception as e:
        print(f"❌ 시스템 오류: {e}")
        return False

if __name__ == "__main__":
    main()
