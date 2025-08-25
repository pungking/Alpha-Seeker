import yfinance as yf
import time
import threading
from datetime import datetime, timedelta
import logging

class RealtimeRiskMonitor:
    def __init__(self, telegram_bot, portfolio_tickers):
        self.telegram_bot = telegram_bot
        self.portfolio_tickers = portfolio_tickers or []
        self.monitoring = False
        self.alert_history = {}  # 중복 알림 방지
        
        # 위험 임계값 설정
        self.risk_thresholds = {
            'gap_down': -0.05,          # 5% 이상 갭다운
            'gap_up': 0.10,             # 10% 이상 갭업 (버블 위험)
            'consecutive_drop': -0.03,   # 3일 연속 3% 하락
            'rsi_oversold': 20,         # RSI 과매도
            'rsi_overbought': 80,       # RSI 과매수
            'volume_spike': 3.0,        # 거래량 3배 급증
            'volume_dry': 0.5,          # 거래량 50% 급감
            'vix_spike': 30,            # VIX 30 이상
            'support_break': -0.02,     # 지지선 2% 이탈
            'resistance_break': 0.02,   # 저항선 2% 돌파
            'price_crash': -0.10        # 10% 이상 급락 (크래시)
        }
    
    def start_monitoring(self):
        """실시간 모니터링 시작"""
        if not self.portfolio_tickers:
            print("⚠️ 모니터링할 종목이 없습니다.")
            return False
        
        self.monitoring = True
        
        # 1. 포트폴리오 모니터링 (3분 간격)
        portfolio_thread = threading.Thread(target=self._monitor_portfolio, daemon=True)
        portfolio_thread.start()
        
        # 2. 시장 전반 모니터링 (10분 간격)
        market_thread = threading.Thread(target=self._monitor_market, daemon=True)
        market_thread.start()
        
        # 3. VIX 모니터링 (15분 간격)
        vix_thread = threading.Thread(target=self._monitor_vix, daemon=True)
        vix_thread.start()
        
        logging.info(f"실시간 위험 모니터링 시작: {len(self.portfolio_tickers)}개 종목")
        print(f"🔍 실시간 위험 모니터링 활성화: {', '.join(self.portfolio_tickers)}")
        return True
    
    def _monitor_portfolio(self):
        """포트폴리오 종목 실시간 모니터링"""
        while self.monitoring:
            try:
                for ticker in self.portfolio_tickers:
                    risk_alerts = self._analyze_ticker_risk(ticker)
                    
                    for alert in risk_alerts:
                        self._send_urgent_alert(alert)
                
                time.sleep(180)  # 3분 간격
                
            except Exception as e:
                logging.error(f"포트폴리오 모니터링 오류: {e}")
                time.sleep(120)
    
    def _analyze_ticker_risk(self, ticker):
        """개별 종목 위험 분석 (긴급 매수/매도 신호 통합)"""
        alerts = []
        
        try:
            # 실시간 데이터 수집
            stock = yf.Ticker(ticker)
            
            # 최근 5일, 1시간 간격 데이터
            data_1h = stock.history(period="5d", interval="1h")
            data_1d = stock.history(period="10d", interval="1d")
            
            if data_1h.empty or data_1d.empty or len(data_1h) < 10:
                return alerts
            
            current_price = data_1h['Close'].iloc[-1]
            previous_close = data_1d['Close'].iloc[-2] if len(data_1d) >= 2 else current_price
            
            # 1. 급락/갭다운 검사
            gap_pct = (current_price - previous_close) / previous_close
            if gap_pct <= self.risk_thresholds['price_crash']:
                alerts.append({
                    'type': 'EMERGENCY',
                    'ticker': ticker,
                    'alert': 'PRICE_CRASH',
                    'value': gap_pct * 100,
                    'message': f"{ticker} 급락 발생: {gap_pct*100:+.1f}%"
                })
            elif gap_pct <= self.risk_thresholds['gap_down']:
                alerts.append({
                    'type': 'URGENT_SELL',
                    'ticker': ticker,
                    'alert': 'GAP_DOWN',
                    'value': gap_pct * 100,
                    'message': f"{ticker} 갭다운 발생: {gap_pct*100:+.1f}%"
                })
            elif gap_pct >= self.risk_thresholds['gap_up']:
                alerts.append({
                    'type': 'URGENT_BUY',
                    'ticker': ticker,
                    'alert': 'GAP_UP',
                    'value': gap_pct * 100,
                    'message': f"{ticker} 급등 발생: {gap_pct*100:+.1f}% (매수 기회 또는 버블 주의)"
                })
            
            # 2. RSI 극단값 검사
            rsi = self._calculate_rsi(data_1h['Close'])
            if rsi <= self.risk_thresholds['rsi_oversold']:
                alerts.append({
                    'type': 'URGENT_BUY',
                    'ticker': ticker,
                    'alert': 'RSI_OVERSOLD',
                    'value': rsi,
                    'message': f"{ticker} RSI 과매도: {rsi:.1f} (매수 기회)"
                })
            elif rsi >= self.risk_thresholds['rsi_overbought']:
                alerts.append({
                    'type': 'URGENT_SELL',
                    'ticker': ticker,
                    'alert': 'RSI_OVERBOUGHT',
                    'value': rsi,
                    'message': f"{ticker} RSI 과매수: {rsi:.1f} (매도 신호)"
                })
            
            # 3. 거래량 이상 검사
            if len(data_1h) >= 20:
                current_volume = data_1h['Volume'].iloc[-1]
                avg_volume = data_1h['Volume'].rolling(20).mean().iloc[-1]
                
                volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
                
                if volume_ratio >= self.risk_thresholds['volume_spike']:
                    if gap_pct > 0.02:  # 상승과 함께
                        alerts.append({
                            'type': 'URGENT_BUY',
                            'ticker': ticker,
                            'alert': 'VOLUME_SPIKE_UP',
                            'value': volume_ratio,
                            'message': f"{ticker} 상승 + 거래량 급증: {volume_ratio:.1f}배 (강력한 매수 신호)"
                        })
                    elif gap_pct < -0.02:  # 하락과 함께
                        alerts.append({
                            'type': 'URGENT_SELL',
                            'ticker': ticker,
                            'alert': 'VOLUME_SPIKE_DOWN',
                            'value': volume_ratio,
                            'message': f"{ticker} 하락 + 거래량 급증: {volume_ratio:.1f}배 (강력한 매도 신호)"
                        })
                    else:
                        alerts.append({
                            'type': 'WARNING',
                            'ticker': ticker,
                            'alert': 'VOLUME_SPIKE',
                            'value': volume_ratio,
                            'message': f"{ticker} 거래량 급증: {volume_ratio:.1f}배 (주의깊게 관찰)"
                        })
                elif volume_ratio <= self.risk_thresholds['volume_dry']:
                    alerts.append({
                        'type': 'WARNING',
                        'ticker': ticker,
                        'alert': 'VOLUME_DRY',
                        'value': volume_ratio,
                        'message': f"{ticker} 거래량 급감: {volume_ratio:.1f}배 (유동성 위험)"
                    })
            
            # 4. 지지선/저항선 이탈 검사
            if len(data_1d) >= 50:
                sma_20 = data_1d['Close'].rolling(20).mean().iloc[-1]
                sma_50 = data_1d['Close'].rolling(50).mean().iloc[-1]
                
                support_break = (current_price - sma_50) / sma_50
                resistance_break = (current_price - sma_20) / sma_20
                
                if support_break <= self.risk_thresholds['support_break']:
                    alerts.append({
                        'type': 'URGENT_SELL',
                        'ticker': ticker,
                        'alert': 'SUPPORT_BREAK',
                        'value': support_break * 100,
                        'message': f"{ticker} 50일선 이탈: {support_break*100:+.1f}% (추가 하락 위험)"
                    })
                
                elif resistance_break >= self.risk_thresholds['resistance_break']:
                    alerts.append({
                        'type': 'URGENT_BUY',
                        'ticker': ticker,
                        'alert': 'RESISTANCE_BREAK',
                        'value': resistance_break * 100,
                        'message': f"{ticker} 20일선 돌파: {resistance_break*100:+.1f}% (상승 모멘텀)"
                    })
            
            # 5. 추가 기술적 분석 기반 신호 (간단 버전)
            if len(data_1h) >= 24:  # 24시간 이상 데이터
                ema_12 = data_1h['Close'].ewm(span=12).mean()
                ema_26 = data_1h['Close'].ewm(span=26).mean()
                
                # 현재와 이전 EMA 크로스오버 감지
                current_ema12 = ema_12.iloc[-1]
                current_ema26 = ema_26.iloc[-1]
                prev_ema12 = ema_12.iloc[-2]
                prev_ema26 = ema_26.iloc[-2]
                
                # 골든크로스 감지
                if current_ema12 > current_ema26 and prev_ema12 <= prev_ema26:
                    alerts.append({
                        'type': 'URGENT_BUY',
                        'ticker': ticker,
                        'alert': 'GOLDEN_CROSS',
                        'value': (current_ema12 - current_ema26) / current_ema26 * 100,
                        'message': f"{ticker} EMA 골든크로스 발생 (강력한 매수 신호)"
                    })
                
                # 데드크로스 감지
                elif current_ema12 < current_ema26 and prev_ema12 >= prev_ema26:
                    alerts.append({
                        'type': 'URGENT_SELL',
                        'ticker': ticker,
                        'alert': 'DEATH_CROSS',
                        'value': (current_ema26 - current_ema12) / current_ema12 * 100,
                        'message': f"{ticker} EMA 데드크로스 발생 (강력한 매도 신호)"
                    })
            
        except Exception as e:
            logging.error(f"{ticker} 위험 분석 오류: {e}")
        
        return alerts
    
    def _monitor_market(self):
        """시장 전반 모니터링"""
        while self.monitoring:
            try:
                # SPY, QQQ, IWM 주요 지수 모니터링
                market_tickers = ['SPY', 'QQQ', 'IWM']
                
                for ticker in market_tickers:
                    stock = yf.Ticker(ticker)
                    data = stock.history(period="2d", interval="1h")
                    
                    if not data.empty and len(data) >= 2:
                        current = data['Close'].iloc[-1]
                        previous = data['Close'].iloc[-2]
                        change_pct = (current - previous) / previous * 100
                        
                        if change_pct <= -3:  # 3% 이상 급락
                            self._send_urgent_alert({
                                'type': 'EMERGENCY',
                                'ticker': ticker,
                                'alert': 'MARKET_CRASH',
                                'value': change_pct,
                                'message': f"시장 급락 감지: {ticker} {change_pct:+.1f}%"
                            })
                        elif change_pct <= -1.5:  # 1.5% 이상 하락
                            self._send_urgent_alert({
                                'type': 'URGENT_SELL',
                                'ticker': ticker,
                                'alert': 'MARKET_DECLINE',
                                'value': change_pct,
                                'message': f"시장 하락 신호: {ticker} {change_pct:+.1f}%"
                            })
                        elif change_pct >= 2:  # 2% 이상 상승
                            self._send_urgent_alert({
                                'type': 'URGENT_BUY',
                                'ticker': ticker,
                                'alert': 'MARKET_RALLY',
                                'value': change_pct,
                                'message': f"시장 상승 신호: {ticker} {change_pct:+.1f}%"
                            })
                
                time.sleep(600)  # 10분 간격
                
            except Exception as e:
                logging.error(f"시장 모니터링 오류: {e}")
                time.sleep(300)
    
    def _monitor_vix(self):
        """VIX 변동성 지수 모니터링"""
        while self.monitoring:
            try:
                vix = yf.Ticker('^VIX')
                data = vix.history(period="1d", interval="15m")
                
                if not data.empty:
                    current_vix = data['Close'].iloc[-1]
                    
                    if current_vix >= 35:  # VIX 35 이상 (극도 공포)
                        self._send_urgent_alert({
                            'type': 'EMERGENCY',
                            'ticker': 'VIX',
                            'alert': 'VIX_EXTREME',
                            'value': current_vix,
                            'message': f"VIX 극도 공포: {current_vix:.1f} (시장 패닉 상태 - 매수 기회 가능성)"
                        })
                    elif current_vix >= self.risk_thresholds['vix_spike']:
                        self._send_urgent_alert({
                            'type': 'URGENT_SELL',
                            'ticker': 'VIX',
                            'alert': 'VIX_SPIKE',
                            'value': current_vix,
                            'message': f"VIX 공포지수 급등: {current_vix:.1f} (변동성 증가 - 주의 필요)"
                        })
                    elif current_vix <= 15:  # VIX 낮음 (시장 안정)
                        self._send_urgent_alert({
                            'type': 'INFO',
                            'ticker': 'VIX',
                            'alert': 'VIX_LOW',
                            'value': current_vix,
                            'message': f"VIX 안정권: {current_vix:.1f} (시장 안정 - 적극적 투자 환경)"
                        })
                
                time.sleep(900)  # 15분 간격
                
            except Exception as e:
                logging.error(f"VIX 모니터링 오류: {e}")
                time.sleep(600)
    
    def _calculate_rsi(self, prices, period=14):
        """RSI 계산"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.iloc[-1] if not rsi.empty else 50
        except:
            return 50  # 기본값
    
    def _send_urgent_alert(self, alert):
        """긴급 알림 전송 (긴급 매수/매도 신호 포함)"""
        alert_key = f"{alert['ticker']}_{alert['alert']}"
        current_time = datetime.now()
        
        # 중복 알림 방지 (같은 알림은 30분에 한 번만)
        if alert_key in self.alert_history:
            last_alert = self.alert_history[alert_key]
            if current_time - last_alert < timedelta(minutes=30):
                return
        
        # 알림 메시지 생성
        if alert['type'] == 'EMERGENCY':
            message = f"""
