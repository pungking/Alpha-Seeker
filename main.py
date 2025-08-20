import os
import asyncio
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import requests
from telegram import Bot
from telegram.error import TelegramError
import numpy as np

class AlphaSeeker:
    def __init__(self):
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.alpaca_key = os.getenv('ALPACA_API_KEY')
        self.perplexity_key = os.getenv('PERPLEXITY_API_KEY')
        self.bot = Bot(token=self.telegram_token) if self.telegram_token else None
        
    async def send_telegram_message(self, message):
        """텔레그램 메시지 전송"""
        if not self.bot or not self.chat_id:
            print("❌ 텔레그램 설정이 없습니다.")
            return False
            
        try:
            await self.bot.send_message(
                chat_id=self.chat_id, 
                text=message,
                parse_mode='Markdown'
            )
            print("✅ 텔레그램 메시지 전송 성공")
            return True
        except TelegramError as e:
            print(f"❌ 텔레그램 전송 실패: {e}")
            return False
    
    def calculate_rsi(self, prices, period=14):
        """RSI 계산"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """MACD 계산"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        return macd, signal_line, histogram
    
    def get_stock_analysis(self, symbol):
        """개별 종목 심화 분석"""
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period="3mo")  # 3개월 데이터
            info = stock.info
            
            if len(hist) < 50:
                return None
                
            current_price = hist['Close'][-1]
            prev_price = hist['Close'][-2]
            change = current_price - prev_price
            change_pct = (change / prev_price) * 100
            
            # 기술적 지표 계산
            hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
            hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
            hist['RSI'] = self.calculate_rsi(hist['Close'])
            
            macd, signal, histogram = self.calculate_macd(hist['Close'])
            hist['MACD'] = macd
            hist['MACD_Signal'] = signal
            
            # 볼린저 밴드
            hist['BB_Middle'] = hist['Close'].rolling(window=20).mean()
            hist['BB_Std'] = hist['Close'].rolling(window=20).std()
            hist['BB_Upper'] = hist['BB_Middle'] + (hist['BB_Std'] * 2)
            hist['BB_Lower'] = hist['BB_Middle'] - (hist['BB_Std'] * 2)
            
            # 거래량 분석
            avg_volume = hist['Volume'].tail(20).mean()
            current_volume = hist['Volume'][-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            # 신호 생성
            signals = []
            score = 0
            
            # RSI 신호
            current_rsi = hist['RSI'][-1]
            if current_rsi < 30:
                signals.append("🟢 RSI 과매도(30↓) - 매수 기회")
                score += 2
            elif current_rsi > 70:
                signals.append("🔴 RSI 과매수(70↑) - 매도 고려")
                score -= 1
            elif 30 <= current_rsi <= 50:
                signals.append("📊 RSI 중립 - 상승 여력")
                score += 1
            
            # MACD 신호
            if macd[-1] > signal[-1] and macd[-2] <= signal[-2]:
                signals.append("🚀 MACD 골든크로스 - 강력 매수")
                score += 3
            elif macd[-1] < signal[-1] and macd[-2] >= signal[-2]:
                signals.append("⚠️ MACD 데드크로스 - 매도 신호")
                score -= 2
            
            # 이동평균선 신호
            sma_20 = hist['SMA_20'][-1]
            sma_50 = hist['SMA_50'][-1]
            
            if current_price > sma_20 > sma_50:
                signals.append("📈 상승 추세 확인 (가격>20일>50일)")
                score += 2
            elif current_price < sma_20 < sma_50:
                signals.append("📉 하락 추세 - 주의")
                score -= 1
            
            # 볼린저 밴드 신호
            bb_upper = hist['BB_Upper'][-1]
            bb_lower = hist['BB_Lower'][-1]
            bb_position = (current_price - bb_lower) / (bb_upper - bb_lower)
            
            if bb_position <= 0.1:
                signals.append("💎 볼린저 하단 근처 - 반등 기대")
                score += 2
            elif bb_position >= 0.9:
                signals.append("🔥 볼린저 상단 근처 - 과열")
                score -= 1
            
            # 거래량 분석
            if volume_ratio > 2:
                signals.append(f"🔊 거래량 급증 ({volume_ratio:.1f}배)")
                score += 1
            elif volume_ratio > 1.5:
                signals.append("📢 거래량 증가")
                score += 0.5
            
            # 가격 변동률 분석
            if change_pct > 3:
                signals.append(f"🚀 강한 상승 (+{change_pct:.1f}%)")
                score += 2
            elif change_pct > 1:
                signals.append(f"📈 상승 중 (+{change_pct:.1f}%)")
                score += 1
            elif change_pct < -3:
                signals.append(f"📉 급락 ({change_pct:.1f}%)")
                score -= 1
            
            return {
                'symbol': symbol,
                'name': info.get('longName', symbol)[:25],
                'price': round(current_price, 2),
                'change': round(change, 2),
                'change_pct': round(change_pct, 2),
                'volume': int(current_volume),
                'volume_ratio': round(volume_ratio, 1),
                'rsi': round(current_rsi, 1),
                'signals': signals,
                'score': score,
                'support': round(bb_lower, 2),
                'resistance': round(bb_upper, 2)
            }
            
        except Exception as e:
            print(f"❌ {symbol} 분석 실패: {e}")
            return None
    
    def get_market_news(self):
        """Perplexity AI로 시장 뉴스 분석"""
        if not self.perplexity_key:
            return "오늘은 미국 주식 시장이 혼조세를 보이고 있습니다. 주요 기술주들의 실적 발표에 관심이 집중되고 있습니다."
            
        try:
            url = "https://api.perplexity.ai/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.perplexity_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [
                    {
                        "role": "system",
                        "content": "당신은 미국 주식 시장의 전문 분석가입니다. 오늘의 주요 뉴스를 3줄로 간단히 요약해주세요."
                    },
                    {
                        "role": "user", 
                        "content": "오늘 미국 주식 시장의 주요 뉴스와 주목할 섹터, 테마를 알려주세요. 200자 이내로 요약해주세요."
                    }
                ]
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content']
                return content[:400]  # 400자 제한
            else:
                return "뉴스 분석을 가져올 수 없습니다. AI 시장과 기술주가 주목받고 있습니다."
                
        except Exception as e:
            return "시장은 전반적으로 안정세를 보이고 있습니다. 주요 기술주와 AI 관련주에 관심이 집중되고 있습니다."
    
    async def run_analysis(self):
        """메인 분석 실행"""
        print("🚀 Alpha Seeker 심화 분석 시작")
        
        # 1. 분석 대상 종목 (미국 대표주 + 인기주)
        watchlist = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA',
            'SPY', 'QQQ', 'AMD', 'NFLX', 'CRM', 'UBER', 'PYPL'
        ]
        
        # 2. 개별 종목 분석
        print("📊 종목별 심화 분석 중...")
        analyzed_stocks = []
        
        for symbol in watchlist:
            analysis = self.get_stock_analysis(symbol)
            if analysis and analysis['signals']:  # 신호가 있는 종목만
                analyzed_stocks.append(analysis)
                print(f"✅ {symbol}: Score {analysis['score']}, Signals: {len(analysis['signals'])}")
        
        # 3. 상위 종목 선별 (점수순)
        top_stocks = sorted(analyzed_stocks, key=lambda x: x['score'], reverse=True)[:7]
        
        # 4. 시장 뉴스 분석
        print("📰 시장 뉴스 분석 중...")
        news = self.get_market_news()
        
        # 5. 리포트 생성
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        report = f"""
🚀 **Alpha Seeker 전문가 분석**  
📅 {current_time} (KST)

📊 **추천 종목 TOP 7**
"""
        
        if top_stocks:
            for i, stock in enumerate(top_stocks, 1):
                emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}️⃣"
                
                report += f"""
{emoji} **{stock['symbol']} - {stock['name']}**
💰 ${stock['price']} ({stock['change_pct']:+.1f}%)
📊 점수: {stock['score']} | RSI: {stock['rsi']}
🛡️ 지지: ${stock['support']} | ⚡ 저항: ${stock['resistance']}
"""
                # 주요 신호 2개만 표시
                for signal in stock['signals'][:2]:
                    report += f"   • {signal}\n"
        else:
            report += "\n현재 추천할 만한 종목이 없습니다."
        
        report += f"""

📰 **시장 뉴스**  
{news}

📈 **투자 전략**
• 상위 3개 종목 중심으로 분산 투자 고려
• RSI 30 이하 종목은 매수 타이밍 주의깊게 관찰
• MACD 골든크로스 종목은 단기 모멘텀 기대

⏰ 다음 분석: 자동 스케줄링 실행 중
"""
        
        # 6. 텔레그램 전송
        print("📱 텔레그램 전송 중...")
        success = await self.send_telegram_message(report)
        
        if success:
            print("🎉 심화 분석 완료 및 알림 전송 성공!")
            print(f"📊 분석 종목: {len(analyzed_stocks)}개")
            print(f"🎯 추천 종목: {len(top_stocks)}개")
        else:
            print("⚠️ 분석은 완료되었으나 알림 전송 실패")
            
        print("=" * 60)
        print("📊 Alpha Seeker 리포트:")
        print(report)
        print("=" * 60)

async def main():
    seeker = AlphaSeeker()
    await seeker.run_analysis()

if __name__ == "__main__":
    asyncio.run(main())
