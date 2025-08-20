import os
from datetime import datetime
from dotenv import load_dotenv

from .technical import TechnicalAnalyzer
from .data_manager import DataManager
from .telegram_bot import TelegramBot
from .report_generator import MorningReportGenerator, EveningReportGenerator, SundayReportGenerator
from utils.stock_utils import StockTickerManager

load_dotenv()

class AlphaSeeker:
    def __init__(self):
        # API 키 설정
        self.perplexity_key = os.getenv('PERPLEXITY_API_KEY')
        
        # 컴포넌트 초기화
        self.ticker_manager = StockTickerManager()
        self.technical_analyzer = TechnicalAnalyzer()
        self.data_manager = DataManager()
        self.telegram_bot = TelegramBot()
        
        # 리포트 생성기
        self.morning_generator = MorningReportGenerator()
        self.evening_generator = EveningReportGenerator()
        self.sunday_generator = SundayReportGenerator()
        
        print("✅ AlphaSeeker 메인 엔진 초기화 완료")
        
    def get_perplexity_analysis(self):
        """Perplexity AI 분석 및 종목 추출"""
        if not self.perplexity_key:
            print("❌ Perplexity API 키가 설정되지 않았습니다.")
            print("📋 .env 파일에 PERPLEXITY_API_KEY를 설정해주세요.")
            print("🔗 API 키 발급: https://www.perplexity.ai/settings/api")
            return None
            
        try:
            print("🧠 Perplexity AI 실시간 분석 시작...")
            
            import requests
            url = "https://api.perplexity.ai/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.perplexity_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "llama-3.1-sonar-large-128k-online",
                "messages": [
                    {
                        "role": "system",
                        "content": """당신은 미국 주식 전문가입니다. 
현재 시점에서 투자할 만한 구체적인 미국 주식 종목들을 추천해주세요.
반드시 정확한 티커 심볼과 함께 추천 이유를 제시해주세요."""
                    },
                    {
                        "role": "user",
                        "content": f"""오늘 {datetime.now().strftime('%Y년 %m월 %d일')} 기준으로:

1. 최근 뉴스나 실적으로 주목받는 종목들
2. 기술적 분석상 매수 신호가 나오는 종목들  
3. 1-3개월 스윙트레이딩에 적합한 종목들

각 종목의 정확한 티커 심볼과 추천 이유를 구체적으로 제시해주세요.
최소 5개, 최대 10개 종목을 추천해주세요."""
                    }
                ],
                "temperature": 0.2,
                "max_tokens": 2000
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content']
                print("✅ Perplexity AI 분석 완료")
                
                # 동적으로 티커 추출
                extracted_tickers = self.ticker_manager.extract_tickers_from_text(content)
                
                if not extracted_tickers:
                    print("⚠️ 유효한 티커를 추출하지 못했습니다.")
                    return None
                
                return {
                    'analysis': content,
                    'extracted_tickers': extracted_tickers,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                print(f"❌ Perplexity API 오류: {response.status_code}")
                print(f"   응답: {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"❌ Perplexity 분석 오류: {e}")
            return None
    
    def send_api_key_required_message(self):
        """API 키 필요 메시지 전송"""
        error_message = f"""
🚨 **Alpha Seeker 분석 중단**
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')} (KST)

❌ **Perplexity API 키 없음**
AI 기반 실시간 종목 분석을 위해서는 API 키가 필요합니다.

🔧 **해결 방법**:
1. https://www.perplexity.ai/settings/api 에서 API 키 발급
2. .env 파일에 `PERPLEXITY_API_KEY=발급받은키` 추가
3. 또는 GitHub Secrets에 키 등록

⚠️ **중요**: API 키 없이는 가짜 데이터를 제공하지 않습니다.
실제 투자 결정에 도움이 되는 정확한 분석만 제공합니다.

⏰ **다음 분석**: API 키 설정 후 자동 재개
🤖 Alpha Seeker v4.3 - 정직한 분석 시스템
"""
        
        return self.telegram_bot.send_message(error_message)
    
    def analyze_extracted_stocks(self, tickers):
        """추출된 종목들 기술적 분석"""
        print(f"📊 {len(tickers)}개 종목 기술적 분석 시작...")
        
        analysis_results = {}
        
        for ticker in tickers[:8]:  # 최대 8개 종목
            print(f"🔍 {ticker} 분석 중...")
            
            # 기본 정보
            basic_info = self.ticker_manager.get_stock_basic_info(ticker)
            if not basic_info:
                continue
                
            # 기술적 분석
            technical_result = self.technical_analyzer.analyze(ticker)
            if not technical_result:
                continue
            
            # 통합 결과
            analysis_results[ticker] = {
                **basic_info,
                **technical_result,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            import time
            time.sleep(0.8)  # API 제한 방지
        
        print(f"✅ {len(analysis_results)}개 종목 분석 완료")
        return analysis_results
    
    def run_morning_analysis(self):
        """오전 분석 실행"""
        print("🌅 오전 헤지펀드급 분석 시작")
        
        try:
            # 1. AI 분석 및 종목 추출
            ai_result = self.get_perplexity_analysis()
            if not ai_result:
                print("❌ Perplexity AI 분석 실패 - API 키 필요 메시지 전송")
                self.send_api_key_required_message()
                return False
            
            if not ai_result['extracted_tickers']:
                error_msg = f"""
🌅 **Alpha Seeker 오전 분석**
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')} (KST)

⚠️ **유효한 종목 발견 안됨**
AI 분석은 완료되었으나 투자 가능한 종목을 찾지 못했습니다.
시장 상황을 지속 모니터링하겠습니다.

🔄 **다음 분석**: 오후 22:13
🤖 Alpha Seeker v4.3
"""
                self.telegram_bot.send_message(error_msg)
                return False
            
            # 2. 추출된 종목들 기술적 분석
            stock_analysis = self.analyze_extracted_stocks(ai_result['extracted_tickers'])
            if not stock_analysis:
                error_msg = f"""
🌅 **Alpha Seeker 오전 분석**
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')} (KST)

⚠️ **기술적 분석 실패**
종목은 추출되었으나 기술적 분석에서 오류가 발생했습니다.

🔄 **다음 분석**: 오후 22:13
🤖 Alpha Seeker v4.3
"""
                self.telegram_bot.send_message(error_msg)
                return False
            
            # 3. 결과 저장
            morning_data = {
                'ai_analysis': ai_result,
                'stock_analysis': stock_analysis,
                'total_analyzed': len(stock_analysis),
                'timestamp': datetime.now().isoformat()
            }
            
            self.data_manager.save_morning_data(morning_data)
            
            # 4. 리포트 생성 및 전송
            report = self.morning_generator.generate(morning_data)
            success = self.telegram_bot.send_message(report)
            
            if success:
                print(f"🎉 오전 분석 완료: {len(stock_analysis)}개 종목")
            
            return success
            
        except Exception as e:
            print(f"❌ 오전 분석 오류: {e}")
            error_msg = f"""
🌅 **Alpha Seeker 오전 분석 오류**
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')} (KST)

❌ **시스템 오류**
{str(e)}

🔄 **다음 분석**: 오후 22:13
🤖 Alpha Seeker v4.3
"""
            self.telegram_bot.send_message(error_msg)
            return False
    
    def run_evening_recheck(self):
        """저녁 재검토 실행"""
        print("🌙 저녁 프리마켓 재검토 시작")
        
        try:
            # 1. 오전 데이터 로드
            morning_data = self.data_manager.load_morning_data()
            if not morning_data:
                
                error_msg = f"""
🌙 **Alpha Seeker 프리마켓 분석**
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')} (KST)

⚠️ **오전 데이터 없음**
재검토할 오전 추천 종목이 없습니다.

🔄 **다음 분석**: 내일 06:07
🤖 Alpha Seeker v4.3
"""
                self.telegram_bot.send_message(error_msg)
                return False
            
            morning_stocks = morning_data.get('stock_analysis', {})
            if not morning_stocks:
                error_msg = f"""
🌙 **Alpha Seeker 프리마켓 분석**
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')} (KST)

⚠️ **오전 추천 종목 없음**
재검토할 데이터가 없습니다.

🔄 **다음 분석**: 내일 06:07
🤖 Alpha Seeker v4.3
"""
                self.telegram_bot.send_message(error_msg)
                return False
            
            # 2. 재검토 실행
            evening_result = self.recheck_morning_picks(morning_stocks)
            
            # 3. 결과 저장
            self.data_manager.save_evening_data(evening_result)
            
            # 4. 리포트 생성 및 전송
            report = self.evening_generator.generate(evening_result)
            success = self.telegram_bot.send_message(report)
            
            if success:
                maintained = len(evening_result.get('maintained', []))
                removed = len(evening_result.get('removed', []))
                print(f"🎉 저녁 재검토 완료: 유지 {maintained}개, 제외 {removed}개")
            
            return success
            
        except Exception as e:
            print(f"❌ 저녁 재검토 오류: {e}")
            error_msg = f"""
🌙 **Alpha Seeker 프리마켓 재검토 오류**
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')} (KST)

❌ **시스템 오류**
{str(e)}

🔄 **다음 분석**: 내일 06:07
🤖 Alpha Seeker v4.3
"""
            self.telegram_bot.send_message(error_msg)
            return False
    
    def recheck_morning_picks(self, morning_stocks):
        """오전 종목들 재검토"""
        print(f"🔄 {len(morning_stocks)}개 종목 재검토 중...")
        
        maintained = []
        removed = []
        recheck_results = {}
        
        for ticker, morning_data in morning_stocks.items():
            print(f"📊 {ticker} 재분석...")
            
            # 현재 기술적 분석
            current_analysis = self.technical_analyzer.analyze(ticker)
            if not current_analysis:
                removed.append((ticker, "데이터 수집 실패"))
                continue
            
            # 변화 분석
            morning_price = morning_data.get('current_price', 0)
            current_price = current_analysis.get('current_price', 0)
            
            if morning_price > 0:
                gap_pct = ((current_price - morning_price) / morning_price) * 100
            else:
                gap_pct = 0
            
            # 유지/제거 결정
            should_maintain = True
            removal_reason = ""
            
            # 큰 갭 발생
            if abs(gap_pct) > 7:
                should_maintain = False
                removal_reason = f"큰 갭 발생 ({gap_pct:+.1f}%)"
            
            # 기술적 점수 하락
            elif current_analysis.get('score', 0) < 4:
                should_maintain = False
                removal_reason = f"기술점수 하락 ({current_analysis.get('score', 0)}/10)"
            
            # 부정적 신호 증가
            elif any("데드크로스" in str(signal) for signal in current_analysis.get('signals', [])):
                should_maintain = False
                removal_reason = "부정적 기술적 신호"
            
            # 결과 기록
            recheck_results[ticker] = {
                **current_analysis,
                'morning_price': morning_price,
                'gap_pct': round(gap_pct, 1),
                'maintain': should_maintain,
                'removal_reason': removal_reason
            }
            
            if should_maintain:
                maintained.append(ticker)
            else:
                removed.append((ticker, removal_reason))
        
        return {
            'maintained': maintained,
            'removed': removed,
            'detailed_analysis': recheck_results,
            'morning_total': len(morning_stocks),
            'timestamp': datetime.now().isoformat()
        }
    
    def run_sunday_analysis(self):
        """일요일 주간 분석"""
        print("📊 일요일 주간 전략 분석")
        
        try:
            sunday_data = {
                'analysis_type': 'weekly_strategy',
                'timestamp': datetime.now().isoformat()
            }
            
            report = self.sunday_generator.generate(sunday_data)
            success = self.telegram_bot.send_message(report)
            
            if success:
                print("🎉 일요일 주간 분석 완료")
            
            return success
            
        except Exception as e:
            print(f"❌ 일요일 분석 오류: {e}")
            return False
    
    def run(self, analysis_type):
        """메인 실행 메서드"""
        print(f"🎯 Alpha Seeker 분석 시작: {analysis_type}")
        
        if analysis_type == "morning_analysis":
            return self.run_morning_analysis()
        elif analysis_type == "pre_market_analysis":
            return self.run_evening_recheck()
        elif analysis_type == "sunday_analysis":
            return self.run_sunday_analysis()
        else:
            print("⏰ 정규 분석 시간이 아닙니다")
            return False

print("✅ AlphaSeeker 메인 엔진 모듈 로드 완료")
