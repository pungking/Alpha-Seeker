import yfinance as yf
import pandas as pd
import numpy as np
import logging
from datetime import datetime

class TechnicalAnalyzer:
    def __init__(self):
        self.timeout = 30
        self.retry_count = 3
        
    def analyze(self, ticker, retry=True):
        """강화된 기술적 분석 (기존 로직 유지)"""
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
                
                # Empty DataFrame 체크
                if data.empty or len(data) < 20:
                    if attempt < self.retry_count - 1:
                        print(f"⚠️ {ticker} 데이터 부족, 재시도 중... ({attempt+1}/{self.retry_count})")
                        continue
                    else:
                        print(f"❌ {ticker} 데이터 수집 최종 실패")
                        return None
                
                # 기술적 분석 수행
                analysis_result = self.perform_technical_analysis(ticker, data)
                return analysis_result
                
            except Exception as e:
                if attempt < self.retry_count - 1:
                    print(f"⚠️ {ticker} 분석 오류 ({attempt+1}/{self.retry_count}): {str(e)}")
                    import time
                    time.sleep(2 ** attempt)  # 지수 백오프
                else:
                    print(f"❌ {ticker} 최종 분석 실패: {str(e)}")
                    logging.error(f"{ticker} 분석 실패: {e}")
                    return None
        
        return None
    
    def perform_technical_analysis(self, ticker, data):
        """실제 기술적 분석 로직 (EMA, RSI, 볼린저밴드, MACD)"""
        try:
            current_price = data['Close'].iloc[-1]
            volume = data['Volume'].iloc[-1] if 'Volume' in data else 0
            
            # EMA 계산 (SMA 대신 사용)
            ema_12 = data['Close'].ewm(span=12).mean().iloc[-1]
            ema_26 = data['Close'].ewm(span=26).mean().iloc[-1]
            
            # RSI 계산
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]
            
            # 볼린저 밴드
            bb_middle = data['Close'].rolling(20).mean()
            bb_std = data['Close'].rolling(20).std()
            bb_upper = (bb_middle + (bb_std * 2)).iloc[-1]
            bb_lower = (bb_middle - (bb_std * 2)).iloc[-1]
            
            # MACD
            macd_line = ema_12 - ema_26
            macd_signal = (ema_12 - ema_26).rolling(9).mean().iloc[-1]
            
            # 거래량 평균
            volume_avg = data['Volume'].rolling(20).mean().iloc[-1] if 'Volume' in data else volume
            
            # 점수 계산 (기존 로직 유지)
            score = 5  # 기본 점수
            signals = []
            
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
            
            # RSI 분석
            if 30 <= rsi <= 70:  # 적정 구간
                score += 1
                signals.append("RSI 양호")
            elif rsi < 30:
                score += 0.5  # 과매도 (반등 가능성)
                signals.append("과매도 구간")
            elif rsi > 70:
                signals.append("과매수 주의")
            
            # 볼린저 밴드 분석
            if bb_lower < current_price < bb_upper:
                score += 0.5
                signals.append("볼린저 적정구간")
            elif current_price < bb_lower:
                signals.append("볼린저 하단 접촉")
            
            # MACD 분석
            if macd_line > macd_signal:
                score += 0.5
                signals.append("MACD 상승신호")
            
            # 거래량 분석
            if volume > volume_avg * 1.5:
                score += 0.5
                signals.append("거래량 급증")
            
            return {
                'ticker': ticker,
                'current_price': float(current_price),
                'ema_12': float(ema_12),
                'ema_26': float(ema_26),
                'rsi': float(rsi),
                'bb_upper': float(bb_upper),
                'bb_lower': float(bb_lower),
                'macd_signal': float(macd_line - macd_signal),
                'volume': int(volume) if volume > 0 else 0,
                'volume_avg': int(volume_avg) if volume_avg > 0 else 0,
                'score': min(round(score, 1), 10),
                'signals': signals,
                'analysis_time': datetime.now().isoformat(),
                # 추가: 신뢰도 메트릭
                'confidence': min(score / 10.0, 1.0),
                'volatility': float((bb_upper - bb_lower) / current_price) if current_price > 0 else 0
            }
            
        except Exception as e:
            print(f"❌ {ticker} 지표 계산 오류: {str(e)}")
            logging.error(f"{ticker} 지표 계산 오류: {e}")
            return None

print("✅ TechnicalAnalyzer Enhanced (EMA + RSI + 볼린저밴드 + MACD + 신뢰도)")
