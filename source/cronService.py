# Copyright (c) 2026 vanphat111 <phathovan14122006@email.com> | All rights reserved
# cronService.py

import time
import traceback
import database as db
from utils import log
import task

import datetime

def notifyTomorrowClasses():
    log("CRON", "Bắt đầu chu kỳ báo lịch ngày mai")
    try:
        users = db.getUsersForPortalNotify()
        if not users:
            return

        tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%d/%m/%Y")
        for chat_id in users:
            try:
                task.periodicPortalTask.delay(chat_id, tomorrow, isTomorrow=True)
            except Exception:
                log("ERROR", f"Lỗi đẩy task cho {chat_id}: {traceback.format_exc()}")
    except Exception:
        log("CRITICAL", f"Crash tại notifyTomorrowClasses: {traceback.format_exc()}")

def scheduleTodayClasses():
    log("CRON", "Bắt đầu lên lịch báo trước 1 tiếng cho hôm nay")
    try:
        users = db.getUsersForPortalNotify()
        if not users:
            return

        today = time.strftime("%d/%m/%Y")
        for chat_id in users:
            try:
                task.scheduleClassRemindersTask.delay(chat_id, today)
            except Exception:
                log("ERROR", f"Lỗi đẩy task cho {chat_id}: {traceback.format_exc()}")
    except Exception:
        log("CRITICAL", f"Crash tại scheduleTodayClasses: {traceback.format_exc()}")

def autoScanAllUsers():
    log("CRON", "Bắt đầu chu kỳ quét Course Deadline")
    try:
        users = db.getUsersForDeadlineNotify()
        if not users:
            log("CRON", "Không có user nào cần quét Deadline")
            return

        for chat_id in users:
            try:
                task.periodicCourseTask.delay(chat_id)
                log("CRON", f"Đã đẩy task Course cho user: {chat_id}")
            except Exception:
                log("ERROR", f"Lỗi đẩy task cho {chat_id}: {traceback.format_exc()}")

    except Exception:
        log("CRITICAL", f"Crash tại autoScanAllUsers: {traceback.format_exc()}")

def scanTodayDeadlines():
    log("CRON", "Bắt đầu chu kỳ quét nhắc nhở deadline trong ngày")
    try:
        users = db.getUsersForDeadlineNotify()
        if not users:
            log("CRON", "Không có user nào cần quét Deadline")
            return

        for chat_id in users:
            try:
                task.periodicTodayDeadlineTask.delay(chat_id)
            except Exception:
                log("ERROR", f"Lỗi đẩy task cho {chat_id}: {traceback.format_exc()}")
    except Exception:
        log("CRITICAL", f"Crash tại scanTodayDeadlines: {traceback.format_exc()}")