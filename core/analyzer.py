import os
import logging
from datetime import datetime
from dotenv import load_dotenv

from .technical import TechnicalAnalyzer
from .data_manager import DataManager
from .telegram_bot import TelegramBot
from .report_generator import MorningReportGenerator, EveningReportGenerator, SundayReportGenerator
from .realtime_monitor import RealtimeRiskMonitor
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
        
        # 실시간 모니터링
        self.realtime_monitor = None
        
        # 포트폴리오 관리 설정
        self.portfolio_balance = 100000  # 기본 포트폴리오 규모
        self.max_position_size = 0.15    # 종목당 최대 15%
        self.max_total_exposure = 0.8    # 전체 노출 최대 80%
        
        print("✅ AlphaSeeker Enhanced Final 메인 엔진 초기화 완료")
    
    def check_emergency_conditions(self, evening_result):
        """긴급 상황 감지"""
        emergency_conditions = []
        
        # 1. 높은 실패율 (80% 이상 실패)
        failed_count = evening_result.get('failed_count', 0)
        total_count = evening_result.get('morning_total', 1)
        failure_rate = failed_count / total_count if total_count > 0 else 0
        
        if failure_rate > 0.8:
            emergency_conditions.append(f"데이터 수집 실패율 {failure_rate*100:.0f}%")
        
        # 2. 전 종목 제거 (100% 제거)
        maintained_count = len(evening_result.get('maintained', []))
        removed_count = len(evening_result.get('removed', []))
        
        if maintained_count == 0 and total_count > 0:
            emergency_conditions.append("모든 추천 종목이 제거됨")
        
        # 3. 대규모 갭 발생 (평균 갭 > 10%)
        detailed_analysis = evening_result.get('detailed_analysis', {})
        large_gaps = []
        
        for ticker, data in detailed_analysis.items():
            gap_pct = abs(data.get('gap_pct', 0))
            if gap_pct > 10:
                large_gaps.append(f"{ticker}({gap_pct:+.1f}%)")
        
        if len(large_gaps) >= 3:
            emergency_conditions.append(f"대규모 갭 발생: {', '.join(large_gaps[:3])}")
        
        # 4. 시스템 오류 감지
        if evening_result.get('system_error'):
            emergency_conditions.append("시스템 치명적 오류 발생")
        
        return emergency_conditions
    
    def calculate_position_size(self, ticker, score, confidence=1.0):
        """신뢰도 기반 포지션 크기 계산"""
        try:
            # 기본 포지션 크기 (점수 기반)
            base_position = self.max_position_size * (score / 10.0)
            
            # 신뢰도 조정
            adjusted_position = base_position * confidence
            
            # 절대 최대치 적용
            final_position = min(adjusted_position, 0.20)  # 절대 최대 20%
            
            position_value = self.portfolio_balance * final_position
            
            logging.info(f"{ticker} 포지션 크기: {final_position:.1%} (${position_value:,.0f})")
            
            return {
                'position_pct': final_position,
                'position_value': position_value,
                'score_factor': score / 10.0,
                'confidence_factor': confidence
            }
            
        except Exception as e:
            logging.error(f"포지션 크기 계산 오류: {e}")
            return {
                'position_pct': 0.05,  # 기본 5%
                'position_value': self.portfolio_balance * 0.05,
                'score_factor': 0.5,
                'confidence_factor': 0.5
            }
    
    def calculate_risk_metrics(self, analysis_result):
        """리스크 메트릭 계산"""
        try:
            if not analysis_result:
                return {'risk_level': '알 수 없음', 'risk_score': 50}
            
            maintained = analysis_result.get('maintained', [])
            removed = analysis_result.get('removed', [])
            failed_count = analysis_result.get('failed_count', 0)
            
            total_analyzed = len(maintained) + len(removed) + failed_count
            
            if total_analyzed == 0:
                return {'risk_level': '데이터 없음', 'risk_score': 50}
            
            # 리스크 점수 계산
            removal_rate = len(removed) / total_analyzed
            failure_rate = failed_count / total_analyzed
            
            # 갭 리스크 추가 고려
            detailed_analysis = analysis_result.get('detailed_analysis', {})
            high_gap_count = 0
            for data in detailed_analysis.values():
                gap_pct = abs(data.get('gap_pct', 0))
                if gap_pct > 5:  # 5% 이상 갭
                    high_gap_count += 1
            
            gap_risk = high_gap_count / total_analyzed if total_analyzed > 0 else 0
            
            # 종합 리스크 점수
            risk_score = (removal_rate * 0.4 + failure_rate * 0.3 + gap_risk * 0.3) * 100
            
            # 리스크 등급 결정
            if risk_score <= 15:
                risk_level = "🟢 저위험"
            elif risk_score <= 35:
                risk_level = "🟡 보통위험"
            elif risk_score <= 60:
                risk_level = "🔴 고위험"
            else:
                risk_level = "💥 매우 고위험"
            
            return {
                'risk_level': risk_level,
                'risk_score': round(risk_score, 1),
                'removal_rate': round(removal_rate * 100, 1),
                'failure_rate': round(failure_rate * 100, 1),
                'gap_risk': round(gap_risk * 100, 1),
                'maintained_count': len(maintained)
            }
            
        except Exception as e:
            logging.error(f"리스크 메트릭 계산 오류: {e}")
            return {'risk_level': '계산 오류', 'risk_score': 50}
    
    def get_perplexity_analysis(self):
        """Perplexity AI 분석 및 종목 추출 (기존 로직 유지)"""
        if not self.perplexity_key:
            print("❌ Perplexity API 키가 설정되지 않았습니다.")
            logging.warning("Perplexity API 키 없음")
            return None
            
        try:
            print("🧠 Perplexity AI 실시간 분석 시작...")
            logging.info("Perplexity AI 분석 시작")
            
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
                logging.info("Perplexity AI 분석 완료")
                
                # 동적으로 티커 추출
                extracted_tickers = self.ticker_manager.extract_tickers_from_text(content)
                
                if not extracted_tickers:
                    print("⚠️ 유효한 티커를 추출하지 못했습니다.")
                    logging.warning("티커 추출 실패")
                    return None
                
                return {
                    'analysis': content,
                    'extracted_tickers': extracted_tickers,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                print(f"❌ Perplexity API 오류: {response.status_code}")
                logging.error(f"Perplexity API 오류: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Perplexity 분석 오류: {e}")
            logging.error(f"Perplexity 분석 오류: {e}")
            return None
    
    def analyze_extracted_stocks(self, tickers):
        """추출된 종목들 기술적 분석 (포지션 크기 계산 추가)"""
        print(f"📊 {len(tickers)}개 종목 기술적 분석 시작...")
        logging.info(f"{len(tickers)}개 종목 분석 시작")
        
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
            
            # 포지션 크기 계산
            position_info = self.calculate_position_size(
                ticker, 
                technical_result.get('score', 5),
                technical_result.get('confidence', 1.0)
            )
            
            # 통합 결과
            analysis_results[ticker] = {
                **basic_info,
                **technical_result,
                **position_info,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            import time
            time.sleep(0.8)  # API 제한 방지
        
        print(f"✅ {len(analysis_results)}개 종목 분석 완료")
        logging.info(f"{len(analysis_results)}개 종목 분석 완료")
        return analysis_results
    
    def run_morning_analysis(self):
        """오전 분석 실행 (기존 로직 유지)"""
        print("🌅 오전 헤지펀드급 분석 시작")
        logging.info("오전 분석 시작")
        
        try:
            # 1. AI 분석 및 종목 추출
            ai_result = self.get_perplexity_analysis()
            if not ai_result or not ai_result.get('extracted_tickers'):
                error_msg = f"""
🌅 Alpha Seeker Enhanced Final 오전 분석 실패
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')} (KST)

❌ Perplexity AI 분석 실패 또는 종목 추출 실패
🔄 다음 분석: 오후 23:30
🤖 Alpha Seeker v4.3 Enhanced Final
"""
                self.telegram_bot.send_message(error_msg)
                return False
            
            # 2. 추출된 종목들 기술적 분석
            stock_analysis = self.analyze_extracted_stocks(ai_result['extracted_tickers'])
            if not stock_analysis:
                error_msg = f"""
🌅 Alpha Seeker Enhanced Final 오전 분석
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')} (KST)

⚠️ 기술적 분석 실패
🔄 다음 분석: 오후 23:30
🤖 Alpha Seeker v4.3 Enhanced Final
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
                logging.info(f"오전 분석 성공: {len(stock_analysis)}개 종목")
            
            return success
            
        except Exception as e:
            print(f"❌ 오전 분석 오류: {e}")
            logging.error(f"오전 분석 오류: {e}", exc_info=True)
            return False
    
    def run_evening_recheck(self):
        """저녁 재검토 실행 + 실시간 모니터링 시작"""
        print("🌙 저녁 프리마켓 재검토 시작")
        logging.info("저녁 재검토 시작")
        
        try:
            # 1. 오전 데이터 로드
            morning_data = self.data_manager.load_morning_data()
            if not morning_data:
                error_msg = f"""
🌙 Alpha Seeker Enhanced Final 프리마켓 분석
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')} (KST)

⚠️ 오전 데이터 없음
🔄 다음 분석: 내일 06:07
🤖 Alpha Seeker v4.3 Enhanced Final
"""
                self.telegram_bot.send_message(error_msg)
                return False
            
            morning_stocks = morning_data.get('stock_analysis', {})
            if not morning_stocks:
                error_msg = f"""
🌙 Alpha Seeker Enhanced Final 프리마켓 분석  
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')} (KST)

⚠️ 오전 추천 종목 없음
🔄 다음 분석: 내일 06:07
🤖 Alpha Seeker v4.3 Enhanced Final
"""
                self.telegram_bot.send_message(error_msg)
                return False
            
            # 2. 재검토 실행
            evening_result = self.recheck_morning_picks(morning_stocks)
            
            # 3. 긴급 상황 체크
            emergency_conditions = self.check_emergency_conditions(evening_result)
            
            if emergency_conditions:
                emergency_msg = f"""
🚨🚨🚨 Alpha Seeker 긴급 상황 🚨🚨🚨
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')} (KST)

⛔ 긴급 사항:
{chr(10).join(f'• {condition}' for condition in emergency_conditions)}

🔧 즉시 확인 필요:
• 시스템 로그 점검
• API 키 상태 확인  
• 네트워크 연결 상태
• 데이터 소스 정상성
• 포지션 긴급 재검토

📞 담당자 즉시 대응 바랍니다.
🤖 Alpha Seeker v4.3 Enhanced Final Emergency
"""
                # 긴급 알림 전송
                self.telegram_bot.send_message(emergency_msg, emergency=True)
            
            # 4. 리스크 메트릭 계산
            risk_metrics = self.calculate_risk_metrics(evening_result)
            evening_result['risk_metrics'] = risk_metrics
            
            # 5. 결과 저장
            self.data_manager.save_evening_data(evening_result)
            
            # 6. 리포트 생성 및 전송
            report = self.evening_generator.generate(evening_result)
            
            # 위험도에 따른 알림 등급 결정
            risk_level = risk_metrics.get('risk_level', '알 수 없음')
            is_urgent = '고위험' in risk_level or '매우 고위험' in risk_level
            
            success = self.telegram_bot.send_message(report, urgent=is_urgent)
            
            # 7. 실시간 모니터링 시작
            maintained = evening_result.get('maintained', [])
            if success and maintained and not emergency_conditions:
                print("🔍 실시간 위험 모니터링 시작...")
                logging.info("실시간 모니터링 시작")
                
                self.realtime_monitor = RealtimeRiskMonitor(
                    self.telegram_bot, 
                    maintained  # 유지된 종목들만 모니터링
                )
                
                monitor_started = self.realtime_monitor.start_monitoring()
                
                if monitor_started:
                    # 모니터링 시작 알림
                    monitor_msg = f"""
🔍 Alpha Seeker 실시간 모니터링 활성화
⏰ {datetime.now().strftime('%H:%M')} KST

📊 모니터링 종목: {len(maintained)}개
{', '.join(maintained)}

🚨 긴급 알림 조건:
• 급락 5% 이상 / 급등 10% 이상
• RSI 극한 과매도/과매수 (20/80)
• 거래량 3배 급증 / 50% 급감
• VIX 30 이상 급등
• 주요 지지선/저항선 이탈

⚡ 24시간 자동 모니터링 시작
🔄 알림 중복 방지: 30분 간격
🤖 Alpha Seeker v4.3 Enhanced Final
"""
                    self.telegram_bot.send_message(monitor_msg)
                    logging.info(f"실시간 모니터링 활성화: {maintained}")
            
            if success:
                maintained_count = len(maintained)
                removed_count = len(evening_result.get('removed', []))
                failed_count = evening_result.get('failed_count', 0)
                risk_level = risk_metrics.get('risk_level', '알 수 없음')
                
                print(f"🎉 저녁 재검토 완료: 유지 {maintained_count}개, 제외 {removed_count}개, 실패 {failed_count}개")
                print(f"📊 리스크 수준: {risk_level}")
                print(f"🔍 실시간 모니터링: {'활성화' if maintained_count > 0 else '대상 없음'}")
                
                logging.info(f"저녁 재검토 완료: 유지={maintained_count}, 제외={removed_count}, 실패={failed_count}, 리스크={risk_level}")
            
            # 부분 성공도 성공으로 처리
            total_processed = len(evening_result.get('maintained', [])) + len(evening_result.get('removed', []))
            return total_processed > 0
            
        except Exception as e:
            print(f"❌ 저녁 재검토 오류: {e}")
            logging.error(f"저녁 재검토 오류: {e}", exc_info=True)
            
            # 시스템 오류도 긴급 알림
            error_msg = f"""
🚨 Alpha Seeker 시스템 오류 🚨
⏰ {datetime.now().strftime('%H:%M')} KST
오류: {str(e)[:200]}

즉시 시스템 점검 필요!
🤖 Alpha Seeker v4.3 Enhanced Final
"""
            self.telegram_bot.send_message(error_msg, emergency=True)
            return False
    
    def recheck_morning_picks(self, morning_stocks):
        """오전 종목들 재검토 (기존 로직 강화)"""
        print(f"🔄 {len(morning_stocks)}개 종목 재검토 중...")
        logging.info(f"{len(morning_stocks)}개 종목 재검토 시작")
        
        maintained = []
        removed = []
        recheck_results = {}
        failed_count = 0
        
        for ticker, morning_data in morning_stocks.items():
            print(f"📊 {ticker} 재분석...")
            
            # 강화된 기술적 분석 (재시도 로직)
            current_analysis = None
            for attempt in range(3):  # 최대 3회 재시도
                try:
                    current_analysis = self.technical_analyzer.analyze(ticker)
                    if current_analysis:
                        break
                    print(f"⚠️ {ticker} 데이터 없음 (시도 {attempt+1}/3)")
                except Exception as e:
                    print(f"⚠️ {ticker} 분석 오류 (시도 {attempt+1}/3): {str(e)}")
                    import time
                    time.sleep(2)
            
            # 분석 실패 시 폴백 처리 (더 정교함)
            if not current_analysis:
                failed_count += 1
                morning_score = morning_data.get('score', 0)
                morning_confidence = morning_data.get('confidence', 0.5)
                
                # 폴백 결정 로직 강화
                fallback_threshold = 6.5 if morning_confidence > 0.7 else 7.0
                
                if morning_score >= fallback_threshold:
                    print(f"🔄 {ticker} 오전 데이터 기반 유지 (점수: {morning_score}/10, 신뢰도: {morning_confidence:.1f})")
                    maintained.append(ticker)
                    recheck_results[ticker] = {
                        **morning_data,
                        'recheck_status': 'fallback_maintain',
                        'maintain': True,
                        'removal_reason': '',
                        'fallback_reason': f'높은 오전 점수 ({morning_score}/10) + 신뢰도 ({morning_confidence:.1f})'
                    }
                else:
                    print(f"❌ {ticker} 데이터 실패로 제거")
                    removed.append((ticker, "데이터 수집 실패"))
                continue
            
            # 정상 분석된 경우 기존 로직 수행
            morning_price = morning_data.get('current_price', 0)
            current_price = current_analysis.get('current_price', 0)
            
            if morning_price > 0:
                gap_pct = ((current_price - morning_price) / morning_price) * 100
            else:
                gap_pct = 0
            
            # 포지션 크기 재계산
            position_info = self.calculate_position_size(
                ticker, 
                current_analysis.get('score', 5),
                current_analysis.get('confidence', 1.0)
            )
            
            # 유지/제거 결정 (더 정교한 로직)
            should_maintain = True
            removal_reason = ""
            
            # 1. 큰 갭 발생 (임계값 상향 조정)
            if abs(gap_pct) > 8:  # 8% 이상으로 상향 조정
                should_maintain = False
                removal_reason = f"큰 갭 발생 ({gap_pct:+.1f}%)"
            # 2. 기술적 점수 하락
            elif current_analysis.get('score', 0) < 4:
                should_maintain = False
                removal_reason = f"기술점수 하락 ({current_analysis.get('score', 0)}/10)"
            # 3. 부정적 신호 증가
            elif any("데드크로스" in str(signal) for signal in current_analysis.get('signals', [])):
                should_maintain = False
                removal_reason = "부정적 기술적 신호"
            # 4. RSI 극한 상황 (추가)
            elif current_analysis.get('rsi', 50) < 15:  # RSI 15 이하 극한 과매도
                should_maintain = False
                removal_reason = f"RSI 극한 과매도 ({current_analysis.get('rsi', 0):.1f})"
            # 5. 신뢰도 급락 (추가)
            elif current_analysis.get('confidence', 1.0) < 0.3:
                should_maintain = False
                removal_reason = f"신뢰도 급락 ({current_analysis.get('confidence', 0)*100:.0f}%)"
            
            # 결과 기록
            recheck_results[ticker] = {
                **current_analysis,
                **position_info,
                'morning_price': morning_price,
                'gap_pct': round(gap_pct, 1),
                'maintain': should_maintain,
                'removal_reason': removal_reason,
                'recheck_status': 'success'
            }
            
            if should_maintain:
                maintained.append(ticker)
            else:
                removed.append((ticker, removal_reason))
        
        # 결과 요약
        total_count = len(morning_stocks)
        success_rate = ((total_count - failed_count) / total_count * 100) if total_count > 0 else 0
        
        print(f"✅ 재검토 완료: 성공률 {success_rate:.1f}% ({total_count-failed_count}/{total_count})")
        logging.info(f"재검토 완료: 성공률={success_rate:.1f}%, 유지={len(maintained)}, 제외={len(removed)}, 실패={failed_count}")
        
        return {
            'maintained': maintained,
            'removed': removed,
            'detailed_analysis': recheck_results,
            'morning_total': total_count,
            'failed_count': failed_count,
            'success_rate': round(success_rate, 1),
            'timestamp': datetime.now().isoformat()
        }
    
    def run_sunday_analysis(self):
        """일요일 주간 분석 (기존 로직 유지)"""
        print("📊 일요일 주간 전략 분석")
        logging.info("일요일 주간 분석 시작")
        
        try:
            sunday_data = {
                'analysis_type': 'weekly_strategy',
                'timestamp': datetime.now().isoformat()
            }
            
            report = self.sunday_generator.generate(sunday_data)
            success = self.telegram_bot.send_message(report)
            
            if success:
                print("🎉 일요일 주간 분석 완료")
                logging.info("일요일 주간 분석 완료")
            
            return success
            
        except Exception as e:
            print(f"❌ 일요일 분석 오류: {e}")
            logging.error(f"일요일 분석 오류: {e}")
            return False
    
    def stop_realtime_monitoring(self):
        """실시간 모니터링 중지"""
        if self.realtime_monitor:
            self.realtime_monitor.stop_monitoring()
            self.realtime_monitor = None
            logging.info("실시간 모니터링 중지 완료")
    
    def run(self, analysis_type):
        """메인 실행 메서드"""
        print(f"🎯 Alpha Seeker Enhanced Final 분석 시작: {analysis_type}")
        logging.info(f"분석 시작: {analysis_type}")
        
        if analysis_type == "morning_analysis":
            return self.run_morning_analysis()
        elif analysis_type == "pre_market_analysis":
            return self.run_evening_recheck()
        elif analysis_type == "sunday_analysis":
            return self.run_sunday_analysis()
        else:
            print("⏰ 정규 분석 시간이 아닙니다")
            logging.info("정규 분석 시간이 아님")
            return False

print("✅ AlphaSeeker Enhanced Final (포지션 관리 + 리스크 메트릭 + 실시간 모니터링)")
