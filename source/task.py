# Copyright (c) 2026 vanphat111 <phathovan14122006@email.com> | All rights reserved
# tasks.py

import os
from datetime import datetime
from celeryApp import app
import notifier
import courseService
import portalService
from utils import log
import json
import redisManager
import utils
import database as db

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

def sendWorkerCheckIn(_self, _chatId):
    workerName = _self.request.hostname

    try:
        log("INFO", f"[{workerName}] Đang xử lí lệnh cho user: {_chatId}")
    except Exception as e:
        log("ERROR", f"Không thể gửi báo danh: {e}")

# ==========================================
# 1. TASK ƯU TIÊN CAO (Dành cho User gọi lệnh)
# ==========================================

@app.task(bind=True, name='tasks.portalTask', queue='high_priority')
def portalTask(self, chatId, dateStr):
    sendWorkerCheckIn(self, chatId)
    try:
        msg = portalService.formatCalendarMessage(chatId, dateStr)
        if msg:
            notifier.send_message("discord", chatId, msg)
    except Exception as e:
        log("ERROR", f"Lỗi Portal Task cho {chatId}: {e}")

@app.task(bind=True, name='tasks.deadlineTask', queue='high_priority')
def deadlineTask(self, chatId):
    sendWorkerCheckIn(self, chatId)
    try:
        courseService.scanAllDeadlines(chatId, isManual=True)
    except Exception as e:
        log("ERROR", f"Lỗi Deadline Task cho {chatId}: {e}")

@app.task(bind=True, name='tasks.registrationTask')
def registrationTask(self, chatId, mssv, password):
    sendWorkerCheckIn(self, chatId)
    success, resultMsg = portalService.verifyAndSaveUser(chatId, mssv, password)
    if success:
        resultMsg += "\n\nBây giờ bạn có thể xem lịch và deadline rồi đó."
    notifier.send_message("discord", chatId, resultMsg)

@app.task(bind=True, name='tasks.logoutTask', queue='high_priority')
def logoutTask(self, chatId):
    sendWorkerCheckIn(self, chatId)
    db.deleteUser(chatId)
    redisManager.deleteSession(chatId, 'portal')
    redisManager.deleteSession(chatId, 'course')
    
    notifier.send_message("discord", chatId, "**Đăng xuất thành công!**\nToàn bộ dữ liệu tài khoản và lịch sử của bạn đã được xóa khỏi hệ thống hoàn toàn.")

@app.task(bind=True, name='tasks.customDeadlineTask', queue='high_priority')
def customDeadlineTask(self, chatId, startDateStr, numDays):
    sendWorkerCheckIn(self, chatId)
    startDate = datetime.strptime(startDateStr, "%d/%m/%Y")
    courseService.scanAllDeadlines(chatId, isManual=True, startDate=startDate, numDays=numDays)

@app.task(bind=True, name="tasks.portalWeekTask", queue='high_priority')
def portalWeekTask(self, chatId, startDateStr):
    sendWorkerCheckIn(self, chatId)
    try:
        msg = portalService.format_week_calendar_message(chatId, startDateStr)
        
        notifier.send_message("discord", chatId, msg)
        
    except Exception as e:
        utils.log("ERROR", f"Lỗi trong portalWeekTask: {e}")

# ==========================================
# 2. TASK ƯU TIÊN THẤP (Dành cho Quét định kỳ)
# ==========================================

@app.task(
    bind=True,
    name='tasks.periodicCourseTask', 
    queue='low_priority', 
    rate_limit='1/s',
    autoretry_for=(Exception,), 
    retry_kwargs={'max_retries': 3, 'countdown': 60}
)
def periodicCourseTask(self, chatId):
    log("WORKER", f"Đang quét deadline cho user: {chatId}")
    courseService.scanAllDeadlines(chatId, isManual=False)

@app.task(
    bind=True,
    name='tasks.periodicTodayDeadlineTask', 
    queue='low_priority', 
    rate_limit='1/s',
    autoretry_for=(Exception,), 
    retry_kwargs={'max_retries': 3, 'countdown': 60}
)
def periodicTodayDeadlineTask(self, chatId):
    log("WORKER", f"Đang quét deadline HÔM NAY cho user: {chatId}")
    courseService.scanAllDeadlines(chatId, isManual=False, onlyToday=True)


