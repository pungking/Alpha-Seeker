import json
import os
import shutil
import logging
from datetime import datetime


class DataManager:
    def __init__(self):
        self.data_dir = "data"
        self.backup_dir = "backups"
        self.morning_file = f"{self.data_dir}/morning_picks.json"
        self.evening_file = f"{self.data_dir}/evening_results.json"
        self.logger = logging.getLogger(__name__)
        
        # 디렉터리 생성
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def save_morning_data(self, data):
        """오전 데이터 저장 + 백업"""
        try:
            # 기존 파일 백업
            self._backup_file(self.morning_file, "morning_picks")
            
            with open(self.morning_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"오전 데이터 저장 완료: {len(data.get('stock_analysis', {}))}개 종목")
            
        except Exception as e:
            self.logger.error(f"오전 데이터 저장 실패: {e}")
            raise
    
    def save_evening_data(self, data):
        """저녁 데이터 저장 + 백업"""
        try:
            # 기존 파일 백업
            self._backup_file(self.evening_file, "evening_results")
            
            with open(self.evening_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"저녁 데이터 저장 완료: 유지 {len(data.get('maintained', []))}개")
            
        except Exception as e:
            self.logger.error(f"저녁 데이터 저장 실패: {e}")
            raise
    
    def load_morning_data(self):
        """오전 데이터 로드"""
        try:
            if not os.path.exists(self.morning_file):
                self.logger.warning("오전 데이터 파일 없음")
                return None
            
            with open(self.morning_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.logger.info("오전 데이터 로드 완료")
            return data
            
        except Exception as e:
            self.logger.error(f"오전 데이터 로드 실패: {e}")
            return None
    
    def load_evening_data(self):
        """저녁 데이터 로드"""
        try:
            if not os.path.exists(self.evening_file):
                self.logger.warning("저녁 데이터 파일 없음")
                return None
            
            with open(self.evening_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.logger.info("저녁 데이터 로드 완료")
            return data
            
        except Exception as e:
            self.logger.error(f"저녁 데이터 로드 실패: {e}")
            return None
    
    def get_data_status(self):
        """데이터 상태 확인"""
        return {
            'morning_data_exists': os.path.exists(self.morning_file),
            'evening_data_exists': os.path.exists(self.evening_file),
            'morning_file_size': (os.path.getsize(self.morning_file) 
                                if os.path.exists(self.morning_file) else 0),
            'evening_file_size': (os.path.getsize(self.evening_file) 
                                if os.path.exists(self.evening_file) else 0)
        }
    
    def _backup_file(self, file_path, prefix):
        """개별 파일 백업"""
        try:
            if os.path.exists(file_path):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.basename(file_path)
                backup_path = f"{self.backup_dir}/{prefix}_{timestamp}.json"
                
                shutil.copy2(file_path, backup_path)
                self.logger.debug(f"파일 백업 완료: {backup_path}")
                
        except Exception as e:
            self.logger.error(f"파일 백업 실패 {file_path}: {e}")
    
    def backup_critical_data(self):
        """중요 데이터 전체 백업"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 백업할 파일 목록
            files_to_backup = [
                (self.morning_file, "morning_picks"),
                (self.evening_file, "evening_results"),
                ("alpha_seeker.log", "system_log"),
                ("failed_messages.log", "failed_messages")
            ]
            
            backup_count = 0
            for file_path, prefix in files_to_backup:
                if os.path.exists(file_path):
                    try:
                        backup_filename = (f"{prefix}_{timestamp}.json" if file_path.endswith('.json') 
                                         else f"{prefix}_{timestamp}.log")
                        backup_path = f"{self.backup_dir}/{backup_filename}"
                        shutil.copy2(file_path, backup_path)
                        backup_count += 1
                        
                    except Exception as e:
                        self.logger.error(f"개별 백업 실패 {file_path}: {e}")
            
            # 오래된 백업 파일 정리 (30일 이상)
            self._cleanup_old_backups(days=30)
            
            self.logger.info(f"전체 데이터 백업 완료: {backup_count}개 파일 ({timestamp})")
            return True
            
        except Exception as e:
            self.logger.error(f"전체 백업 실패: {e}")
            return False
    
    def _cleanup_old_backups(self, days=30):
        """오래된 백업 파일 정리"""
        try:
            import time
            cutoff_time = time.time() - (days * 24 * 60 * 60)
            
            cleanup_count = 0
            for filename in os.listdir(self.backup_dir):
                file_path = os.path.join(self.backup_dir, filename)
                
                if os.path.isfile(file_path) and os.path.getmtime(file_path) < cutoff_time:
                    os.remove(file_path)
                    cleanup_count += 1
            
            if cleanup_count > 0:
                self.logger.info(f"오래된 백업 파일 정리: {cleanup_count}개 파일 삭제")
                
        except Exception as e:
            self.logger.error(f"백업 파일 정리 실패: {e}")


print("✅ DataManager Enhanced (자동 백업 + 파일 정리)")
