import notifier
from curl_cffi import requests
import time
from datetime import datetime, timedelta
import database as db
import utils
import re
import redisManager

# courseSession = requests.Session(impersonate="chrome110")

def rebuildSession(cookieDict):
    session = requests.Session(impersonate="chrome")
    session.cookies.update(cookieDict)
    return session

def getValidCourseSession(chatId, rawUser, rawPass):
    cached = redisManager.getSession(chatId, 'course')
    if cached:
        return cached['cookies'], cached['sesskey']

    session, sesskey = fetchMoodleSession(rawUser, rawPass) 
    
    if session and sesskey:
        data = {
            "sesskey": sesskey,
            "cookies": session
        }
        redisManager.saveSession(chatId, 'course', data)
        
    return session, sesskey

def fetchMoodleSession(username, password):
    with requests.Session(impersonate="chrome") as s:
        try:
            loginUrl = f"https://courses.ut.edu.vn/login/index.php"

            loginPage = s.get(
                loginUrl,
                headers={
                    "Accept": (
                        "text/html,application/xhtml+xml,"
                        "application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
                    )
                },
                timeout=20,
            )
            loginPage.raise_for_status()

            tokenMatch = re.search(
                r'name=["\']logintoken["\'][^>]*value=["\']([^"\']+)["\']',
                loginPage.text,
                re.IGNORECASE,
            )

            if not tokenMatch:
                utils.log("ERROR", "Không tìm thấy Moodle logintoken")
                return None, None

            loginToken = tokenMatch.group(1)

            loginResponse = s.post(
                loginUrl,
                data={
                    "anchor": "",
                    "logintoken": loginToken,
                    "username": username,
                    "password": password,
                },
                headers={
                    "Origin": "https://courses.ut.edu.vn",
                    "Referer": loginUrl,
                    "Accept": (
                        "text/html,application/xhtml+xml,"
                        "application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
                    ),
                },
                allow_redirects=True,
                timeout=25,
            )
            loginResponse.raise_for_status()

            if (
                "/login/index.php" in str(loginResponse.url)
                or 'name="logintoken"' in loginResponse.text
            ):
                utils.log("WARN", "Đăng nhập Moodle thất bại")
                return None, None

            coursePage = s.get(
                "https://courses.ut.edu.vn/my/courses.php",
                headers={
                    "Referer": "https://courses.ut.edu.vn/my/",
                    "Accept": (
                        "text/html,application/xhtml+xml,"
                        "application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
                    ),
                },
                timeout=20,
            )
            coursePage.raise_for_status()

            sesskeyMatch = re.search(
                r'"sesskey"\s*:\s*"([^"]+)"',
                coursePage.text,
            )

            if not sesskeyMatch:
                utils.log("ERROR", "Login được nhưng không thấy sesskey")
                return None, None

            cookies = s.cookies.get_dict()
            sesskey = sesskeyMatch.group(1)

            return cookies, sesskey

        except Exception as e:
            utils.log("ERROR", f"Lỗi login Moodle: {e}")
            return None, None

def prepareActionEventsPayload(startDate, numDays):
    now_ts = int(startDate.timestamp())
    end_ts = now_ts + (numDays * 24 * 60 * 60)
    
    payload = [{
        "index": 0,
        "methodname": "core_calendar_get_action_events_by_timesort",
        "args": {
            "timesortfrom": now_ts,
            "timesortto": end_ts,
            "limitnum": 50
        }
    }]

    return payload, now_ts, end_ts