🚨🚨🚨 ALPHA SEEKER 긴급 알림 🚨🚨🚨
⏰ {current_time.strftime('%H:%M:%S')} KST

🔥 {alert['message']}

⚠️ 즉시 확인 필요:
• 포지션 즉시 재검토
• 손절 라인 점검  
• 추가 하락/상승 대비
• 리스크 관리 강화

📱 즉시 대응 바랍니다!
🤖 Alpha Seeker v4.3 Enhanced Final
"""
            self.telegram_bot.send_message(message, emergency=True)
            logging.critical(f"긴급 알림 전송: {alert['message']}")
            
        elif alert['type'] == 'URGENT_BUY':
            message = f"""
🟢 긴급 매수 신호 🟢
⏰ {current_time.strftime('%H:%M:%S')} KST

✅ {alert['message']}

📊 매수 고려사항:
• 포지션 크기 신중히 결정
• 손절가 미리 설정
• 추가 확인 신호 대기 권장

💰 신중한 매수 검토 바랍니다
🤖 Alpha Seeker v4.3 Enhanced Final
"""
            self.telegram_bot.send_message(message, urgent=True)
            logging.warning(f"긴급 매수 신호: {alert['message']}")
            
        elif alert['type'] == 'URGENT_SELL':
            message = f"""
