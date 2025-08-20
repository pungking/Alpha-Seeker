import json
import os
from datetime import datetime

# config import 제거하고 직접 정의 (import 에러 방지)
DATA_DIR = 'data'
MORNING_PICKS_FILE = 'morning_picks.json'
EVENING_ANALYSIS_FILE = 'evening_analysis.json'

class DataManager:
    def __init__(self):
        self.data_dir = DATA_DIR
        self.morning_picks_path = os.path.join(self.data_dir, MORNING_PICKS_FILE)
        self.evening_analysis_path = os.path.join(self.data_dir, EVENING_ANALYSIS_FILE)
        self.ensure_data_dir()
        
    def ensure_data_dir(self):
        """데이터 디렉토리 생성"""
        try:
            os.makedirs(self.data_dir, exist_ok=True)
        except Exception as e:
            pass
        
    def save_morning_data(self, data):
        """오전 분석 데이터 저장"""
        try:
            data['save_timestamp'] = datetime.now().isoformat()
            with open(self.morning_picks_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            return False
    
    def load_morning_data(self):
        """오전 분석 데이터 로드"""
        try:
            if not os.path.exists(self.morning_picks_path):
                return None
                
            with open(self.morning_picks_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 문법 오류 수정: 조건문 완성
            if not data or 'stock_analysis' not in data:
                return None
                
            return data
            
        except Exception as e:
            return None
    
    def save_evening_data(self, data):
        """저녁 분석 데이터 저장"""
        try:
            data['save_timestamp'] = datetime.now().isoformat()
            with open(self.evening_analysis_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            return False
    
    def load_evening_data(self):
        """저녁 분석 데이터 로드"""
        try:
            if not os.path.exists(self.evening_analysis_path):
                return None
                
            with open(self.evening_analysis_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            return data
            
        except Exception as e:
            return None
    
    def get_data_status(self):
        """데이터 상태 확인"""
        status = {
            'data_dir_exists': os.path.exists(self.data_dir),
            'morning_data_exists': os.path.exists(self.morning_picks_path),
            'evening_data_exists': os.path.exists(self.evening_analysis_path),
            'check_timestamp': datetime.now().isoformat()
        }
        return status
