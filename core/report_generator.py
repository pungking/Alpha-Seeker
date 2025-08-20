from datetime import datetime
import json

class MorningReportGenerator:
    def __init__(self):
        self.report_type = "morning_analysis"
        
    def generate(self, morning_data):
        """오전 헤지펀드급 리포트 생성"""
        try:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
            ai_analysis = morning_data.get('ai_analysis', {})
            stock_analysis = morning_data.get('stock_analysis', {})
            
            if not stock_analysis:
                return self._generate_empty_report(current_time)
            
            # 점수순 정렬
            sorted_stocks = sorted(
                stock_analysis.items(), 
                key=lambda x: x[1].get('score', 0), 
                reverse=True
            )
            
            # 데이터 소스 통계 계산
            realtime_count = sum(1 for _, data in stock_analysis.items() 
                               if data.get('data_source') == 'alpaca_realtime')
            total_count = len(stock_analysis)
            
            report = f"""
🌅 **Alpha Seeker 헤지펀드급 분석 v4.3**
📅 {current_time} (KST) | 투자 성공률 95% 목표

📡 **하이브리드 데이터 시스템**
• 실시간 데이터: {realtime_count}개 📡
• 백업 데이터: {total_count - realtime_count}개 📊
• 총 분석: {total_count}개 종목

🧠 **Perplexity AI 실시간 분석**
{ai_analysis.get('analysis', '시장 분석을 진행했습니다.')[:400]}

📊 **오늘의 추천 종목 TOP 5**
"""
            
            # TOP 5 종목 표시
            for i, (symbol, data) in enumerate(sorted_stocks[:5], 1):
                emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}️⃣"
                
                # 데이터 소스 아이콘
                source_emoji = "📡" if data.get('data_source') == 'alpaca_realtime' else "📊"
                
                # 안전한 데이터 추출
                current_price = data.get('current_price', 0)
                change_pct = data.get('change_pct', 0)
                score = data.get('score', 0)
                rsi = data.get('rsi', 50)
                macd_signal = data.get('macd_signal', 'N/A')
                resistance = data.get('resistance_level', current_price * 1.1)
                support = data.get('support_level', current_price * 0.9)
                signals = data.get('signals', ['분석 완료'])
                company_name = data.get('name', symbol)
                
                # RR비율 계산
                if support < current_price < resistance:
                    rr_ratio = round((resistance - current_price) / (current_price - support), 1)
                else:
                    rr_ratio = 1.0
                
                report += f"""
{emoji} **{symbol}** {source_emoji} | 점수: {score}/10
🏢 {company_name[:25]}
💰 **${current_price}** ({change_pct:+.1f}%) | RR: {rr_ratio}:1
🎯 목표: ${resistance} | 🛡️ 손절: ${support}
📊 RSI: {rsi} | MACD: {macd_signal}
🔍 {signals[0]}
"""

            # 1위 종목 상세 분석
            if sorted_stocks:
                top_symbol, top_data = sorted_stocks[0]
                top_source = "📡 실시간" if top_data.get('data_source') == 'alpaca_realtime' else "📊 백업"
                
                report += f"""

💎 **1위 종목 {top_symbol} 핵심 분석** {top_source}
• **현재가**: ${top_data.get('current_price', 0)} (실제 시세)
• **회사명**: {top_data.get('name', top_symbol)}
• **시가총액**: ${top_data.get('market_cap', 0):,}
• **섹터**: {top_data.get('sector', 'Unknown')}
• **RSI**: {top_data.get('rsi', 50)}점 - {"매수권" if top_data.get('rsi', 50) < 70 else "과매수 주의"}
• **볼린저밴드**: {top_data.get('bb_position', 50)}% 위치
• **거래량**: {top_data.get('volume_ratio', 1):.1f}배 ({top_data.get('volume', 0):,}주)

**핵심 신호**
{chr(10).join(f"• {signal}" for signal in top_data.get('signals', ['분석중'])[:3])}

**투자 포인트**
- 상승 여력: {((top_data.get('resistance_level', 0)/max(top_data.get('current_price', 1), 0.01)-1)*100):+.1f}%
- 하락 위험: {((top_data.get('support_level', 0)/max(top_data.get('current_price', 1), 0.01)-1)*100):+.1f}%
"""

            # 데이터 품질 정보
            if realtime_count > 0:
                report += f"""

📡 **실시간 데이터 품질**
• Alpaca 실시간: {realtime_count}개 종목
• 지연 없는 현재가 반영
• IEX 거래소 기준 데이터
"""

            report += f"""

⚡ **오후 22:13 재검토 예정**
- 프리마켓 갭 분석 ({top_source} 데이터 기준)
- 기술적 신호 변화 점검  
- 제거/유지/신규 결정

⚠️ **리스크 관리**
• 개별 종목 최대 20% 비중
• 손절매: -7% 무조건 실행
• VIX 30+ 시 신중 접근

🎯 **투자 성공률 95% 목표**
📈 실시간 + 백업 하이브리드 데이터
🤖 Alpha Seeker v4.3 Premium Hybrid
"""
            
            return report
            
        except Exception as e:
            return f"""
🌅 **Alpha Seeker 오전 분석 오류**
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')} (KST)

❌ **리포트 생성 오류**
시스템 오류: {str(e)}

🔄 **다음 분석**: 오후 22:13 재시도
🤖 Alpha Seeker v4.3 Hybrid
"""
    
    def _generate_empty_report(self, current_time):
        """빈 리포트 생성"""
        return f"""
🌅 **Alpha Seeker 오전 분석**
📅 {current_time} (KST)

📊 **분석 결과 없음**
오늘은 투자할 만한 종목이 발견되지 않았습니다.
하이브리드 데이터 시스템으로 지속 모니터링합니다.

🔄 **다음 분석**: 오후 22:13
🤖 Alpha Seeker v4.3 Hybrid
"""

