# Copyright (c) 2026 vanphat111 <phathovan14122006@email.com> | All rights reserved
# main.py

import os, sys
import database as db
import task
from utils import log
import discordBot

critical_vars = ["DISCORD_TOKEN", "CELERY_BROKER_URL"]
missing_critical = [v for v in critical_vars if not os.getenv(v)]
if missing_critical:
    log("CRITICAL", f"Thiếu các biến môi trường bắt buộc: {', '.join(missing_critical)}. Dừng hệ thống!")
    sys.exit(1)
log("SUCCESS", "Cấu hình hệ thống cốt lõi đã tải thành công.")

weather_enabled = bool(os.getenv("WEATHER_API_KEY"))
if weather_enabled:
    log("SUCCESS", "Cấu hình WeatherAPI hợp lệ. Kích hoạt chức năng thời tiết.")
else:
    log("WARN", "Thiếu WEATHER_API_KEY. Hủy bỏ chức năng thời tiết.")

# cron jobs moved to Celery Beat

if __name__ == "__main__":
    db.initDb()

    if weather_enabled:
        task.updateWeatherTask.delay()
    
    # Chạy Discord Bot ở thread chính
    log("SYSTEM", "Đang khởi động bot Discord...")
    discordBot.run()