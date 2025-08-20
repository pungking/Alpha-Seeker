import json
import os
import re
import yfinance as yf
from datetime import datetime

class StockTickerManager:
    def __init__(self):
        self.discovered_tickers_file = 'data/discovered_tickers.json'
        self.company_ticker_map_file = 'data/company_ticker_map.json'
        self.ensure_data_dir()
        
    def ensure_data_dir(self):
        """데이터 디렉토리 생성"""
        os.makedirs('data', exist_ok=True)
    
    def load_discovered_tickers(self):
        """발견된 티커 목록 로드"""
        try:
            if not os.path.exists(self.discovered_tickers_file):
                return set()
                
            with open(self.discovered_tickers_file, 'r') as f:
                data = json.load(f)
                return set(data.get('tickers', []))
        except Exception:
            return set()
    
    def load_company_ticker_map(self):
        """회사명-티커 매핑 로드 (동적)"""
        try:
            if not os.path.exists(self.company_ticker_map_file):
                return {}
                
            with open(self.company_ticker_map_file, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def save_company_ticker_map(self, mapping):
        """회사명-티커 매핑 저장 (동적)"""
        try:
            with open(self.company_ticker_map_file, 'w') as f:
                json.dump(mapping, f, indent=2)
        except Exception:
            pass
    
    def validate_ticker(self, ticker):
        """티커가 실제 존재하는 주식인지 검증"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # 기본 정보가 있는지 확인
            if info.get('symbol') and info.get('longName'):
                return True
            return False
            
        except Exception:
            return False
    
    def discover_company_from_ticker(self, ticker):
        """티커에서 회사명 역추론 (동적 학습)"""
        try:
            if self.validate_ticker(ticker):
                stock = yf.Ticker(ticker)
                info = stock.info
                company_name = info.get('longName', '').upper()
                
                # 회사명에서 주요 키워드 추출
                keywords = []
                if company_name:
                    # 'INC', 'CORP', 'LTD' 등 제거
                    clean_name = re.sub(r'\b(INC|CORP|CORPORATION|LTD|LIMITED|CO|COMPANY)\b', '', company_name)
                    # 주요 단어들 추출
                    words = re.findall(r'\b[A-Z]{3,}\b', clean_name)
                    keywords = [w for w in words if len(w) >= 3]
                
                return keywords
        except Exception:
            pass
        return []
    
    def extract_tickers_from_text(self, text):
        """텍스트에서 티커 추출 (완전 동적)"""
        print("🔍 완전 동적 티커 추출 시작...")
        
        # 기존 발견된 티커들과 매핑 로드
        known_tickers = self.load_discovered_tickers()
        company_map = self.load_company_ticker_map()
        
        verified_tickers = []
        new_tickers = []
        new_mappings = {}
        
        # 1. 명시적 티커 패턴 추출 (가장 확실한 방법)
        ticker_patterns = [
            r'\b[A-Z]{2,5}\b',           # 기본 패턴 AAPL, MSFT
            r'(?:NYSE:|NASDAQ:)([A-Z]{2,5})',  # NYSE:AAPL
            r'\$([A-Z]{2,5})\b',         # $AAPL
            r'\(([A-Z]{2,5})\)',         # (AAPL)
        ]
        
        text_upper = text.upper()
        potential_tickers = set()
        
        for pattern in ticker_patterns:
            matches = re.findall(pattern, text_upper)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0] if match else match[-1]
                if 2 <= len(match) <= 5:
                    potential_tickers.add(match)
        
        # 2. 회사명 패턴 추출 (동적 추론)
        company_patterns = [
            r'([A-Z][A-Za-z]{2,15})\s*(?:\([A-Z]{2,5}\))',  # Apple (AAPL)
            r'([A-Z][A-Za-z]{2,15})\s+(?:Inc|Corp|Ltd)',    # Tesla Inc
            r'([A-Z][A-Za-z]{2,15})\s+(?:주식|종목)',        # Tesla 주식
        ]
        
        for pattern in company_patterns:
            matches = re.findall(pattern, text)
            for company in matches:
                company_upper = company.upper()
                # 기존 매핑에서 확인
                if company_upper in company_map:
                    ticker = company_map[company_upper]
                    if ticker not in potential_tickers:
                        potential_tickers.add(ticker)
                        print(f"📋 매핑에서 발견: {company} → {ticker}")
        
        # 3. 실제 검증 및 동적 학습
        for ticker in potential_tickers:
            if ticker in known_tickers:
                verified_tickers.append(ticker)
                continue
            
            print(f"🔍 새 티커 검증 중: {ticker}")
            if self.validate_ticker(ticker):
                verified_tickers.append(ticker)
                new_tickers.append(ticker)
                
                # 역추론으로 회사명 학습
                company_keywords = self.discover_company_from_ticker(ticker)
                for keyword in company_keywords:
                    new_mappings[keyword] = ticker
                
                print(f"✅ 새 티커 학습: {ticker} → {company_keywords}")
            else:
                print(f"❌ 무효 티커: {ticker}")
        
        # 4. 새로운 발견 저장
        if new_tickers:
            all_tickers = known_tickers.union(set(new_tickers))
            ticker_data = {
                'tickers': list(all_tickers),
                'total_count': len(all_tickers),
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.discovered_tickers_file, 'w') as f:
                json.dump(ticker_data, f, indent=2)
        
        if new_mappings:
            company_map.update(new_mappings)
            self.save_company_ticker_map(company_map)
            print(f"🧠 새 매핑 학습: {len(new_mappings)}개")
        
        print(f"✅ 완전 동적 추출 완료: {len(verified_tickers)}개 티커")
        return verified_tickers
    
    def get_stock_basic_info(self, ticker):
        """주식 기본 정보 조회"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            return {
                'symbol': ticker,
                'name': info.get('longName', ticker),
                'sector': info.get('sector', 'Unknown'),
                'market_cap': info.get('marketCap', 0),
                'exchange': info.get('exchange', 'Unknown')
            }
        except Exception as e:
            print(f"⚠️ {ticker} 기본 정보 조회 실패: {e}")
            return None

print("✅ 완전 동적 StockTickerManager 모듈 로드 완료")
