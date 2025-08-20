import os
import asyncio
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import requests
from telegram import Bot
from telegram.error import TelegramError
import time
import random

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
    
    def safe_get_stock_data(self, symbol, max_retries=3):
        """안전한 주식 데이터 수집 (429 에러 대응)"""
        for attempt in range(max_retries):
            try:
                # 요청 간 랜덤 지연 (1-3초)
                delay = random.uniform(1, 3)
                time.sleep(delay)
                
                print(f"📊 {symbol} 데이터 수집 중... (시도 {attempt + 1})")
                
                stock = yf.Ticker(symbol)
                hist = stock.history(period="5d")
                
                if len(hist) >= 2:
                    current_price = hist['Close'][-1]
                    prev_price = hist['Close'][-2]
                    change = current_price - prev_price
                    change_pct = (change / prev_price) * 100
                    volume = hist['Volume'][-1]
                    
                    # 간단한 기술적 지표
                    sma_5 = hist['Close'].tail(5).mean()
                    price_vs_sma = ((current_price - sma_5) / sma_5) * 100
                    
                    return {
                        'symbol': symbol,
                        'price': round(current_price, 2),
                        'change': round(change, 2),
                        'change_pct': round(change_pct, 2),
                        'volume': int(volume),
                        'price_vs_sma': round(price_vs_sma, 2),
                        'success': True
                    }
                else:
                    print(f"⚠️ {symbol}: 데이터 부족")
                    return None
                    
            except Exception as e:
                print(f"❌ {symbol} 시도 {attempt + 1} 실패: {e}")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5  # 지수적 백오프
                    print(f"   ⏳ {wait_time}초 후 재시도...")
                    time.sleep(wait_time)
                else:
                    print(f"   💀 {symbol} 최종 실패")
                    return None
        
        return None
    
    def analyze_stock_signals(self, stock_data):
        """간단하지만 효과적인 신호 생성"""
        if not stock_
            return None
            
        signals = []
        score = 0
        
        # 가격 변동 신호
        change_pct = stock_data['change_pct']
        if change_pct > 2:
            signals.append(f"🚀 강한 상승 (+{change_pct:.1f}%)")
            score += 3
        elif change_pct > 0.5:
            signals.append(f"📈 상승 중 (+{change_pct:.1f}%)")
            score += 1
        elif change_pct < -2:
            signals.append(f"📉 급락 주의 ({change_pct:.1f}%)")
            score -= 2
        
        # 거래량 신호 (간단한 추정)
        if stock_data['volume'] > 5000000:  # 500만주 이상
            signals.append("🔊 높은 거래량")
            score += 1
        
        # 5일 평균 대비 신호
        price_vs_sma = stock_data['price_vs_sma']
        if price_vs_sma > 3:
            signals.append("💪 5일 평균 상회")
            score += 1
        elif price_vs_sma < -3:
            signals.append("🛡️ 5일 평균 하회 - 반등 대기")
            score += 0.5
        
        stock_data['signals'] = signals
        stock_data['score'] = score
        
        return stock_data
    
    def get_market_news(self):
        """Perplexity AI로 시장 뉴스 분석"""
        if not self.perplexity_key:
            return "미국 시장은 기술주와 AI 관련주를 중심으로 관심이 집중되고 있습니다. 주요 지수들은 혼조세를 보이고 있으며, 실적 발표 시즌에 주목이 필요합니다."
            
        try:
            print("📰 뉴스 분석 중...")
            url = "https://api.perplexity.ai/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.perplexity_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [
                    {
                        "role": "user", 
                        "content": "미국 주식 시장의 오늘 주요 뉴스를 3줄로 요약해주세요. 200자 이내로 간단히."
                    }
                ]
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content']
                return content[:300]
            else:
                return "현재 미국 시장은 안정적인 흐름을 보이고 있습니다."
                
        except Exception as e:
            print(f"뉴스 분석 오류: {e}")
            return "시장은 주요 기술주를 중심으로 관심이 집중되고 있습니다."
    
    async def run_analysis(self):
        """메인 분석 실행 (429 에러 방지 버전)"""
        print("🚀 Alpha Seeker 안전 분석 시작")
        
        # 1. 분석 대상을 5개로 제한 (429 에러 방지)
        watchlist = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA']
        
        # 2. 주식 데이터 수집 (안전하게)
        print("📊 주식 데이터 안전 수집 중...")
        analyzed_stocks = []
        
        for i, symbol in enumerate(watchlist, 1):
            print(f"진행률: {i}/{len(watchlist)}")
            
            stock_data = self.safe_get_stock_data(symbol)
            if stock_
                analyzed_stock = self.analyze_stock_signals(stock_data)
                if analyzed_stock and analyzed_stock['signals']:
                    analyzed_stocks.append(analyzed_stock)
                    print(f"✅ {symbol}: Score {analyzed_stock['score']}")
            
            # 종목 간 2초 대기 (필수!)
            if i < len(watchlist):
                time.sleep(2)
        
        # 3. 시장 뉴스
        news = self.get_market_news()
        
        # 4. 상위 종목 선별
        top_stocks = sorted(analyzed_stocks, key=lambda x: x['score'], reverse=True)[:5]
        
        # 5. 리포트 생성
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        report = f"""
🚀 **Alpha Seeker 리포트**  
📅 {current_time} (KST)

📊 **추천 종목 TOP {len(top_stocks)}**
"""
        
        if top_stocks:
            for i, stock in enumerate(top_stocks, 1):
                emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}️⃣"
                
                report += f"""
{emoji} **{stock['symbol']}**
💰 ${stock['price']} ({stock['change_pct']:+.1f}%)
📊 점수: {stock['score']:.1f}
"""
                # 신호 표시
                for signal in stock['signals'][:2]:
                    report += f"   • {signal}\n"
        else:
            report += "\n현재 특별한 신호를 보이는 종목이 없습니다."
        
        report += f"""

📰 **시장 뉴스**  
{news}

⚠️ **투자 주의사항**
• 이 리포트는 투자 참고용이며 투자 결정은 개인 책임입니다
• 손실 가능성을 충분히 고려하여 투자하세요

⏰ 다음 분석: 자동 스케줄링 중
"""
        
        # 6. 텔레그램 전송
        print("📱 텔레그램 전송 중...")
        success = await self.send_telegram_message(report)
        
        if success:
            print("🎉 분석 완료 및 알림 전송 성공!")
            print(f"📊 분석 종목: {len(analyzed_stocks)}개")
        else:
            print("⚠️ 분석은 완료되었으나 알림 전송 실패")
            
        print("=" * 50)
        print("📊 Alpha Seeker 리포트:")
        print(report)
        print("=" * 50)

async def main():
    seeker = AlphaSeeker()
    await seeker.run_analysis()

if __name__ == "__main__":
    asyncio.run(main())
