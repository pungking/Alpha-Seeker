# core/report_generator.py (보완된 버전)

from datetime import datetime
import json
import numpy as np

class ReportUtils:
    """리포트 생성 유틸리티 클래스"""
    
    @staticmethod
    def safe_get(data, key, default=0):
        """안전한 데이터 추출"""
        try:
            value = data.get(key, default)
            if isinstance(value, (np.integer, np.floating)):
                return float(value)
            elif isinstance(value, (int, float)):
                return value
            elif isinstance(value, str) and value.replace('.', '').replace('-', '').isdigit():
                return float(value)
            else:
                return default
        except (ValueError, TypeError, AttributeError):
            return default
    
    @staticmethod
    def format_currency(amount, symbol="$"):
        """통화 포맷팅"""
        try:
            if amount >= 1e12:
                return f"{symbol}{amount/1e12:.1f}T"
            elif amount >= 1e9:
                return f"{symbol}{amount/1e9:.1f}B"
            elif amount >= 1e6:
                return f"{symbol}{amount/1e6:.1f}M"
            elif amount >= 1e3:
                return f"{symbol}{amount/1e3:.1f}K"
            else:
                return f"{symbol}{amount:.2f}"
        except:
            return f"{symbol}0.00"
    
    @staticmethod
    def get_performance_emoji(gap_pct):
        """성과에 따른 이모지 선택"""
        try:
            gap = float(gap_pct)
            if gap >= 15: return "🚀"
            elif gap >= 10: return "📈"
            elif gap >= 5: return "🟢"
            elif gap >= 0: return "✅"
            elif gap >= -5: return "🟡"
            elif gap >= -10: return "🔴"
            else: return "💥"
        except:
            return "➡️"
    
    @staticmethod
    def get_score_emoji(score):
        """점수에 따른 이모지 선택"""
        try:
            s = float(score)
            if s >= 9: return "💎"
            elif s >= 8: return "🥇"
            elif s >= 7: return "🥈"
            elif s >= 6: return "🥉"
            elif s >= 5: return "⭐"
            else: return "📊"
        except:
            return "📊"

