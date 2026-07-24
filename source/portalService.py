# Copyright (c) 2026 vanphat111 <phathovan14122006@email.com> | All rights reserved
# portalService.py

# from curl_cffi import requests
from datetime import datetime, timedelta
import database as db
import utils
import redisManager

# session = requests.Session(impersonate="chrome110")

def forceLoginPortal(user, password):
    try:
        fakeCaptcha = utils.generateFakeCaptcha()
        url = f"https://portal.ut.edu.vn/api/v1/user/login?g-recaptcha-response={fakeCaptcha}"
        r = utils.safeRequest("POST", url, json={"username": user, "password": password})
        
        try:
            data = r.json()
        except Exception:
            utils.log("ERROR", f"Server không trả về JSON. Mã lỗi HTTP: {r.status_code}. Nội dung: {r.text[:500]}")
            return None, "Lỗi phản hồi từ server trường"
            
        token = data.get("token")
        if r.status_code == 200 and token:
            return token, "Thành công"
        return None, data.get("message", "Sai tài khoản hoặc mật khẩu")
    except Exception as e:
        utils.log("ERROR", f"Lỗi login portal: {e}")
        return None, "Lỗi kết nối server trường"

def verifyUthCredentials(user, password):
    token, msg = forceLoginPortal(user, password)
    if token:
        return True, msg
    return False, msg

def get_classes_by_week(chat_id, user, password, targetDate):
    try:
        date_obj = datetime.strptime(targetDate, "%d/%m/%Y")
        iso_date = date_obj.strftime("%Y-%m-%d")

        tk = getValidPortalToken(chat_id, user, password)
        if not tk: 
            return False, "Không thể lấy Token. Vui lòng kiểm tra lại tài khoản/mật khẩu."

        headers = {
            "Authorization": f"Bearer {tk}",
            "Referer": "https://portal.ut.edu.vn/calendar",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
            "accept": "application/json, text/plain, */*"
        }

        url = f"https://portal.ut.edu.vn/api/v1/lichhoc/lichTuan?date={iso_date}"
        res = utils.safeRequest("GET", url, headers=headers)

        if res is None:
            return False, "Trang web trường đang quá tải hoặc không phản hồi (Timeout)."

        if res.status_code == 401:
            utils.log("WARN", f"Token của {chat_id} bị Invalid khi lấy lịch tuần. Đang login lại...")
            tk = getValidPortalToken(chat_id, user, password, force=True)
            if not tk: 
                return False, "Phiên đăng nhập hết hạn và không thể gia hạn. Hãy đăng ký lại."
            
            headers["Authorization"] = f"Bearer {tk}"
            res = utils.safeRequest("GET", url, headers=headers)

        if res.status_code == 200:
            data = res.json().get("body", [])
            return data, None

        return False, f"Lỗi không xác định từ server trường (Mã: {res.status_code})"

    except Exception as e:
        utils.log("ERROR", f"Lỗi get_classes_by_week: {e}")
        return False, "Lỗi hệ thống không xác định khi lấy lịch tuần."

def getClassesByDate(chatId, user, password, targetDate):
    try:
        week_data, error = get_classes_by_week(chatId, user, password, targetDate)

        if week_data is False:
            return False, error

        classes = [c for c in week_data if c.get("ngayBatDauHoc") == targetDate]

        return classes, None

    except Exception as e:
        utils.log("ERROR", f"Lỗi getClassesByDate: {e}")
        return False, "Lỗi hệ thống không xác định. Vui lòng thử lại sau ít phút."

def verifyAndSaveUser(chatId, mssv, password):
    isValid, reason = verifyUthCredentials(mssv, password)
    if isValid:
        conn = db.getDbConn(); cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (chat_id, uth_user, uth_pass) VALUES (?, ?, ?) ON CONFLICT (chat_id) DO UPDATE SET uth_user = excluded.uth_user, uth_pass = excluded.uth_pass",
            (str(chatId), utils.encryptData(mssv), utils.encryptData(password))
        )
        conn.commit(); cur.close(); conn.close()
        utils.log("SUCCESS", f"User {chatId} đã đăng ký thành công")
        return True, "**Đăng ký thành công!** Mình sẽ tự động nhắc lịch cho bạn."
    
    utils.log("ERROR", f"User {chatId} đăng ký thất bại: {reason}")
    return False, f"**Thất bại:** {reason}"

def getValidPortalToken(chatId, rawUser, rawPass, force=False):
    if not force:
        cachedToken = redisManager.getSession(chatId, 'portal')
        if cachedToken: return cachedToken

    token, _ = forceLoginPortal(rawUser, rawPass)
    if token:
        redisManager.saveSession(chatId, 'portal', token, expire=7200)
        return token
    return None

