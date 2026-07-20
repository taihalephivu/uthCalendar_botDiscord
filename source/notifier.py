# Copyright (c) 2026 vanphat111 <phathovan14122006@email.com> | All rights reserved
# notifier.py

import os
import requests
from utils import log

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

def send_discord_message(user_id, text, photo_url=None):
    """Gửi tin nhắn trực tiếp (DM) qua Discord API"""
    if not DISCORD_TOKEN:
        log("ERROR", "DISCORD_TOKEN chưa được cấu hình!")
        return

    headers = {
        "Authorization": f"Bot {DISCORD_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        # 1. Mở kênh chat riêng (DM) với user
        dm_payload = {"recipient_id": user_id}
        r = requests.post("https://discord.com/api/v10/users/@me/channels", headers=headers, json=dm_payload)
        r.raise_for_status()
        channel_id = r.json().get("id")
        
        # 2. Xử lý giao diện Embed cho đẹp mắt
        embed = {
            "color": 0x5865F2, # Màu xanh Discord (Blurple)
            "timestamp": __import__("datetime").datetime.utcnow().isoformat() + "Z",
            "footer": {"text": "UTH Calendar Bot"}
        }
        
        lines = text.strip().split('\n')
        # Lấy dòng đầu làm Tiêu đề nếu nó chứa icon biểu tượng
        if len(lines) > 1 and any(icon in lines[0] for icon in ['📅', '🔔', '🎉', '❌', '✅']):
            embed["title"] = lines[0].replace('**', '').strip()
            
            content_lines = lines[1:]
            if content_lines and "━━━━" in content_lines[0]:
                content_lines.pop(0) # Xoá đường kẻ ngang cũ vì Embed đã có viền
                
            embed["description"] = '\n'.join(content_lines).strip()
        else:
            embed["description"] = text
            
        if not embed.get("description"):
            embed["description"] = " "
            
        if photo_url:
            embed["image"] = {"url": photo_url}
            
        msg_payload = {"embeds": [embed]}
            
        res = requests.post(f"https://discord.com/api/v10/channels/{channel_id}/messages", headers=headers, json=msg_payload)
        res.raise_for_status()
    except Exception as e:
        log("ERROR", f"Lỗi gửi tin nhắn Discord cho {user_id}: {e}")

def send_message(platform, user_id, text, photo_url=None):
    """Hàm trung tâm phân phối tin nhắn đến các nền tảng"""
    if platform == "discord":
        send_discord_message(user_id, text, photo_url)
    elif platform == "telegram":
        # log("WARN", "Nền tảng telegram đã bị loại bỏ.")
        pass
    else:
        log("WARN", f"Nền tảng {platform} không được hỗ trợ.")