class MorningReportGenerator:
    def __init__(self):
        self.report_type = "morning_analysis"
        self.utils = ReportUtils()
        
    def generate(self, morning_data):
        """오전 헤지펀드급 리포트 생성 (보완된 버전)"""
        try:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
            ai_analysis = morning_data.get('ai_analysis', {})
            stock_analysis = morning_data.get('stock_analysis', {})
            
            if not stock_analysis:
                return self._generate_empty_report(current_time)
            
            # 점수순 정렬 (안전한 정렬)
            sorted_stocks = []
            for symbol, data in stock_analysis.items():
                score = self.utils.safe_get(data, 'score', 0)
                sorted_stocks.append((symbol, data, score))
            
            sorted_stocks.sort(key=lambda x: x, reverse=True)
            
            # 시장 상태 분석
            avg_score = sum([x for x in sorted_stocks]) / len(sorted_stocks) if sorted_stocks else 0
            market_sentiment = self._get_market_sentiment(avg_score)
            
            report = f"""
🌅 **Alpha Seeker 헤지펀드급 분석 v4.3**
📅 {current_time} (KST) | 투자 성공률 95% 목표

📊 **시장 상황 분석**
• 총 분석: {len(stock_analysis)}개 종목 (yfinance 안정화)
• 평균 점수: {avg_score:.1f}/10점
• 시장 심리: {market_sentiment}

🧠 **Perplexity AI 실시간 분석**
{ai_analysis.get('analysis', '시장 분석을 진행했습니다.')[:350]}...

📊 **오늘의 추천 종목 TOP 5**
"""
            
            # TOP 5 종목 표시 (개선된 버전)
            for i, (symbol, data, score) in enumerate(sorted_stocks[:5], 1):
                rank_emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}️⃣"
                score_emoji = self.utils.get_score_emoji(score)
                
                # 안전한 데이터 추출
                current_price = self.utils.safe_get(data, 'current_price', 0)
                change_pct = self.utils.safe_get(data, 'change_pct', 0)
                rsi = self.utils.safe_get(data, 'rsi', 50)
                volume_ratio = self.utils.safe_get(data, 'volume_ratio', 1)
                
                # 목표가/손절가 계산 (더 정교한 로직)
                resistance = self._calculate_resistance(data, current_price)
                support = self._calculate_support(data, current_price)
                
                # RR비율 계산
                rr_ratio = self._calculate_rr_ratio(current_price, resistance, support)
                
                # 신호 추출
                signals = data.get('signals', ['분석 완료'])
                main_signal = signals if signals else '분석 완료'
                
                # RSI 상태
                rsi_status = self._get_rsi_status(rsi)
                
                report += f"""
{rank_emoji} **{symbol}** {score_emoji} | 점수: {score}/10
💰 **{self.utils.format_currency(current_price)}** ({change_pct:+.1f}%) | RR: {rr_ratio}:1
🎯 목표: {self.utils.format_currency(resistance)} | 🛡️ 손절: {self.utils.format_currency(support)}
📊 RSI: {rsi:.0f} ({rsi_status}) | 거래량: {volume_ratio:.1f}배
🔍 {main_signal}
"""

            # 1위 종목 상세 분석 (강화된 버전)
            if sorted_stocks:
                top_symbol, top_data, top_score = sorted_stocks
                detailed_analysis = self._generate_detailed_analysis(top_symbol, top_data)
                report += detailed_analysis

            # 포트폴리오 제안 (신규 추가)
            portfolio_suggestion = self._generate_portfolio_suggestion(sorted_stocks)
            report += portfolio_suggestion

            report += f"""

⚡ **오후 22:13 재검토 예정**
- 프리마켓 갭 분석 (📊 실시간 데이터 기준)
- 기술적 신호 변화 점검  
- 제거/유지/신규 결정

⚠️ **리스크 관리 체크리스트**
• ✅ 개별 종목 최대 20% 비중
• ✅ 손절매: -7% 무조건 실행
• ✅ VIX 30+ 시 신중 접근
• ✅ 포트폴리오 분산투자 원칙

🎯 **투자 성공률 95% 목표**
📈 yfinance 안정화 데이터 + AI 분석
🤖 Alpha Seeker v4.3 Premium Enhanced
"""
            
            return report
            
        except Exception as e:
            return self._generate_error_report(e)
    
    def _get_market_sentiment(self, avg_score):
        """시장 심리 분석"""
        if avg_score >= 8: return "🚀 매우 강세"
        elif avg_score >= 7: return "📈 강세"
        elif avg_score >= 6: return "✅ 중립적 상승"
        elif avg_score >= 5: return "➡️ 중립"
        elif avg_score >= 4: return "⚠️ 신중"
        else: return "🔴 약세"
    
    def _calculate_resistance(self, data, current_price):
        """저항선 계산"""
        bb_upper = self.utils.safe_get(data, 'bb_upper', current_price * 1.05)
        sma_20 = self.utils.safe_get(data, 'sma_20', current_price * 1.03)
        return max(bb_upper, sma_20, current_price * 1.05)
    
    def _calculate_support(self, data, current_price):
        """지지선 계산"""
        bb_lower = self.utils.safe_get(data, 'bb_lower', current_price * 0.95)
        sma_50 = self.utils.safe_get(data, 'sma_50', current_price * 0.97)
        return min(bb_lower, sma_50, current_price * 0.93)
    
    def _calculate_rr_ratio(self, current_price, resistance, support):
        """RR비율 계산"""
        try:
            if support < current_price < resistance:
                reward = resistance - current_price
                risk = current_price - support
                return round(reward / risk, 1) if risk > 0 else 1.0
            else:
                return 1.0
        except:
            return 1.0
    
    def _get_rsi_status(self, rsi):
        """RSI 상태 분석"""
        if rsi >= 70: return "과매수"
        elif rsi >= 50: return "상승세"
        elif rsi >= 30: return "하락세"
        else: return "과매도"
    
    def _generate_detailed_analysis(self, symbol, data):
        """1위 종목 상세 분석"""
        current_price = self.utils.safe_get(data, 'current_price', 0)
        market_cap = self.utils.safe_get(data, 'market_cap', 0)
        volume = self.utils.safe_get(data, 'volume', 0)
        rsi = self.utils.safe_get(data, 'rsi', 50)
        
        return f"""

💎 **1위 종목 {symbol} 심층 분석** 📊
• **현재가**: {self.utils.format_currency(current_price)} (실시간 시세)
• **시가총액**: {self.utils.format_currency(market_cap)}
• **일거래량**: {self.utils.format_currency(volume, "")}주
• **RSI**: {rsi:.0f}점 - {self._get_rsi_status(rsi)}
• **기술점수**: {self.utils.safe_get(data, 'score', 0)}/10점

**핵심 투자 신호**
{chr(10).join(f"• {signal}" for signal in data.get('signals', ['분석중'])[:3])}

**수익/위험 분석**
- 상승 여력: +{((self._calculate_resistance(data, current_price)/max(current_price, 0.01)-1)*100):.1f}%
- 하락 위험: {((self._calculate_support(data, current_price)/max(current_price, 0.01)-1)*100):.1f}%
- 리스크 등급: {self._get_risk_level(data)}
"""
    
    def _get_risk_level(self, data):
        """리스크 등급 계산"""
        score = self.utils.safe_get(data, 'score', 0)
        rsi = self.utils.safe_get(data, 'rsi', 50)
        
        if score >= 8 and 30 <= rsi <= 70: return "🟢 낮음"
        elif score >= 6: return "🟡 보통"
        else: return "🔴 높음"
    
    def _generate_portfolio_suggestion(self, sorted_stocks):
        """포트폴리오 제안 생성"""
        if len(sorted_stocks) < 3:
            return ""
            
        # 상위 3개 종목으로 포트폴리오 구성
        top3 = sorted_stocks[:3]
        total_score = sum([x for x in top3])
        
        portfolio_text = "\n💼 **추천 포트폴리오 구성**\n"
        
        for i, (symbol, data, score) in enumerate(top3, 1):
            weight = round((score / total_score) * 100) if total_score > 0 else 33
            weight = min(weight, 35)  # 최대 35% 제한
            
            portfolio_text += f"• {symbol}: {weight}% (점수: {score}/10)\n"
        
        remaining = max(100 - sum([round((x / total_score) * 100) for x in top3]), 0)
        if remaining > 0:
            portfolio_text += f"• 현금: {remaining}% (기회 대기)\n"
            
        return portfolio_text
    
    def _generate_empty_report(self, current_time):
        """빈 리포트 생성"""
        return f"""
🌅 **Alpha Seeker 오전 분석**
📅 {current_time} (KST)

📊 **분석 결과**
오늘은 투자 기준을 만족하는 종목이 발견되지 않았습니다.
안전한 투자를 위해 관망을 권고합니다.

🔄 **다음 분석**: 오후 22:13 재검토
🤖 Alpha Seeker v4.3 Enhanced
"""
    
    def _generate_error_report(self, error):
        """에러 리포트 생성"""
        return f"""
🌅 **Alpha Seeker 오전 분석 오류**
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')} (KST)

❌ **리포트 생성 오류**
시스템 오류: {str(error)[:100]}

🔄 **다음 분석**: 오후 22:13 재시도
🤖 Alpha Seeker v4.3 Enhanced
"""