def getDeadlineMessages(chatId, cookieDict, sesskey, startDate=None, numDays=7):
    if startDate is None:
        startDate = datetime.now()
        
    payload, startTs, endTs = prepareActionEventsPayload(startDate, numDays)
    url = f"https://courses.ut.edu.vn/lib/ajax/service.php?sesskey={sesskey}"
    
    with requests.Session(impersonate="chrome") as s:
        s.cookies.update(cookieDict)
        # Thêm headers mặc định cho Moodle Session
        s.headers.update({
            "Connection": "close",
            "Accept": "application/json, text/plain, */*",
        })
        
        try:
            r = s.post(url, json=payload, timeout=15)
            
            try:
                responses = r.json()
            except Exception:
                utils.log("ERROR", f"Moodle Deadline: Server không trả về JSON. Mã HTTP: {r.status_code}. Nội dung: {r.text[:500]}")
                return None

            if responses and isinstance(responses, list) and responses[0].get('error'):
                utils.log("WARN", f"Session Moodle của {chatId} đã hết hạn")
                return None
            
            allEvents = []

            for res in responses:
                if res.get('error'): continue
                if 'data' in res and 'events' in res['data']:
                    for event in res['data']['events']:
                        if not any(e['id'] == event['id'] for e in allEvents):
                            allEvents.append(event)
            
            allEvents.sort(key=lambda x: x['timesort'])
            
            msgList = []
            for e in allEvents:
                dueDt = datetime.fromtimestamp(e['timesort'])
                dueStr = dueDt.strftime('%d/%m/%Y %H:%M')
                
                text = (
                    f"**[{e['name']}]({e.get('url')})**\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"Trạng thái: Chưa hoàn thành\n"
                    f"Môn học: {e['course']['fullname']}\n"
                    f"Hạn nộp: `{dueStr}`"
                )

                msgList.append({
                    "text": text
                })
            return msgList

        except Exception as e:
            utils.log("ERROR", f"Lỗi lấy message deadline: {e}")
        return None

def scanAllDeadlines(chatId, isManual=False, startDate=None, numDays=7):
    u = db.getUserCredentials(chatId)
    if not u: return False

    rawUser = utils.decryptData(u['uth_user'])
    rawPass = utils.decryptData(u['uth_pass'])
    
    session, sesskey = getValidCourseSession(chatId, rawUser, rawPass)
    
    if not session or not sesskey:
        if isManual: notifier.send_message("discord", chatId, "**Lỗi**\nKhông thể kết nối hệ thống Courses.")
        return False

    messages = getDeadlineMessages(chatId, session, sesskey, startDate=startDate, numDays=numDays)

    if messages is None:
        utils.log("INFO", f"Đang làm mới sesskey cho {chatId}")
        redisManager.deleteSession(chatId, 'course')
        session, sesskey = fetchMoodleSession(rawUser, rawPass)
        if session and sesskey:
            data = {
                "sesskey": sesskey,
                "cookies": session
                }
            redisManager.saveSession(chatId, 'course', data)
            messages = getDeadlineMessages(chatId, session, sesskey, startDate=startDate, numDays=numDays)

    if messages is None:
        notifier.send_message("discord", chatId, "**Lỗi**\nKhông thể lấy danh sách deadline.")
        return False

            
    if len(messages) == 0:
        if isManual:
            notifier.send_message("discord", chatId, "**Hoàn tất**\nBạn không có deadline nào trong khoảng thời gian này. Nghỉ ngơi thôi!")
        return True

    rangeStart = startDate if startDate else datetime.now()
    rangeEnd = rangeStart + timedelta(days=numDays)

    startStr = rangeStart.strftime('%d/%m/%Y')
    endStr = rangeEnd.strftime('%d/%m/%Y')

    if isManual:
        header = "**DANH SÁCH DEADLINE**\n"
    else:
        header = "**THÔNG BÁO DEADLINE TỰ ĐỘNG**\n"

    header += f"Thời gian: từ {startStr} đến {endStr}\n"
    header += f"Tìm thấy **{len(messages)}** sự kiện trong khoảng thời gian này.\n"
    header += "━━━━━━━━━━━━━━━━━━"
    
    notifier.send_message("discord", chatId, header)

    for m in messages:
        notifier.send_message("discord", chatId, m['text'])
        time.sleep(0.3)
    return True

def getEventIcon(eventType):
    icons = {'assign': '📝', 'quiz': '✍️', 'course': '📚', 'site': '🌐'}
    return icons.get(eventType, '🔔')