# Copyright (c) 2026 vanphat111 <phathovan14122006@email.com> | All rights reserved
# database.py

import sqlite3
import os
import time
from utils import log

# SQLite DB Path (mặc định lưu tại thư mục hiện tại)
db_path = os.getenv("DB_PATH", "database.sqlite3")

def getDbConn(): 
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def initDb():
    log("SYSTEM", "Bắt đầu kiểm tra và khởi tạo Database (SQLite)...")
    try:
        conn = getDbConn(); cur = conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL;")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                chat_id TEXT PRIMARY KEY, 
                uth_user TEXT NOT NULL, 
                uth_pass TEXT NOT NULL, 
                notify_enabled INTEGER DEFAULT 1, 
                notify_deadline INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        conn.commit(); cur.close(); conn.close()
        log("INFO", "Hệ thống Database (SQLite) đã sẵn sàng.")
        return
    except Exception as e:
        log("ERROR", f"Lỗi khởi tạo DB: {e}")


def getUserCredentials(chatId):
    try:
        conn = getDbConn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE chat_id = ?", (str(chatId),))
        res = cur.fetchone()
        cur.close(); conn.close()
        return dict(res) if res else None
    except Exception as e:
        log("ERROR", f"Lỗi lấy user {chatId}: {e}")
        return None

def updateDeadlineStatus(chatId, status):
    status_int = 1 if status else 0
    try:
        conn = getDbConn(); cur = conn.cursor()
        cur.execute("UPDATE users SET notify_deadline = ? WHERE chat_id = ?", (status_int, str(chatId)))
        conn.commit(); cur.close(); conn.close()
        return True
    except Exception as e:
        log("ERROR", f"Lỗi DB updateDeadlineStatus: {e}")
        return False

def updateNotifyStatus(chatId, newStatus):
    status_int = 1 if newStatus else 0
    try:
        conn = getDbConn(); cur = conn.cursor()
        cur.execute("UPDATE users SET notify_enabled = ? WHERE chat_id = ?", (status_int, str(chatId)))
        conn.commit(); cur.close(); conn.close()
        return True
    except Exception as e:
        log("ERROR", f"Lỗi DB updateNotifyStatus: {e}")
        return False        

def getDeadlineStatus(chatId):
    try:
        conn = getDbConn(); cur = conn.cursor()
        cur.execute("SELECT notify_deadline FROM users WHERE chat_id = ?", (str(chatId),))
        res = cur.fetchone(); cur.close(); conn.close()
        return bool(res[0]) if res else True
    except Exception as e:
        log("ERROR", f"Lỗi DB getDeadlineStatus: {e}")
        return True

def getUsersForPortalNotify():
    try:
        conn = getDbConn()
        cur = conn.cursor()
        cur.execute("SELECT chat_id FROM users WHERE notify_enabled = 1")
        res = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
        return res
    except Exception as e:
        log("ERROR", f"Lỗi lấy list Portal Notify: {e}")
        return []

def getUsersForDeadlineNotify():
    try:
        conn = getDbConn()
        cur = conn.cursor()
        cur.execute("SELECT chat_id FROM users WHERE notify_deadline = 1")
        res = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
        return res
    except Exception as e:
        log("ERROR", f"Lỗi lấy list Deadline Notify: {e}")
        return []

def deleteUser(chatId):
    try:
        conn = getDbConn(); cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE chat_id = ?", (str(chatId),))
        conn.commit(); cur.close(); conn.close()
        log("INFO", f"Đã xóa tài khoản user {chatId}")
        return True
    except Exception as e:
        log("ERROR", f"Lỗi DB deleteUser: {e}")
        return False
