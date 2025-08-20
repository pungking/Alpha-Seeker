"""
Alpha Seeker v4.3 시스템 설정
"""

# API 설정
PERPLEXITY_MODEL = "llama-3.1-sonar-large-128k-online"
PERPLEXITY_TIMEOUT = 30
PERPLEXITY_TEMPERATURE = 0.2
PERPLEXITY_MAX_TOKENS = 2000

# 기술적 분석 설정
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
BOLLINGER_PERIOD = 20
BOLLINGER_STD = 2

# 분석 기준
MIN_TECHNICAL_SCORE = 4.0
MAX_STOCKS_ANALYSIS = 8
TOP_RECOMMENDATIONS = 5
MIN_DATA_POINTS = 50

# 갭 분석 기준
LARGE_GAP_THRESHOLD = 7.0  # %
ATTENTION_GAP_THRESHOLD = 3.0  # %

# 리스크 관리
MAX_INDIVIDUAL_WEIGHT = 25  # %
STOP_LOSS_THRESHOLD = -7.0  # %
VIX_WARNING_LEVEL = 30
VIX_DANGER_LEVEL = 35

# 데이터 파일 설정
DATA_DIR = 'data'
MORNING_PICKS_FILE = 'morning_picks.json'
EVENING_ANALYSIS_FILE = 'evening_analysis.json'
DISCOVERED_TICKERS_FILE = 'discovered_tickers.json'

# 시간 설정
ANALYSIS_HOURS = {
    'morning_start': 5,
    'morning_end': 8,
    'evening_start': 21,
    'evening_end': 23,
    'sunday_start': 17,
    'sunday_end': 19
}

# 텔레그램 설정
TELEGRAM_TIMEOUT = 15
TELEGRAM_PARSE_MODE = 'Markdown'
TELEGRAM_MAX_MESSAGE_LENGTH = 4096

# 로깅 설정
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

# print 문 제거! (import 시 오류 방지)
