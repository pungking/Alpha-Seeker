import yfinance as yf
import pandas as pd
import numpy as np
import logging
from datetime import datetime


class TechnicalAnalyzer:
    def __init__(self):
        self.timeout = 30
        self.retry_count = 3
        
        # 로깅 설정
        self.logger = logging.getLogger(__name__)
        
    def analyze(self, ticker, retry=True):
        """강화된 기술적 분석 (데이터 검증 포함)"""
        for attempt in range(self.retry_count if retry else 1):
            try:
                # yfinance 데이터 수집
                stock = yf.Ticker(ticker)
                
                # 타임아웃과 함께 데이터 요청
                data = stock.history(
                    period="60d", 
                    interval="1d", 
                    timeout=self.timeout
                )
                
                # 데이터 유효성 검증
                if not self.validate_market_data(data, ticker):
                    if attempt < self.retry_count - 1:
                        self.logger.warning(f"{ticker} 데이터 검증 실패, 재시도 중... ({attempt + 1}/{self.retry_count})")
                        continue
                    else:
                        self.logger.error(f"{ticker} 데이터 검증 최종 실패")
                        return None
                
                # 기술적 분석 수행
                analysis_result = self.perform_technical_analysis(ticker, data)
                return analysis_result
                
            except Exception as e:
                if attempt < self.retry_count - 1:
                    self.logger.warning(f"{ticker} 분석 오류 ({attempt + 1}/{self.retry_count}): {str(e)}")
                    import time
                    time.sleep(2 ** attempt)  # 지수 백오프
                else:
                    self.logger.error(f"{ticker} 최종 분석 실패: {str(e)}")
                    return None
        
        return None
    
    def validate_market_data(self, data, ticker):
        """시장 데이터 유효성 검증 (강화된 버전)"""
        try:
            # 1. 빈 데이터 체크
            if data.empty:
                self.logger.error(f"{ticker}: 데이터가 비어있음")
                return False
            
            # 2. 최소 데이터 개수 체크
            if len(data) < 20:
                self.logger.error(f"{ticker}: 데이터 부족 ({len(data)}개, 최소 20개 필요)")
                return False
            
            # 3. 가격 유효성 체크
            current_price = data['Close'].iloc[-1]
            if pd.isna(current_price) or current_price <= 0:
                self.logger.error(f"{ticker}: 비정상적 현재가 {current_price}")
                return False
            
            if current_price > 10000:  # 일반적이지 않은 고가
                self.logger.warning(f"{ticker}: 높은 가격 주의 ${current_price}")
            
            # 4. 거래량 체크
            volume = data['Volume'].iloc[-1]
            if pd.isna(volume) or volume < 0:
                self.logger.error(f"{ticker}: 비정상적 거래량 {volume}")
                return False
            
            if volume == 0:
                self.logger.warning(f"{ticker}: 거래량 0 - 휴장일 또는 거래 정지 가능성")
            
            # 5. 가격 연속성 체크 (급격한 변화 감지)
            if len(data) >= 2:
                prev_price = data['Close'].iloc[-2]
                price_change = abs((current_price - prev_price) / prev_price)
                
                if price_change > 0.5:  # 50% 이상 급변
                    self.logger.warning(f"{ticker}: 급격한 가격 변화 {price_change * 100:.1f}% - 분할/합병 가능성")
            
            # 6. 데이터 무결성 체크
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_columns = [col for col in required_columns if col not in data.columns]
            
            if missing_columns:
                self.logger.error(f"{ticker}: 필수 컬럼 누락 {missing_columns}")
                return False
            
            # 7. OHLC 논리적 일관성 체크
            last_row = data.iloc[-1]
            if not (last_row['Low'] <= last_row['Close'] <= last_row['High']):
                self.logger.error(f"{ticker}: OHLC 데이터 불일치")
                return False
            
            if not (last_row['Low'] <= last_row['Open'] <= last_row['High']):
                self.logger.error(f"{ticker}: OHLC 데이터 불일치")
                return False
            
            self.logger.debug(f"{ticker}: 데이터 검증 통과 ({len(data)}개 데이터)")
            return True
            
        except Exception as e:
            self.logger.error(f"{ticker} 데이터 검증 중 오류: {e}")
            return False
    
    def perform_technical_analysis(self, ticker, data):
        """실제 기술적 분석 로직 (기존 코드와 동일하되 추가 안전성 검사)"""
        try:
            current_price = data['Close'].iloc[-1]
            volume = data['Volume'].iloc[-1] if 'Volume' in data else 0
            
            # EMA 계산 (Series로 유지하여 rolling 계산 가능하게 함)
            ema_12_series = data['Close'].ewm(span=12).mean()
            ema_26_series = data['Close'].ewm(span=26).mean()
            
            # NaN 값 체크
            if ema_12_series.isna().any() or ema_26_series.isna().any():
                self.logger.warning(f"{ticker}: EMA 계산에서 NaN 값 발견")
            
            ema_12 = ema_12_series.iloc[-1]
            ema_26 = ema_26_series.iloc[-1]
            
            # RSI 계산 (안전성 강화)
            rsi_series = self._calculate_rsi_safe(data['Close'])
            rsi = rsi_series.iloc[-1] if not rsi_series.empty else 50
            
            # 볼린저 밴드 (안전성 강화)
            bb_middle = data['Close'].rolling(20).mean()
            bb_std = data['Close'].rolling(20).std()
            
            if bb_std.iloc[-1] == 0:  # 표준편차가 0인 경우 (모든 값이 동일)
                self.logger.warning(f"{ticker}: 볼린저밴드 계산 불가 (표준편차 0)")
                bb_upper = current_price * 1.02
                bb_lower = current_price * 0.98
            else:
                bb_upper = (bb_middle + (bb_std * 2)).iloc[-1]
                bb_lower = (bb_middle - (bb_std * 2)).iloc[-1]
            
            # MACD 계산 (수정된 버전)
            macd_line_series = ema_12_series - ema_26_series
            macd_signal_series = macd_line_series.ewm(span=9).mean()
            macd_histogram = (macd_line_series - macd_signal_series).iloc[-1]
            
            # 거래량 평균 (안전한 계산)
            volume_avg_series = (data['Volume'].rolling(20).mean() if 'Volume' in data 
                               else pd.Series([volume] * len(data)))
            volume_avg = (volume_avg_series.iloc[-1] if not volume_avg_series.empty 
                         and not pd.isna(volume_avg_series.iloc[-1]) else volume)
            volume_ratio = volume / volume_avg if volume_avg > 0 else 1.0
            
            # 점수 계산 (기존 로직 유지하되 NaN 체크 추가)
            score = 5  # 기본 점수
            signals = []
            
            # 모든 지표가 유효한지 확인
            if pd.isna(ema_12) or pd.isna(ema_26) or pd.isna(rsi):
                self.logger.warning(f"{ticker}: 일부 지표 계산 실패")
                return None
            
            # EMA 기반 분석
            if current_price > ema_12:
                score += 1
                signals.append("12일 EMA 상향")
                
            if current_price > ema_26:
                score += 1
                signals.append("26일 EMA 상향")
                
            # 골든크로스/데드크로스
            if ema_12 > ema_26:
                score += 0.5
                signals.append("EMA 골든크로스")
            elif ema_12 < ema_26:
                signals.append("EMA 데드크로스")
            
            # RSI 분석
            if 30 <= rsi <= 70:
                score += 1
                signals.append("RSI 양호")
            elif rsi < 30:
                score += 0.5
                signals.append("과매도 구간")
            elif rsi > 70:
                signals.append("과매수 주의")
            
            # 볼린저 밴드 분석
            if bb_lower < current_price < bb_upper:
                score += 0.5
                signals.append("볼린저 적정구간")
            elif current_price <= bb_lower:
                score += 0.3
                signals.append("볼린저 하단 접촉")
            elif current_price >= bb_upper:
                signals.append("볼린저 상단 접촉")
            
            # MACD 분석
            if not pd.isna(macd_histogram):
                if macd_histogram > 0:
                    score += 0.5
                    signals.append("MACD 상승신호")
                elif macd_histogram < -0.1:
                    signals.append("MACD 하락신호")
            
            # 거래량 분석
            if volume_ratio > 1.5:
                score += 0.5
                signals.append("거래량 급증")
            elif volume_ratio < 0.7:
                signals.append("거래량 위축")
            
            # 추가 기술적 분석: 가격 모멘텀
            price_change_5d = 0
            if len(data) >= 6:
                price_change_5d = ((current_price - data['Close'].iloc[-6]) 
                                 / data['Close'].iloc[-6] * 100)
                if price_change_5d > 3:
                    score += 0.3
                    signals.append("5일 상승 모멘텀")
                elif price_change_5d < -3:
                    signals.append("5일 하락 모멘텀")
            
            # 긴급 매수/매도 신호 감지
            urgent_signals = self.detect_urgent_signals(
                data, current_price, ema_12, ema_26, rsi, macd_histogram, 
                volume_ratio, bb_upper, bb_lower
            )
            
            return {
                'ticker': ticker,
                'current_price': float(current_price),
                'ema_12': float(ema_12),
                'ema_26': float(ema_26),
                'rsi': float(rsi),
                'bb_upper': float(bb_upper),
                'bb_lower': float(bb_lower),
                'bb_middle': float(bb_middle.iloc[-1]),
                'macd_signal': float(macd_histogram) if not pd.isna(macd_histogram) else 0,
                'volume': int(volume) if volume > 0 else 0,
                'volume_avg': int(volume_avg) if volume_avg > 0 else 0,
                'volume_ratio': float(volume_ratio),
                'price_change_5d': float(price_change_5d),
                'score': min(round(score, 1), 10),
                'signals': signals[:6],
                'analysis_time': datetime.now().isoformat(),
                'confidence': min(score / 10.0, 1.0),
                'volatility': float((bb_upper - bb_lower) / current_price) if current_price > 0 else 0,
                'urgent_buy_signals': urgent_signals['buy'],
                'urgent_sell_signals': urgent_signals['sell'],
                'urgent_level': urgent_signals['level']
            }
            
        except Exception as e:
            self.logger.error(f"{ticker} 지표 계산 오류: {str(e)}")
            return None
    
    def _calculate_rsi_safe(self, prices, period=14):
        """안전한 RSI 계산"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            # 0으로 나누기 방지
            rs = gain / loss.replace(0, np.nan)
            rsi = 100 - (100 / (1 + rs))
            
            # NaN 값을 50으로 대체
            rsi = rsi.fillna(50)
            
            return rsi
            
        except Exception as e:
            self.logger.error(f"RSI 계산 오류: {e}")
            # 기본값으로 50 시리즈 반환
            return pd.Series([50] * len(prices), index=prices.index)
    
    def detect_urgent_signals(self, data, current_price, ema_12, ema_26, rsi, 
                            macd_histogram, volume_ratio, bb_upper, bb_lower):
        """긴급 신호 감지"""
        try:
            # 이전 값들 계산
            prev_rsi = 50
            if len(data) > 15:
                prev_data = data[:-1]['Close']
                prev_rsi_series = self._calculate_rsi_safe(prev_data)
                if not prev_rsi_series.empty:
                    prev_rsi = prev_rsi_series.iloc[-1]
            
            # 긴급 신호 로직...
            buy_signals = []
            sell_signals = []
            urgency_level = 0
            
            # 급락/급등 검사
            if len(data) >= 2:
                price_change_1d = ((current_price - data['Close'].iloc[-2]) 
                                 / data['Close'].iloc[-2] * 100)
                
                if price_change_1d <= -5:  # 5% 이상 급락
                    sell_signals.append("급락 발생")
                    urgency_level = max(urgency_level, 4)
                elif price_change_1d >= 10:  # 10% 이상 급등
                    buy_signals.append("급등 발생")
                    urgency_level = max(urgency_level, 3)
            
            # RSI 극한값
            if rsi <= 20:
                buy_signals.append("RSI 극한 과매도")
                urgency_level = max(urgency_level, 4)
            elif rsi >= 80:
                sell_signals.append("RSI 극한 과매수")
                urgency_level = max(urgency_level, 4)
            
            # 거래량 급증
            if volume_ratio >= 3.0:
                if len(buy_signals) > 0:
                    buy_signals.append("거래량 급증")
                    urgency_level = max(urgency_level, 3)
                elif len(sell_signals) > 0:
                    sell_signals.append("거래량 급증")
                    urgency_level = max(urgency_level, 3)
            
            return {
                'buy': buy_signals,
                'sell': sell_signals,
                'level': urgency_level
            }
            
        except Exception as e:
            self.logger.error(f"긴급 신호 감지 오류: {e}")
            return {'buy': [], 'sell': [], 'level': 0}


print("✅ TechnicalAnalyzer Enhanced (데이터 검증 + 안전성 강화)")