@app.task(
    bind=True,
    name='tasks.periodicPortalTask', 
    queue='low_priority', 
    rate_limit='1/s'
)
def periodicPortalTask(self, chatId, dateStr, isTomorrow=False):
    log("WORKER", f"Đang quét lịch cho user: {chatId}")
    msg = portalService.formatCalendarMessage(chatId, dateStr, isAuto=True, isTomorrow=isTomorrow)
    if msg:
        notifier.send_message("discord", chatId, msg)

@app.task(
    bind=True,
    name='tasks.scheduleClassRemindersTask',
    queue='low_priority'
)
def scheduleClassRemindersTask(self, chatId, dateStr):
    from datetime import timedelta
    log("WORKER", f"Đang lên lịch báo trước 1 tiếng cho user: {chatId}")
    u = db.getUserCredentials(chatId)
    if not u: return
    
    rawUser = utils.decryptData(u['uth_user'])
    rawPass = utils.decryptData(u['uth_pass'])

    classes, error = portalService.getClassesByDate(chatId, rawUser, rawPass, dateStr)
    if not classes: return
    
    for c in classes:
        tuGioStr = c.get('tuGio')
        if not tuGioStr: continue
        
        try:
            from zoneinfo import ZoneInfo
            tz = ZoneInfo("Asia/Ho_Chi_Minh")
            dtStr = f"{dateStr} {tuGioStr}"
            classTime = datetime.strptime(dtStr, "%d/%m/%Y %H:%M").replace(tzinfo=tz)
            notifyTime = classTime - timedelta(hours=1)
            
            if notifyTime > datetime.now(tz):
                notifySingleClassTask.apply_async(args=[chatId, c, dateStr], eta=notifyTime)
        except Exception as e:
            log("ERROR", f"Lỗi parse time lên lịch 1 tiếng: {e}")

@app.task(
    bind=True,
    name='tasks.notifySingleClassTask',
    queue='high_priority'
)
def notifySingleClassTask(self, chatId, classData, dateStr):
    msg = portalService.formatSingleClassMessage(classData, dateStr)
    notifier.send_message("discord", chatId, msg)

@app.task(
    name='tasks.updateWeatherTask',
    queue='low_priority'
)
def updateWeatherTask():
    if not WEATHER_API_KEY:
        log("WARN", "Bỏ qua chu kỳ cập nhật thời tiết do thiếu cấu hình WEATHER_API_KEY.")
        return

    campuses = {
        "CS1": "10.8023,106.7147",
        "CS2": "10.7934,106.7320",
        "CS3": "10.8524,106.6361"
    }

    for code, coords in campuses.items():
        try:
            url = f"https://api.weatherapi.com/v1/forecast.json?key={WEATHER_API_KEY}&q={coords}&days=2&lang=vi"
            response = utils.safeRequest("GET", url, use_proxy=False)
            
            if response and response.status_code == 200:
                data = response.json() 
                
                forecast_data = []
                for day in data['forecast']['forecastday']:
                    forecast_data.extend(day['hour'])

                redisManager.redisClient.set(f"forecast:{code}", json.dumps(forecast_data), ex=7200)
                log("SUCCESS", f"Đã lưu dự báo 48h cho {code}")
            else:
                log("ERROR", f"Không thể lấy weather cho {code}, Code: {response.status_code if response else 'None'}")
                
        except Exception as e:
            log("ERROR", f"Lỗi fetch forecast {code}: {e}")

# ==========================================
# 3. CRON JOB TASK WRAPPERS (Celery Beat)
# ==========================================
import cronService

@app.task(name='tasks.cron_notifyTomorrowClasses', queue='low_priority')
def cron_notifyTomorrowClasses():
    cronService.notifyTomorrowClasses()

@app.task(name='tasks.cron_scheduleTodayClasses', queue='low_priority')
def cron_scheduleTodayClasses():
    cronService.scheduleTodayClasses()

@app.task(name='tasks.cron_autoScanAllUsers', queue='low_priority')
def cron_autoScanAllUsers():
    cronService.autoScanAllUsers()

@app.task(name='tasks.cron_scanTodayDeadlines', queue='low_priority')
def cron_scanTodayDeadlines():
    cronService.scanTodayDeadlines()