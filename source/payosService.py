# Copyright (c) 2026 vanphat111 <phathovan14122006@email.com> | All rights reserved
# payosService.py

import os
import time
from payos import PayOS
from payos.type import PaymentData
from utils import log

payos = None

if os.getenv("PAYOS_CLIENT_ID") and os.getenv("PAYOS_API_KEY") and os.getenv("PAYOS_CHECKSUM_KEY"):
    try:
        payos = PayOS(
            client_id=os.getenv("PAYOS_CLIENT_ID"),
            api_key=os.getenv("PAYOS_API_KEY"),
            checksum_key=os.getenv("PAYOS_CHECKSUM_KEY")
        )
    except Exception as e:
        log("ERROR", f"Không thể khởi tạo SDK PayOS: {e}")

def create_donate_link(chat_id: str, username: str, amount: int):
    if not payos:
        log("ERROR", f"Chức năng Donate chưa được cấu hình. Bỏ qua yêu cầu từ: {chat_id}")
        return None, None, None
        
    try:
        order_code = int(time.time() * 1000) % 100000000
        
        user_clean = username.replace("@", "") if username else f"User{chat_id[:4]}"
        description = f"{user_clean} donate to UTH_calendar"[:25] 
        
        payment_data = PaymentData(
            orderCode=order_code,
            amount=amount,
            description=description,
            cancelUrl="https://t.me/uth_calendar_bot",
            returnUrl="https://t.me/uth_calendar_bot"
        )
        
        response = payos.createPaymentLink(payment_data)
        return response.checkoutUrl, response.qrCode, order_code
    except Exception as e:
        log("ERROR", f"Lỗi tạo link payOS cho {chat_id}: {e}")
        return None, None, None