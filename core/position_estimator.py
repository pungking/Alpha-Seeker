import pandas as pd
import numpy as np
from datetime import datetime
import logging

class AdvancedPositionEstimator:
    """고급 포지션 사이징 및 매매 예상 시스템"""
    
    def __init__(self, total_capital=100000):
        self.total_capital = total_capital
        self.max_position_per_stock = 0.20  # 종목당 최대 20%
        self.risk_per_trade = 0.02  # 거래당 최대 2% 리스크
        self.min_position = 1000   # 최소 포지션 금액
        
    def estimate_optimal_position(self, analysis_data):
        """종합적 포지션 분석 및 예상"""
        try:
            # 1. 기본 신호 분석
            signals = self._analyze_signals(analysis_data)
            
            # 2. 리스크 계산
            risk_metrics = self._calculate_risk(analysis_data)
            
            # 3. 포지션 크기 결정
            position_size = self._calculate_position_size(signals, risk_metrics)
            
            # 4. 진입/청산 타이밍 예상
            timing = self._predict_timing(analysis_data, signals)
            
            # 5. 손익 구간 예상
            profit_targets = self._calculate_profit_targets(analysis_data)
            
            return {
                'ticker': analysis_data.get('ticker', 'UNKNOWN'),
                'current_price': analysis_data.get('current_price', 0),
                'position_recommendation': self._get_recommendation(signals),
                'position_size': position_size,
                'risk_level': risk_metrics['risk_level'],
                'entry_timing': timing['entry'],
                'exit_timing': timing['exit'],
                'stop_loss': profit_targets['stop_loss'],
                'take_profit': profit_targets['take_profit'],
                'expected_return': profit_targets['expected_return'],
                'win_probability': signals['win_probability'],
                'confidence_score': signals['confidence'],
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"포지션 분석 오류: {e}")
            return self._get_default_position(analysis_data)
    
    def _analyze_signals(self, data):
        """신호 강도 분석"""
        score = data.get('score', 5)
        confidence = data.get('confidence', 0.5)
        rsi = data.get('rsi', 50)
        macd_signal = data.get('macd_signal', 0)
        volume_ratio = data.get('volume_ratio', 1.0)
        urgent_buy = len(data.get('urgent_buy_signals', []))
        urgent_sell = len(data.get('urgent_sell_signals', []))
        
        # 매수 신호 강도 (0-10)
        buy_strength = 0
        if score >= 8: 
            buy_strength += 4
        elif score >= 7: 
            buy_strength += 3
        elif score >= 6: 
            buy_strength += 2
        elif score >= 5: 
            buy_strength += 1
        
        if rsi < 25: 
            buy_strength += 3  # 극한 과매도
        elif rsi < 30: 
            buy_strength += 2  # 과매도
        elif rsi < 40: 
            buy_strength += 1
        
        if macd_signal > 0.5: 
            buy_strength += 2
        elif macd_signal > 0: 
            buy_strength += 1
        
        if volume_ratio > 3: 
            buy_strength += 2
        elif volume_ratio > 2: 
            buy_strength += 1
        
        buy_strength += min(urgent_buy, 3)  # 최대 3점
        
        # 매도 신호 강도 (0-10)
        sell_strength = 0
        if score <= 2: 
            sell_strength += 4
        elif score <= 3: 
            sell_strength += 3
        elif score <= 4: 
            sell_strength += 2
        elif score <= 5: 
            sell_strength += 1
        
        if rsi > 75: 
            sell_strength += 3  # 극한 과매수
        elif rsi > 70: 
            sell_strength += 2  # 과매수
        elif rsi > 60: 
            sell_strength += 1
        
        if macd_signal < -0.5: 
            sell_strength += 2
        elif macd_signal < 0: 
            sell_strength += 1
        
        sell_strength += min(urgent_sell, 3)  # 최대 3점
        
        # 승률 예상 (15% ~ 85%)
        win_probability = min(0.85, max(0.15, (score * confidence) / 10))
        
        return {
            'buy_strength': min(buy_strength, 10),
            'sell_strength': min(sell_strength, 10),
            'net_signal': buy_strength - sell_strength,
            'win_probability': win_probability,
            'confidence': confidence
        }
    
    def _calculate_risk(self, data):
        """리스크 메트릭 계산"""
        volatility = data.get('volatility', 0.05)
        current_price = data.get('current_price', 100)
        bb_upper = data.get('bb_upper', current_price * 1.1)
        bb_lower = data.get('bb_lower', current_price * 0.9)
        
        # 변동성 기반 리스크 등급
        risk_level = 'LOW'
        if volatility > 0.20:
            risk_level = 'EXTREME'
        elif volatility > 0.15:
            risk_level = 'VERY_HIGH'
        elif volatility > 0.10:
            risk_level = 'HIGH'
        elif volatility > 0.05:
            risk_level = 'MEDIUM'
        
        # 볼린저밴드 기반 위험도
        bb_range_pct = (bb_upper - bb_lower) / current_price if current_price > 0 else 0.1
        price_position = (current_price - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5
        
        # 리스크 조정 승수
        risk_multiplier = max(0.1, min(2.0, 1 / (volatility * 20 + 0.1)))
        
        return {
            'volatility': volatility,
            'risk_level': risk_level,
            'bb_risk': bb_range_pct,
            'price_position': price_position,
            'risk_multiplier': risk_multiplier
        }
    
    def _calculate_position_size(self, signals, risk_metrics):
        """최적 포지션 크기 계산 (Kelly Criterion 변형)"""
        net_signal = signals['net_signal']
        win_prob = signals['win_probability']
        risk_multiplier = risk_metrics['risk_multiplier']
        
        # Kelly Criterion 계산
        if win_prob > 0.5:
            # f = (bp - q) / b, 여기서 b=1, p=win_prob, q=1-win_prob
            kelly_fraction = (win_prob * 2 - 1)
            kelly_fraction = max(0, min(0.25, kelly_fraction))  # 최대 25%로 제한
        else:
            kelly_fraction = 0
        
        # 신호 강도 기반 승수
        signal_multiplier = max(0.1, min(2.0, abs(net_signal) / 5))
        
        # 기본 포지션 계산
        base_position = self.total_capital * self.risk_per_trade * signal_multiplier
        
        # Kelly와 리스크 조정 결합
        optimal_position = base_position * (1 + kelly_fraction) * risk_multiplier
        
        # 최대/최소 한도 적용
        max_allowed = self.total_capital * self.max_position_per_stock
        final_position = min(max(optimal_position, self.min_position), max_allowed)
        
        position_pct = final_position / self.total_capital
        
        return {
            'dollar_amount': round(final_position, 2),
            'percentage': round(position_pct * 100, 2),
            'shares': int(final_position / max(1, signals.get('current_price', 100))) if 'current_price' in signals else 0,
            'kelly_component': round(kelly_fraction * 100, 2),
            'signal_strength': round(signal_multiplier, 2),
            'risk_adjustment': round(risk_multiplier, 2)
        }
    
    def _predict_timing(self, data, signals):
        """진입/청산 타이밍 예상"""
        rsi = data.get('rsi', 50)
        net_signal = signals['net_signal']
        urgent_level = data.get('urgent_level', 0)
        
        # 진입 타이밍
        if net_signal > 5 or urgent_level >= 5:
            entry_timing = "IMMEDIATE"  # 즉시 매수
        elif net_signal > 3 or urgent_level >= 4:
            entry_timing = "SOON"      # 곧 매수 (1-2시간 내)
        elif net_signal > 0:
            entry_timing = "WAIT"      # 관망 (추가 신호 대기)
        elif net_signal > -3:
            entry_timing = "REDUCE"    # 포지션 축소
        else:
            entry_timing = "EXIT"      # 즉시 매도
        
        # 청산 타이밍 (RSI + 급반전 신호 기반)
        if rsi > 80 or urgent_level >= 5:
            exit_timing = "IMMEDIATE"  # 즉시 매도
        elif rsi > 70 or urgent_level >= 4:
            exit_timing = "PARTIAL"    # 부분 매도 (50%)
        elif rsi < 20:
            exit_timing = "HOLD"       # 보유 (극한 과매도)
        else:
            exit_timing = "MONITOR"    # 지속 모니터링
        
        return {
            'entry': entry_timing,
            'exit': exit_timing,
            'entry_score': net_signal,
            'exit_score': round((rsi - 50) / 10, 1),
            'urgency': urgent_level
        }
    
    def _calculate_profit_targets(self, data):
        """동적 손익 목표 설정"""
        current_price = data.get('current_price', 100)
        volatility = data.get('volatility', 0.05)
        bb_upper = data.get('bb_upper', current_price * 1.1)
        bb_lower = data.get('bb_lower', current_price * 0.9)
        
        # ATR 추정 (Average True Range)
        atr_estimate = current_price * volatility * 2
        
        # 동적 손절가 계산
        stop_loss_atr = current_price - (atr_estimate * 1.5)
        stop_loss_bb = bb_lower * 0.98
        stop_loss_support = current_price * 0.95  # 기본 5% 손절
        stop_loss = max(stop_loss_atr, stop_loss_bb, stop_loss_support)
        
        # 동적 익절가 계산  
        take_profit_atr = current_price + (atr_estimate * 2.5)
        take_profit_bb = bb_upper * 1.02
        take_profit_resistance = current_price * 1.10  # 기본 10% 익절
        take_profit = min(take_profit_atr, take_profit_bb, take_profit_resistance)
        
        # 기대 수익률 및 위험 보상 비율
        expected_return = ((take_profit - current_price) / current_price) * 100
        downside_risk = ((current_price - stop_loss) / current_price) * 100
        risk_reward_ratio = abs(expected_return / downside_risk) if downside_risk > 0 else 0
        
        return {
            'stop_loss': round(stop_loss, 2),
            'take_profit': round(take_profit, 2),
            'stop_loss_pct': round(-downside_risk, 1),
            'take_profit_pct': round(expected_return, 1),
            'expected_return': round(expected_return, 1),
            'risk_reward_ratio': round(risk_reward_ratio, 2),
            'atr_estimate': round(atr_estimate, 2)
        }
    
    def _get_recommendation(self, signals):
        """최종 매매 추천"""
        net_signal = signals['net_signal']
        confidence = signals['confidence']
        
        if net_signal >= 6 and confidence > 0.8:
            return "STRONG_BUY"
        elif net_signal >= 4 and confidence > 0.7:
            return "BUY"
        elif net_signal >= 2:
            return "WEAK_BUY"
        elif net_signal <= -6 and confidence > 0.8:
            return "STRONG_SELL"
        elif net_signal <= -4 and confidence > 0.7:
            return "SELL"
        elif net_signal <= -2:
            return "WEAK_SELL"
        else:
            return "HOLD"
    
    def _get_default_position(self, data):
        """기본 포지션 반환 (에러 시)"""
        return {
            'ticker': data.get('ticker', 'UNKNOWN'),
            'current_price': data.get('current_price', 0),
            'position_recommendation': 'HOLD',
            'position_size': {
                'dollar_amount': 0,
                'percentage': 0,
                'shares': 0
            },
            'risk_level': 'UNKNOWN',
            'entry_timing': 'WAIT',
            'exit_timing': 'MONITOR',
            'stop_loss': 0,
            'take_profit': 0,
            'expected_return': 0,
            'win_probability': 0.5,
            'confidence_score': 0.5
        }

print("✅ AdvancedPositionEstimator Enhanced Final (Kelly Criterion + 동적 손익 목표)")