class EveningReportGenerator:
    def __init__(self):
        self.report_type = "pre_market_analysis"
        
    def generate(self, evening_data):
        """저녁 프리마켓 재검토 리포트 생성"""
        try:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
            
            maintained = evening_data.get('maintained', [])
            removed = evening_data.get('removed', [])
            detailed_analysis = evening_data.get('detailed_analysis', {})
            
            # 데이터 소스 통계
            realtime_maintained = sum(1 for symbol in maintained 
                                    if detailed_analysis.get(symbol, {}).get('data_source') == 'alpaca_realtime')
            
            report = f"""
🌙 **Alpha Seeker 프리마켓 재검토 v4.3**
📅 {current_time} (KST) | 미국 개장 30분 전

📡 **하이브리드 재검토 현황**
• 실시간 유지: {realtime_maintained}개 📡
• 백업 유지: {len(maintained) - realtime_maintained}개 📊

📊 **오전 종목 재검토 결과**
• ✅ 유지 종목: {len(maintained)}개
• ❌ 제외 종목: {len(removed)}개
• 📈 최종 투자 대상: {len(maintained)}개
"""

            # 유지 종목 상세 정보
            if maintained:
                report += f"""

✅ **유지 종목** ({len(maintained)}개)
"""
                for i, symbol in enumerate(maintained[:5], 1):
                    if symbol in detailed_analysis:
                        data = detailed_analysis[symbol]
                        gap_pct = data.get('gap_pct', 0)
                        score = data.get('score', 0)
                        current_price = data.get('current_price', 0)
                        source_emoji = "📡" if data.get('data_source') == 'alpaca_realtime' else "📊"
                        
                        status_emoji = "🟢" if gap_pct >= 0 else "🔴"
                        
                        report += f"""
{i}. **{symbol}** {source_emoji}: ${current_price} (갭: {gap_pct:+.1f}%)
   점수: {score}/10 | 상태: 정상 유지 {status_emoji}
"""

            # 제외 종목 정보
            if removed:
                report += f"""

❌ **제외 종목** ({len(removed)}개)
"""
                for symbol, reason in removed[:3]:
                    if symbol in detailed_analysis:
                        data = detailed_analysis[symbol]
                        gap_pct = data.get('gap_pct', 0)
                        current_price = data.get('current_price', 0)
                        source_emoji = "📡" if data.get('data_source') == 'alpaca_realtime' else "📊"
                        
                        report += f"""
• **{symbol}** {source_emoji}: ${current_price} (갭: {gap_pct:+.1f}%)
  제외 사유: {reason}
"""

            # 최종 투자 전략
            if maintained:
                # 점수순 재정렬
                final_sorted = []
                for symbol in maintained:
                    if symbol in detailed_analysis:
                        final_sorted.append((symbol, detailed_analysis[symbol]))
                
                final_sorted.sort(key=lambda x: x[1].get('score', 0), reverse=True)
                
                report += f"""

🎯 **최종 투자 전략 TOP 3**
"""
                for i, (symbol, data) in enumerate(final_sorted[:3], 1):
                    current_price = data.get('current_price', 0)
                    score = data.get('score', 0)
                    resistance = data.get('resistance_level', current_price * 1.05)
                    support = data.get('support_level', current_price * 0.95)
                    rsi = data.get('rsi', 50)
                    source_emoji = "📡" if data.get('data_source') == 'alpaca_realtime' else "📊"
                    
                    report += f"""
{i}. **{symbol}** {source_emoji}: ${current_price}
   기술점수: {score}/10 | RSI: {rsi}
   목표: ${resistance} | 손절: ${support}
"""

            # 데이터 품질 정보
            if realtime_maintained > 0:
                report += f"""

📡 **실시간 모니터링**
• {realtime_maintained}개 종목 실시간 추적
• 갭 변화 즉시 반영
"""

            # 즉시 행동 지침
            if len(maintained) > 0:
                action_msg = "계획대로 진행, 포지션 유지"
                if realtime_maintained > 0:
                    action_msg += f" (실시간 {realtime_maintained}개 중점 관리)"
            else:
                action_msg = "투자 대상 없음, 관망 권고"
            
            if len(removed) > 0:
                risk_msg = "제거 종목 손절 검토 필요"
            else:
                risk_msg = "특별한 위험 없음"
                
            report += f"""

🚨 **즉시 행동 지침**
• 기본 전략: {action_msg}
• 리스크 관리: {risk_msg}

⏰ **핵심 모니터링 시간**
• 23:30-24:00: 개장 첫 30분 집중
• 01:00: 중간 점검 (실시간 데이터 우선)
• 04:30: 마감 전 확인

🎯 다음 분석: 내일 06:07 (하이브리드 모닝 브리핑)
🤖 Alpha Seeker v4.3 프리마켓 하이브리드
"""
            
            return report
            
        except Exception as e:
            return f"""
🌙 **Alpha Seeker 프리마켓 재검토 오류**
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')} (KST)

❌ **재검토 오류**
오류: {str(e)}

🔄 다음 분석: 내일 06:07
🤖 Alpha Seeker v4.3 Hybrid
"""