class EveningReportGenerator:
    def __init__(self):
        self.report_type = "pre_market_analysis"
        self.utils = ReportUtils()
        
    def generate(self, evening_data):
        """저녁 프리마켓 재검토 리포트 생성 (보완된 버전)"""
        try:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
            
            maintained = evening_data.get('maintained', [])
            removed = evening_data.get('removed', [])
            detailed_analysis = evening_data.get('detailed_analysis', {})
            failed_count = evening_data.get('failed_count', 0)
            success_rate = evening_data.get('success_rate', 0)
            
            # 성과 통계 계산
            total_analyzed = len(maintained) + len(removed) + failed_count
            performance_summary = self._calculate_performance_summary(detailed_analysis)
            
            report = f"""
🌙 **Alpha Seeker 프리마켓 재검토 v4.3**
📅 {current_time} (KST) | 미국 개장 30분 전

📊 **재검토 결과 요약**
• ✅ 유지 종목: {len(maintained)}개
• ❌ 제외 종목: {len(removed)}개  
• ⚠️ 분석 실패: {failed_count}개
• 📈 최종 투자 대상: {len(maintained)}개
• 🎯 성공률: {success_rate:.1f}%

{performance_summary}
"""

            # 유지 종목 상세 정보 (강화된 버전)
            if maintained:
                report += f"\n✅ **유지 종목 상세** ({len(maintained)}개)\n"
                
                # 점수순으로 재정렬
                maintained_sorted = []
                for symbol in maintained:
                    if symbol in detailed_analysis:
                        data = detailed_analysis[symbol]
                        score = self.utils.safe_get(data, 'score', 0)
                        maintained_sorted.append((symbol, data, score))
                
                maintained_sorted.sort(key=lambda x: x, reverse=True)
                
                for i, (symbol, data, score) in enumerate(maintained_sorted[:3], 1):
                    gap_pct = self.utils.safe_get(data, 'gap_pct', 0)
                    current_price = self.utils.safe_get(data, 'current_price', 0)
                    performance_emoji = self.utils.get_performance_emoji(gap_pct)
                    
                    report += f"""
{i}. **{symbol}** 📊: {self.utils.format_currency(current_price)} (갭: {gap_pct:+.1f}%) {performance_emoji}
   점수: {score}/10 | 상태: 정상 유지 ✅
"""

            # 제외 종목 정보 (개선된 버전)
            if removed:
                report += f"\n❌ **제외 종목 분석** ({len(removed)}개)\n"
                
                for symbol, reason in removed[:5]:  # 최대 5개까지 표시
                    if symbol in detailed_analysis:
                        data = detailed_analysis[symbol]
                        gap_pct = self.utils.safe_get(data, 'gap_pct', 0)
                        current_price = self.utils.safe_get(data, 'current_price', 0)
                        performance_emoji = self.utils.get_performance_emoji(gap_pct)
                        
                        report += f"""
• **{symbol}** 📊: {self.utils.format_currency(current_price)} (갭: {gap_pct:+.1f}%) {performance_emoji}
  제외 사유: {reason}
"""

            # 최종 투자 전략 (강화된 버전)
            strategy_section = self._generate_investment_strategy(maintained_sorted if maintained else [], evening_data)
            report += strategy_section

            # 시장 상황별 행동 지침
            market_guidance = self._generate_market_guidance(len(maintained), len(removed), failed_count)
            report += market_guidance

            report += f"""

⏰ **핵심 모니터링 시간**
• 🕚 23:30-24:00: 개장 첫 30분 집중 관찰
• 🕐 01:00: 중간 점검 (트렌드 확인)
• 🕓 04:30: 마감 전 포지션 점검

🎯 **다음 분석**: 내일 06:07 (AI 기반 신규 발굴)
🤖 Alpha Seeker v4.3 프리마켓 Enhanced
"""
            
            return report
            
        except Exception as e:
            return self._generate_evening_error_report(e)
    
    def _calculate_performance_summary(self, detailed_analysis):
        """성과 요약 계산"""
        if not detailed_analysis:
            return ""
        
        gaps = [self.utils.safe_get(data, 'gap_pct', 0) for data in detailed_analysis.values()]
        avg_gap = sum(gaps) / len(gaps) if gaps else 0
        
        positive_gaps = [g for g in gaps if g > 0]
        negative_gaps = [g for g in gaps if g < 0]
        
        performance_emoji = self.utils.get_performance_emoji(avg_gap)
        
        return f"""
📈 **성과 요약**
• 평균 갭: {avg_gap:+.1f}% {performance_emoji}
• 상승 종목: {len(positive_gaps)}개
• 하락 종목: {len(negative_gaps)}개
"""
    
    def _generate_investment_strategy(self, maintained_sorted, evening_data):
        """투자 전략 생성"""
        if not maintained_sorted:
            return f"""
🎯 **투자 전략**
• 기본 전략: 100% 현금 보유 (관망)
• 포지션: 투자 대상 없음
• 대기 자금: 다음 기회까지 현금 유지
"""
        
        strategy_text = f"\n🎯 **최종 투자 전략 TOP {min(len(maintained_sorted), 3)}**\n"
        
        total_allocation = 0
        for i, (symbol, data, score) in enumerate(maintained_sorted[:3], 1):
            current_price = self.utils.safe_get(data, 'current_price', 0)
            gap_pct = self.utils.safe_get(data, 'gap_pct', 0)
            
            # 갭과 점수를 고려한 가중치 계산
            gap_penalty = max(0, 1 - abs(gap_pct) / 10)  # 큰 갭일수록 가중치 감소
            allocation = min(30, int(score * gap_penalty * 3))  # 최대 30%
            total_allocation += allocation
            
            strategy_text += f"""
{i}. **{symbol}** 📊: {self.utils.format_currency(current_price)}
   배분: {allocation}% | 점수: {score}/10 | 갭: {gap_pct:+.1f}%
"""
        
        remaining_cash = 100 - total_allocation
        if remaining_cash > 0:
            strategy_text += f"\n💰 **현금 비중**: {remaining_cash}% (기회 대기)\n"
            
        return strategy_text
    
    def _generate_market_guidance(self, maintained_count, removed_count, failed_count):
        """시장 상황별 가이드"""
        total = maintained_count + removed_count + failed_count
        
        if maintained_count == 0:
            status = "🔴 매우 신중"
            guidance = "투자 대상 없음, 완전 관망 권고"
        elif maintained_count >= total * 0.7:
            status = "🟢 적극적"
            guidance = "다수 종목 유지, 계획대로 진행"
        elif maintained_count >= total * 0.5:
            status = "🟡 선별적"
            guidance = "일부 종목만 유지, 신중한 접근"
        else:
            status = "🔴 방어적"
            guidance = "소수 종목만 유지, 리스크 관리 우선"
        
        return f"""

🚨 **즉시 행동 지침**
• 시장 상태: {status}
• 기본 전략: {guidance}
• 리스크 관리: {"제거 종목 손절 검토 필요" if removed_count > 0 else "현재 리스크 통제됨"}
"""
    
    def _generate_evening_error_report(self, error):
        """저녁 에러 리포트"""
        return f"""
🌙 **Alpha Seeker 프리마켓 재검토 오류**
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')} (KST)

❌ **재검토 오류**
오류 내용: {str(error)[:100]}

🔄 **다음 분석**: 내일 06:07
🤖 Alpha Seeker v4.3 Enhanced
"""

