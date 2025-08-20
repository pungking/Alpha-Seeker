import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# config import 제거하고 직접 정의
TELEGRAM_TIMEOUT = 15
TELEGRAM_PARSE_MODE = 'Markdown'
TELEGRAM_MAX_MESSAGE_LENGTH = 4096

class TelegramBot:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.timeout = TELEGRAM_TIMEOUT
        self.parse_mode = TELEGRAM_PARSE_MODE
        self.max_length = TELEGRAM_MAX_MESSAGE_LENGTH
        
        # print 제거
    
    def send_message(self, message):
        """텔레그램 메시지 전송"""
        if not self.token or not self.chat_id:
            return False
            
        try:
            messages = self._split_message(message)
            
            success_count = 0
            for i, msg in enumerate(messages):
                success = self._send_single_message(msg, i + 1, len(messages))
                if success:
                    success_count += 1
            
            return success_count == len(messages)
                
        except Exception as e:
            return False
    
    def _send_single_message(self, message, part_num=1, total_parts=1):
        """단일 메시지 전송"""
        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            
            if total_parts > 1:
                header = f"📄 **메시지 {part_num}/{total_parts}**\n\n"
                message = header + message
            
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': self.parse_mode
            }
            
            response = requests.post(url, data=data, timeout=self.timeout)
            return response.status_code == 200
                
        except Exception as e:
            return False
    
    def _split_message(self, message):
        """긴 메시지를 여러 개로 분할"""
        if len(message) <= self.max_length:
            return [message]
        
        messages = []
        current_message = ""
        lines = message.split('\n')
        
        for line in lines:
            if len(current_message + line + '\n') <= self.max_length:
                current_message += line + '\n'
            else:
                if current_message.strip():
                    messages.append(current_message.strip())
                current_message = line + '\n'
        
        if current_message.strip():
            messages.append(current_message.strip())
        
        return messages
    
    def send_test_message(self):
        """테스트 메시지 전송"""
        test_msg = f"""
🧪 **Alpha Seeker 테스트 메시지**
📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✅ 텔레그램 봇 연결 정상
🤖 Alpha Seeker v4.3 시스템 준비 완료
"""
        
        return self.send_message(test_msg)

# print 문 제거!