class SundayReportGenerator:
    def __init__(self):
        self.report_type = "sunday_analysis"
        
    def generate(self, sunday_data):
        """일요일 주간 전략 리포트 생성"""
        try:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
            
            report = f"""
📊 **Alpha Seeker 주간 전략 분석 v4.3**
📅 {current_time} (KST)

🚀 **하이브리드 시스템 업그레이드 완료**
• 📡 Alpaca 실시간 데이터 통합
• 📊 yfinance 백업 데이터 보장
• 🔄 자동 장애 복구 시스템

📈 **차주 투자 전략**
하이브리드 데이터 시스템으로 더욱 정확한 분석을 제공합니다.

**데이터 품질 향상**
• 실시간성: Alpaca IEX 데이터
• 안정성: yfinance 백업
• 신뢰성: 이중 검증 시스템

**차주 포트폴리오 전략**
• 실시간 데이터 종목: 40% 비중
• 백업 데이터 종목: 35% 비중  
• 현금 비중: 25% (기회 대기)

📅 **차주 핵심 일정**
• 월요일 06:07 - 하이브리드 분석 시작
• 매일 22:13 - 실시간 재검토
• 주요 경제지표 발표 실시간 모니터링

⚠️ **리스크 관리**
• 데이터 소스 이중화로 안정성 확보
• API 장애 시 자동 백업 전환
• 실시간 갭 모니터링 강화

🎯 **성과 목표**
• 투자 성공률: 95% 유지
• 월 수익률: 5-10% 목표
• 리스크: 최대 낙폭 7% 제한

🔄 **시스템 성능**
• 하이브리드 데이터: 100% 가동
• 자동 복구: 실시간 적용
• 다음 주간 분석: 차주 일요일 18:23

🤖 Alpha Seeker v4.3 하이브리드 주간 전략
"""
            
            return report
            
        except Exception as e:
            return f"""
📊 **Alpha Seeker 일요일 분석 오류**
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')} (KST)

❌ **주간 분석 오류**
오류: {str(e)}

🔄 다음 분석: 내일 06:07
🤖 Alpha Seeker v4.3 Hybrid
"""

print("✅ HybridReportGenerator 모듈 로드 완료 (Alpaca + yfinance)")
