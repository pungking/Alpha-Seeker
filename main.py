import sys
import os
import logging
from datetime import datetime


# 로깅 설정 (최우선)
def setup_logging():
    """고급 로깅 시스템 설정"""
    log_filename = f"alpha_seeker_{datetime.now().strftime('%Y%m%d')}.log"
    
    # 로그 디렉터리 생성
    os.makedirs('logs', exist_ok=True)
    log_filepath = f"logs/{log_filename}"
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        handlers=[
            logging.FileHandler(log_filepath, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # 외부 라이브러리 로그 레벨 조정
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    print(f"✅ 로깅 시스템 초기화: {log_filepath}")
    return log_filepath


# 로깅 시스템 최우선 초기화
log_file = setup_logging()
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.time_utils import get_analysis_type, get_now_kst
from utils.stock_utils import StockTickerManager
from core.data_manager import DataManager
from core.telegram_bot import TelegramBot
from core.technical import TechnicalAnalyzer
from core.report_generator import MorningReportGenerator, EveningReportGenerator
from core.analyzer import AlphaSeeker


def main():
    try:
        current_time_kst = get_now_kst().strftime('%Y-%m-%d %H:%M:%S')
        print(f"🚀 Alpha Seeker v4.3 Enhanced Final 시작 - {current_time_kst} (KST)")
        logger.info(f"Alpha Seeker v4.3 Enhanced Final 시작 - {current_time_kst}")
        
        analysis_type = get_analysis_type()
        print(f"📊 분석 유형: {analysis_type}")
        logger.info(f"분석 유형: {analysis_type}")
        
        # 테스트 모드 (실제 운영에서는 제거)
        if analysis_type == "general_analysis":
            analysis_type = "pre_market_analysis"  # 테스트용
            print(f"📊 분석 유형: {analysis_type} (테스트 모드)")
            logger.info(f"테스트 모드 활성화: {analysis_type}")
        
        # 시스템 구성요소 초기화
        logger.info("시스템 구성요소 초기화 시작")
        
        data_manager = DataManager()
        print("✅ DataManager 초기화 완료")
        logger.info("DataManager 초기화 완료")
        
        # 시작 시 자동 백업
        backup_success = data_manager.backup_critical_data()
        if backup_success:
            print("✅ 시작 시 데이터 백업 완료")
        else:
            print("⚠️ 시작 시 데이터 백업 실패")
        
        telegram_bot = TelegramBot()
        print("✅ TelegramBot 초기화 완료")
        logger.info("TelegramBot 초기화 완료")
        
        stock_manager = StockTickerManager()
        print("✅ StockTickerManager 초기화 완료")
        logger.info("StockTickerManager 초기화 완료")
        
        technical_analyzer = TechnicalAnalyzer()
        print("✅ TechnicalAnalyzer 초기화 완료")
        logger.info("TechnicalAnalyzer 초기화 완료")
        
        morning_generator = MorningReportGenerator()
        evening_generator = EveningReportGenerator()
        print("✅ ReportGenerators 초기화 완료")
        logger.info("ReportGenerators 초기화 완료")
        
        alpha_seeker = AlphaSeeker()
        print("✅ AlphaSeeker 메인 엔진 초기화 완료")
        logger.info("AlphaSeeker 메인 엔진 초기화 완료")

        # 데이터 상태 확인
        status = data_manager.get_data_status()
        print(f"📊 데이터 상태: 오전데이터={status['morning_data_exists']}, 저녁데이터={status['evening_data_exists']}")
        logger.info(f"데이터 상태 확인 완료: {status}")

        if analysis_type in ["morning_analysis", "pre_market_analysis", "sunday_analysis"]:
            print(f"🎯 실제 분석 실행: {analysis_type}")
            logger.info(f"분석 실행 시작: {analysis_type}")
            
            success = alpha_seeker.run(analysis_type)
            
            if success:
                print(f"🎉 {analysis_type} 완료!")
                logger.info(f"{analysis_type} 성공적으로 완료")
                
                # 완료 후 백업
                data_manager.backup_critical_data()
                
            else:
                print(f"⚠️ {analysis_type} 일부 실패")
                logger.warning(f"{analysis_type} 부분 실패 발생")
        else:
            print("⏰ 정규 분석 시간이 아님 - 테스트 모드")
            logger.info("정규 분석 시간이 아님 - 대기 상태")
            print("✅ 모든 시스템 준비됨 - 안정화 완료")
            
    except Exception as e:
        print(f"❌ 시스템 오류: {e}")
        logger.error(f"시스템 심각한 오류 발생: {e}", exc_info=True)
        
        # 긴급 상황 알림
        try:
            emergency_bot = TelegramBot()
            emergency_msg = f"""🚨🚨🚨 Alpha Seeker 시스템 오류 🚨🚨🚨
⏰ {datetime.now().strftime('%H:%M:%S')} KST

❌ 심각한 오류 발생:
{str(e)[:200]}

🔧 즉시 확인 필요:
• 시스템 로그 점검: {log_file}
• 환경변수 확인
• 네트워크 연결 상태
• API 키 상태

📱 담당자 즉시 대응 바랍니다!
🤖 Alpha Seeker v4.3 Emergency Alert"""
            
            emergency_bot.send_message(emergency_msg, emergency=True)
            
        except Exception as alert_error:
            print(f"❌ 긴급 알림 전송도 실패: {alert_error}")
            logger.critical(f"긴급 알림 전송 실패: {alert_error}")


if __name__ == "__main__":
    main()