🔴 긴급 매도 신호 🔴
⏰ {current_time.strftime('%H:%M:%S')} KST

⚠️ {alert['message']}

📊 매도 고려사항:
• 현재 포지션 즉시 점검
• 손절 또는 부분 매도 고려
• 추가 하락 위험 대비

💸 신속한 매도 검토 바랍니다
🤖 Alpha Seeker v4.3 Enhanced Final
"""
            self.telegram_bot.send_message(message, urgent=True)
            logging.warning(f"긴급 매도 신호: {alert['message']}")
            
        elif alert['type'] == 'WARNING':
            message = f"""
💡 Alpha Seeker 주의 신호
⏰ {current_time.strftime('%H:%M:%S')} KST

📈 {alert['message']}

📝 참고사항: 지속적 모니터링 권장
🤖 Alpha Seeker v4.3 Enhanced Final
"""
            self.telegram_bot.send_message(message)
            logging.info(f"주의 알림 전송: {alert['message']}")
            
        elif alert['type'] == 'INFO':
            message = f"""
ℹ️ Alpha Seeker 정보 알림
⏰ {current_time.strftime('%H:%M:%S')} KST

📊 {alert['message']}

📝 시장 환경 참고 정보
🤖 Alpha Seeker v4.3 Enhanced Final
"""
            self.telegram_bot.send_message(message)
            logging.info(f"정보 알림 전송: {alert['message']}")
        
        # 알림 기록 업데이트
        self.alert_history[alert_key] = current_time
    
    def stop_monitoring(self):
        """모니터링 중지"""
        self.monitoring = False
        print("🛑 실시간 위험 모니터링 중지")
        logging.info("실시간 위험 모니터링 중지")

print("✅ RealtimeRiskMonitor Enhanced (24시간 실시간 위험 감지 + 긴급 매수/매도 신호)")
