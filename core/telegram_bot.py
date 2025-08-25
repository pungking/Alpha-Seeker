import os
import time
import threading
import logging
from datetime import datetime
from dotenv import load_dotenv


class TelegramBot:
    def __init__(self):
        load_dotenv()
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.emergency_chat_id = os.getenv('EMERGENCY_CHAT_ID')
        
    def send_message(self, message, urgent=False, emergency=False):
        """메시지 전송 (재시도 로직 강화)"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                import requests
                
                # 메시지 포맷팅
                if emergency:
                    formatted_message = f"🚨🚨🚨 긴급 알림 🚨🚨🚨\n\n{message}"
                    target_chats = ([self.chat_id, self.emergency_chat_id] 
                                  if self.emergency_chat_id else [self.chat_id])
                elif urgent:
                    formatted_message = f"⚠️ 중요 알림 ⚠️\n\n{message}"
                    target_chats = [self.chat_id]
                else:
                    formatted_message = message
                    target_chats = [self.chat_id]
                
                # 여러 채널에 전송
                success_count = 0
                for chat_id in target_chats:
                    if chat_id:
                        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                        payload = {
                            'chat_id': chat_id,
                            'text': formatted_message,
                            'parse_mode': 'HTML'
                        }
                        
                        response = requests.post(url, data=payload, timeout=30)
                        if response.status_code == 200:
                            success_count += 1
                            logging.info(f"텔레그램 전송 성공 (시도 {attempt + 1}): {chat_id}")
                        else:
                            logging.error(f"텔레그램 전송 실패: {response.status_code} - {response.text}")
                
                if success_count > 0:
                    # 긴급 알림의 경우 후속 알림 스케줄
                    if emergency:
                        self._schedule_emergency_followup(formatted_message)
                    
                    logging.info(f"텔레그램 전송 완료: {success_count}/{len(target_chats)} 채널")
                    return True
                
                # 전송 실패 시 재시도 대기
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # 지수 백오프
                    logging.warning(f"텔레그램 전송 실패, {wait_time}초 후 재시도 ({attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    
            except Exception as e:
                logging.error(f"텔레그램 전송 오류 (시도 {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        
        # 최종 실패 시 로컬 파일에 백업
        self._backup_failed_message(formatted_message, urgent, emergency)
        return False
    
    def _backup_failed_message(self, message, urgent, emergency):
        """실패한 메시지 로컬 백업"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            priority = "EMERGENCY" if emergency else "URGENT" if urgent else "NORMAL"
            
            with open('failed_messages.log', 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] [{priority}] {message}\n")
                f.write("-" * 80 + "\n")
                
            logging.error(f"텔레그램 전송 최종 실패 - 로컬 백업 완료: {priority}")
            
        except Exception as e:
            logging.critical(f"메시지 백업도 실패: {e}")
    
    def _schedule_emergency_followup(self, message):
        """긴급 알림 후속 처리"""
        def followup():
            time.sleep(300)  # 5분 후
            followup_msg = f"📢 5분 전 긴급 알림 재확인 필요\n\n{message[:200]}..."
            self.send_message(followup_msg, urgent=True)
        
        # 백그라운드로 후속 알림 스케줄
        threading.Thread(target=followup, daemon=True).start()


print("✅ TelegramBot Enhanced (재시도 로직 + 실패 백업)")