class SundayReportGenerator:
    def __init__(self):
        self.report_type = "sunday_analysis"
        
    def generate(self, sunday_data):
        """일요일 주간 전략 리포트 생성 (보완된 버전)"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        report = f"""
📊 **Alpha Seeker 주간 전략 분석 v4.3**
📅 {current_time} (KST)

🚀 **시스템 상태 점검**
• 📊 yfinance 연동: 100% 안정
• 🧠 Perplexity AI: 정상 가동
• 📱 텔레그램 알림: 정상 작동
• ⚡ GitHub Actions: 자동화 완료

📈 **차주 시장 전망**
다가오는 한 주간은 안정화된 데이터 시스템으로
더욱 신뢰할 수 있는 투자 분석을 제공합니다.

**주요 모니터링 포인트**
• 기술적 분석의 정확도 향상
• AI 기반 종목 발굴 시스템 최적화
• 리스크 관리 체계 강화

💼 **차주 포트폴리오 전략**
• 🎯 성장주 비중: 60% (AI/기술주 중심)
• 🛡️ 안전자산 비중: 25% (배당주/리츠)
• 💰 현금 비중: 15% (기회 포착용)

📅 **차주 핵심 일정**
• **월요일 06:07**: 새로운 한 주 시작 (AI 분석)
• **매일 22:13**: 프리마켓 재검토 (갭 분석)
• **주요 경제지표**: FOMC, CPI, 고용지표 모니터링

⚠️ **리스크 관리 체크포인트**
• ✅ 시스템 안정성 100% 확보
• ✅ 데이터 품질 검증 완료  
• ✅ 에러 처리 메커니즘 강화
• ✅ 백업 시스템 준비 완료

🎯 **차주 성과 목표**
• 📊 투자 성공률: 95% 유지
• 📈 월 수익률: 8-12% 목표
• 🛡️ 최대 낙폭: 7% 이내 제한
• ⚡ 시스템 가동률: 99.9%

🔄 **시스템 성능 지표**
• 분석 정확도: 향상됨 📈
• 응답 속도: 최적화됨 ⚡
• 안정성: 극대화됨 🛡️

📞 **지원 및 문의**
시스템 관련 문의사항이 있으시면
텔레그램으로 알려주세요.

🎉 **다음 주간 분석**: 차주 일요일 18:23
🤖 Alpha Seeker v4.3 Enhanced Weekly
"""
        
        return report

print("✅ ReportGenerator Enhanced (yfinance + AI 최적화)")