def formatCalendarMessage(chatId, dateStr, isAuto=False, isTomorrow=False):
    u = db.getUserCredentials(chatId)
    if not u:
        if isAuto:
            return None
        return "Bạn chưa đăng ký tài khoản!"
    
    rawUser = utils.decryptData(u['uth_user'])
    rawPass = utils.decryptData(u['uth_pass'])

    classes, error = getClassesByDate(chatId, rawUser, rawPass, dateStr)
    if classes is False:
        if isAuto:
            return None
        return f"**Lỗi:** {error}"
    
    if classes:
        if isTomorrow:
            header = f"**NHẮC LỊCH HỌC NGÀY MAI ({dateStr})**\n"
        elif isAuto:
            header = f"**NHẮC LỊCH TỰ ĐỘNG ({dateStr})**\n"
        else:
            header = f"**LỊCH HỌC {dateStr}**\n"
            
        msg = header + "━━━━━━━━━━━━━━━━━━\n"
        for c in classes:
            courseLink = c.get('link', 'https://courses.ut.edu.vn/')
            statusLabel = "Tạm ngưng" if c.get("isTamNgung") else "Bình thường"

            weatherLabel = ""
            target_cs = None
            ten_phong = c.get('tenPhong', '')
            co_so_display = c.get('coSoToDisplay', '')
            
            if "CS1" in ten_phong or "Cơ sở 1" in co_so_display: target_cs = "CS1"
            elif "CS3" in ten_phong or "Cơ sở 3" in co_so_display: target_cs = "CS3"
            elif "CS2" in ten_phong or "Cơ sở 2" in co_so_display: target_cs = "CS2"
            
            if target_cs:
                weatherData = utils.getWeatherByHour(target_cs, c['tuGio'], dateStr)
                if weatherData:
                    weatherLabel = (
                        f"\nThời tiết {target_cs} (`{c['tuGio']}`): "
                        f"{weatherData['temp']}°C, {weatherData['desc']}"
                    )

            msg += f"\n[{c['tenMonHoc']}]({courseLink})"
            msg += f"\nThời gian: {c['tuGio']} - {c['denGio']}"
            msg += f"\nPhòng: {c['tenPhong']}"
            msg += weatherLabel
            msg += f"\nTrạng thái: {statusLabel}\n"
        msg += "\n[Portal UTH](https://portal.ut.edu.vn/)"
        return msg
    else:
        if isAuto:
            return None
        return f"**Thông báo**\nNgày {dateStr} bạn không có lịch học."

def formatSingleClassMessage(c, dateStr):
    header = "**NHẮC NHỞ: CÒN 1 TIẾNG NỮA VÀO HỌC!**\n"
    msg = header + "━━━━━━━━━━━━━━━━━━\n"
    courseLink = c.get('link', 'https://courses.ut.edu.vn/')
    statusLabel = "Tạm ngưng" if c.get("isTamNgung") else "Bình thường"

    weatherLabel = ""
    target_cs = None
    ten_phong = c.get('tenPhong', '')
    co_so_display = c.get('coSoToDisplay', '')
    
    if "CS1" in ten_phong or "Cơ sở 1" in co_so_display: target_cs = "CS1"
    elif "CS3" in ten_phong or "Cơ sở 3" in co_so_display: target_cs = "CS3"
    elif "CS2" in ten_phong or "Cơ sở 2" in co_so_display: target_cs = "CS2"
    
    if target_cs:
        weatherData = utils.getWeatherByHour(target_cs, c['tuGio'], dateStr)
        if weatherData:
            weatherLabel = (
                f"\nThời tiết: "
                f"{weatherData['temp']}°C, {weatherData['desc']}"
            )

    msg += f"[{c['tenMonHoc']}]({courseLink})"
    msg += f"\nThời gian: {c['tuGio']} - {c['denGio']}"
    msg += f"\nPhòng: {c['tenPhong']}"
    msg += weatherLabel
    msg += f"\nTrạng thái: {statusLabel}\n"
    return msg
    
def format_week_calendar_message(chat_id, startDateStr):
    u = db.getUserCredentials(chat_id)
    if not u: return "**Lỗi**\nBạn chưa đăng ký tài khoản!"

    raw_user = utils.decryptData(u['uth_user'])
    raw_pass = utils.decryptData(u['uth_pass'])
    
    now = datetime.strptime(startDateStr, "%d/%m/%Y")
    monday = now - timedelta(days=now.weekday())

    data, error = get_classes_by_week(chat_id, raw_user, raw_pass, startDateStr)
    
    if data is False:
        return f"**Có lỗi xảy ra:**\n{error}"
    
    if not data:
        return f"**Thông báo**\nTuần từ {monday.strftime('%d/%m')} bạn không có lịch học."

    week_data = { (monday + timedelta(days=i)).strftime("%d/%m/%Y"): [] for i in range(7) }
    
    for item in data:
        date_key = item.get("ngayBatDauHoc")
        if date_key in week_data:
            week_data[date_key].append(item)

    msg = "**LỊCH HỌC CẢ TUẦN**\n"
    msg += f"Từ {monday.strftime('%d/%m')} đến {(monday + timedelta(days=6)).strftime('%d/%m')}\n"
    msg += "━━━━━━━━━━━━━━━━━━\n"

    day_names = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"]
    
    for i, (date_str, classes) in enumerate(week_data.items()):
        msg += f"\n**{day_names[i]} ({date_str}):**\n"
        
        if not classes:
            msg += "   ╰ Bạn được nghỉ\n"
        else:
            for c in classes:
                status = " (**Tạm ngưng**)" if c.get("isTamNgung") else ""
                courseLink = c.get('link') or 'https://courses.ut.edu.vn/'
                
                # --- Logic xác định cơ sở dựa trên code cũ của mày ---
                target_cs = "N/A"
                ten_phong = c.get('tenPhong', '')
                co_so_display = c.get('coSoToDisplay', '')
                
                if "CS1" in ten_phong or "Cơ sở 1" in co_so_display: target_cs = "CS1"
                elif "CS3" in ten_phong or "Cơ sở 3" in co_so_display: target_cs = "CS3"
                elif "CS2" in ten_phong or "Cơ sở 2" in co_so_display: target_cs = "CS2"
                
                # Nhúng link vào tên môn và thêm cơ sở ở sau
                msg += f"   ╰ `{c['tuGio']}`: [{c['tenMonHoc']}]({courseLink}) ({target_cs}){status}\n"

    msg += "\n━━━━━━━━━━━━━━━━━━\n"
    msg += "Dùng lệnh `/lichhoc` để xem chi tiết phòng học và thời tiết."
    
    return msg