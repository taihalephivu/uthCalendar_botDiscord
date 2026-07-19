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
        
        # 2. Gửi tin nhắn
        msg_payload = {"content": text}
        if photo_url:
            msg_payload["embeds"] = [{"image": {"url": photo_url}}]
            
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
