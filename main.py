import sys
import os
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('alpha_seeker.log'),
        logging.StreamHandler()
    ]
)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.time_utils import get_analysis_type, get_now_kst
from utils.stock_utils import StockTickerManager
from core.data_manager import DataManager
from core.telegram_bot import TelegramBot
from core.technical import TechnicalAnalyzer
from core.report_generator import MorningReportGenerator, EveningReportGenerator
from core.analyzer import AlphaSeeker

def main():
    current_time_kst = get_now_kst().strftime('%Y-%m-%d %H:%M:%S')
    print(f"🚀 Alpha Seeker v4.3 Enhanced Final 시작 - {current_time_kst} (KST)")
    logging.info(f"Alpha Seeker v4.3 Enhanced Final 시작 - {current_time_kst}")
    
    analysis_type = get_analysis_type()
    print(f"📊 분석 유형: {analysis_type}")
    
    # 테스트 모드 (실제 운영에서는 제거)
    if analysis_type == "general_analysis":
        analysis_type = "pre_market_analysis"  # 테스트용
        print(f"📊 분석 유형: {analysis_type} (테스트 모드)")
    
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
        
        alpha_seeker = AlphaSeeker()
        print("✅ AlphaSeeker 메인 엔진 초기화 완료")

        status = data_manager.get_data_status()
        print(f"📊 데이터 상태: 오전데이터={status['morning_data_exists']}, 저녁데이터={status['evening_data_exists']}")

        if analysis_type in ["morning_analysis", "pre_market_analysis", "sunday_analysis"]:
            print(f"🎯 실제 분석 실행: {analysis_type}")
            logging.info(f"분석 실행 시작: {analysis_type}")
            
            success = alpha_seeker.run(analysis_type)
            
            if success:
                print(f"🎉 {analysis_type} 완료!")
                logging.info(f"{analysis_type} 성공적으로 완료")
            else:
                print(f"⚠️ {analysis_type} 일부 실패")
                logging.warning(f"{analysis_type} 부분 실패 발생")
        else:
            print("⏰ 정규 분석 시간이 아님 - 테스트 모드")
            print("✅ 모든 시스템 준비됨 - 안정화 완료")
            
    except Exception as e:
        print(f"❌ 시스템 오류: {e}")
        logging.error(f"시스템 오류 발생: {e}", exc_info=True)

if __name__ == "__main__":
    main()
