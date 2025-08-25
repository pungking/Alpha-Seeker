import os
import time
import threading
import logging
from dotenv import load_dotenv

class TelegramBot:
    def __init__(self):
        load_dotenv()
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.emergency_chat_id = os.getenv('EMERGENCY_CHAT_ID')  # 긴급 알림용
        
    def send_message(self, message, urgent=False, emergency=False):
        """
        메시지 전송 (긴급도별 구분)
        - normal: 일반 알림
        - urgent: 중요 알림 (⚠️ 표시)
        - emergency: 긴급 알림 (여러 채널 + 반복)
        """
        try:
            import requests
            
            # 메시지 포맷팅
            if emergency:
                formatted_message = f"🚨🚨🚨 긴급 알림 🚨🚨🚨\n\n{message}"
                target_chats = [self.chat_id, self.emergency_chat_id] if self.emergency_chat_id else [self.chat_id]
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
                    else:
                        logging.error(f"텔레그램 전송 실패: {response.status_code} - {response.text}")
            
            # 긴급 알림의 경우 후속 알림 스케줄
            if emergency and success_count > 0:
                self._schedule_emergency_followup(formatted_message)
            
            logging.info(f"텔레그램 전송 완료: {success_count}/{len(target_chats)} 채널")
            return success_count > 0
            
        except Exception as e:
            print(f"❌ 텔레그램 전송 오류: {e}")
            logging.error(f"텔레그램 전송 오류: {e}")
            return False
    
    def _schedule_emergency_followup(self, message):
        """긴급 알림 후속 처리"""
        def followup():
            time.sleep(300)  # 5분 후
            followup_msg = f"📢 5분 전 긴급 알림 재확인 필요\n\n{message[:200]}..."
            self.send_message(followup_msg, urgent=True)
        
        # 백그라운드로 후속 알림 스케줄
        threading.Thread(target=followup, daemon=True).start()

print("✅ TelegramBot Enhanced (긴급 알림 시스템)")
