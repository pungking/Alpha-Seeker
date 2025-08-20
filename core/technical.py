import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

class TechnicalAnalyzer:
    def __init__(self):
        self.min_data_points = 50

    def get_stock_data(self, ticker):
        """yfinance 전용 안정화 데이터 수집"""
        try:
            print(f"📈 {ticker} 데이터 수집 중...")
            stock = yf.Ticker(ticker)
            hist = stock.history(period="6mo")
            
            if len(hist) < self.min_data_points:
                print(f"⚠️ {ticker}: 데이터 부족")
                return None
                
            return {
                'history': hist,
                'current_price': float(hist['Close'].iloc[-1]),
                'previous_price': float(hist['Close'].iloc[-2]),
                'symbol': ticker,
                'data_source': 'yfinance_stable'
            }
        except Exception as e:
            print(f"❌ {ticker} 데이터 수집 실패: {e}")
            return None

    def calculate_rsi(self, prices, period=14):
        """RSI 계산"""
        try:
            prices_series = pd.Series(prices)
            delta = prices_series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return float(rsi.iloc[-1])
        except Exception:
            return 50.0

    def calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """MACD 계산"""
        try:
            prices_series = pd.Series(prices)
            ema_fast = prices_series.ewm(span=fast).mean()
            ema_slow = prices_series.ewm(span=slow).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal).mean()
            
            current_macd = float(macd_line.iloc[-1])
            current_signal = float(signal_line.iloc[-1])
            prev_macd = float(macd_line.iloc[-2])
            prev_signal = float(signal_line.iloc[-2])
            
            if prev_macd <= prev_signal and current_macd > current_signal:
                signal_type = "골든크로스"
            elif prev_macd >= prev_signal and current_macd < current_signal:
                signal_type = "데드크로스"
            elif current_macd > current_signal:
                signal_type = "강세"
            else:
                signal_type = "약세"
                
            return {
                'macd': current_macd,
                'signal': current_signal,
                'signal_type': signal_type
            }
        except Exception:
            return {
                'macd': 0.0,
                'signal': 0.0,
                'signal_type': '중립'
            }

    def calculate_bollinger_bands(self, prices, period=20, std_dev=2):
        """볼린저 밴드 계산"""
        try:
            prices_series = pd.Series(prices)
            sma = prices_series.rolling(window=period).mean()
            std = prices_series.rolling(window=period).std()
            
            upper_band = sma + (std * std_dev)
            lower_band = sma - (std * std_dev)
            
            current_price = prices[-1]
            current_upper = float(upper_band.iloc[-1])
            current_lower = float(lower_band.iloc[-1])
            current_middle = float(sma.iloc[-1])
            
            bb_position = (current_price - current_lower) / (current_upper - current_lower)
            
            return {
                'upper': current_upper,
                'middle': current_middle,
                'lower': current_lower,
                'position': float(bb_position)
            }
        except Exception:
            current_price = prices[-1]
            return {
                'upper': current_price * 1.05,
                'middle': current_price,
                'lower': current_price * 0.95,
                'position': 0.5
            }

    def calculate_moving_averages(self, prices):
        """이동평균선 계산"""
        try:
            prices_series = pd.Series(prices)
            
            sma_5 = float(prices_series.rolling(window=5).mean().iloc[-1])
            sma_20 = float(prices_series.rolling(window=20).mean().iloc[-1])
            sma_50 = float(prices_series.rolling(window=50).mean().iloc[-1])
            
            return {
                'sma_5': sma_5,
                'sma_20': sma_20,
                'sma_50': sma_50
            }
        except Exception:
            current_price = prices[-1]
            return {
                'sma_5': current_price,
                'sma_20': current_price,
                'sma_50': current_price
            }

    def calculate_volume_indicators(self, hist):
        """거래량 지표 계산"""
        try:
            volume = hist['Volume'].values
            current_volume = int(volume[-1])
            
            avg_volume_20 = np.mean(volume[-20:])
            volume_ratio = current_volume / avg_volume_20 if avg_volume_20 > 0 else 1
            
            return {
                'current_volume': current_volume,
                'volume_ratio': round(float(volume_ratio), 2)
            }
        except Exception:
            return {
                'current_volume': 1000000,
                'volume_ratio': 1.0
            }

    def generate_trading_signals(self, rsi, macd_data, bb_data, ma_data, current_price, volume_data, data_source):
        """매매 신호 생성 및 점수 계산"""
        signals = []
        score = 5.0
        
        # RSI 신호
        if rsi < 30:
            signals.append(f"RSI 과매도 ({rsi:.1f})")
            score += 3
        elif rsi < 40:
            signals.append(f"RSI 매수권 ({rsi:.1f})")
            score += 2
        elif rsi > 70:
            signals.append(f"RSI 과매수 ({rsi:.1f})")
            score -= 2
        
        # MACD 신호
        if macd_data['signal_type'] == "골든크로스":
            signals.append("MACD 골든크로스")
            score += 3
        elif macd_data['signal_type'] == "강세":
            signals.append("MACD 강세")
            score += 1
        elif macd_data['signal_type'] == "데드크로스":
            signals.append("MACD 데드크로스")
            score -= 2
        
        # 볼린저 밴드 신호
        bb_pos = bb_data['position']
        if bb_pos <= 0.1:
            signals.append("볼린저밴드 하단돌파")
            score += 2.5
        elif bb_pos <= 0.2:
            signals.append("볼린저밴드 하단권")
            score += 1.5
        elif bb_pos >= 0.9:
            signals.append("볼린저밴드 상단돌파")
            score -= 1.5
        elif bb_pos >= 0.8:
            signals.append("볼린저밴드 상단권")
            score -= 1
        
        # 이동평균선 신호
        sma_5 = ma_data['sma_5']
        sma_20 = ma_data['sma_20']
        sma_50 = ma_data['sma_50']
        
        if current_price > sma_5 > sma_20 > sma_50:
            signals.append("이평선 정배열")
            score += 2
        elif current_price > sma_20:
            signals.append("20일선 상회")
            score += 1
        
        # 거래량 신호
        vol_ratio = volume_data['volume_ratio']
        if vol_ratio > 2.0:
            signals.append(f"거래량 급증 ({vol_ratio:.1f}배)")
            score += 1.5
        elif vol_ratio > 1.5:
            signals.append(f"거래량 증가 ({vol_ratio:.1f}배)")
            score += 0.5
        
        final_score = max(0, min(10, score))
        return signals, round(final_score, 1)

    def calculate_support_resistance(self, hist, period=20):
        """지지/저항선 계산"""
        try:
            prices = hist['Close'].values
            highs = hist['High'].values
            lows = hist['Low'].values
            
            recent_high = float(np.max(highs[-period:]))
            recent_low = float(np.min(lows[-period:]))
            
            return {
                'resistance': recent_high,
                'support': recent_low
            }
        except Exception:
            current_price = hist['Close'].iloc[-1]
            return {
                'resistance': current_price * 1.1,
                'support': current_price * 0.9
            }

    def analyze(self, ticker):
        """종합 기술적 분석"""
        try:
            # 1. 데이터 수집
            stock_data = self.get_stock_data(ticker)
            if not stock_data:
                return None
            
            hist = stock_data['history']
            prices = hist['Close'].values
            current_price = stock_data['current_price']
            prev_price = stock_data['previous_price']
            data_source = stock_data['data_source']
            
            # 2. 기술적 지표 계산
            rsi = self.calculate_rsi(prices)
            macd_data = self.calculate_macd(prices)
            bb_data = self.calculate_bollinger_bands(prices)
            ma_data = self.calculate_moving_averages(prices)
            volume_data = self.calculate_volume_indicators(hist)
            support_resistance = self.calculate_support_resistance(hist)
            
            # 3. 매매 신호 생성
            signals, score = self.generate_trading_signals(
                rsi, macd_data, bb_data, ma_data, current_price, volume_data, data_source
            )
            
            # 4. 변화율 계산
            change_pct = ((current_price - prev_price) / prev_price) * 100
            
            # 5. 종합 결과
            result = {
                'symbol': ticker,
                'current_price': round(current_price, 2),
                'change_pct': round(change_pct, 2),
                'volume': volume_data['current_volume'],
                'volume_ratio': volume_data['volume_ratio'],
                'rsi': round(rsi, 1),
                'macd_signal': macd_data['signal_type'],
                'bb_position': round(bb_data['position'] * 100, 1),
                'support_level': round(support_resistance['support'], 2),
                'resistance_level': round(support_resistance['resistance'], 2),
                'signals': signals[:5],
                'score': score,
                'data_source': data_source,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            print(f"✅ {ticker} 📊 기술적 분석 완료: {score}/10점")
            return result
            
        except Exception as e:
            print(f"❌ {ticker} 기술적 분석 실패: {e}")
            return None

print("✅ TechnicalAnalyzer 안정화 (yfinance 기반)")
