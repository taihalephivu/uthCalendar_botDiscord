# 🎓 UTH Calendar Bot (Discord)

Bot Discord đa nhiệm dành cho sinh viên Trường Đại học Giao thông Vận tải TP.HCM (UTH).
Hệ thống tự động tra cứu lịch học, nhắc nhở deadline bài tập, và cung cấp thông tin thời tiết dựa trên nền tảng Discord với kiến trúc phân tán mạnh mẽ.

---

## 🚀 Tính Năng Chính

- **Slash Commands**: Giao diện lệnh `/` hiện đại, tự động gợi ý tham số và giữ bảo mật thông tin (chế độ phản hồi ẩn danh - ephemeral).
- **Lịch Học Nhanh Chóng**: Xem lịch học hôm nay, lịch cả tuần chi tiết đến từng phòng học và cơ sở.
- **Nhắc Lịch Tự Động**: Tự động gửi thông báo lịch học vào các khung giờ 05:00, 12:00, và 17:00 hằng ngày.
- **Quét Deadline (Moodle)**: Tự động tổng hợp và nhắc nhở bài tập chưa hoàn thành trên hệ thống Courses, tự động quét định kỳ vào thứ Hai.
- **Thời Tiết Tích Hợp**: Tự động nhận diện cơ sở học và hiển thị thời tiết tương ứng cho từng ca học.
- **Kiến Trúc Phân Tán (Microservices)**:
  - `Discord Bot`: Đóng vai trò là Gateway giao tiếp chính với người dùng.
  - `Celery & Redis`: Hệ thống Hàng đợi (Queue) xử lý các tác vụ nền tốn thời gian (cào dữ liệu) để không làm treo bot.
  - `Cloudflare WARP`: Proxy vượt rào để tránh việc bị hệ thống trường chặn IP khi có quá nhiều truy vấn.
  - `SQLite`: Cơ sở dữ liệu gọn nhẹ, lưu trữ cấu hình người dùng và phiên bản mã hóa bảo mật.

## 🛠️ Công Nghệ Sử Dụng

- **Ngôn ngữ**: Python 3.10+
- **Thư viện chính**: `discord.py` (Bot framework), `Celery` (Task Queue), `curl_cffi` (Requests), `cryptography`.
- **Cơ sở dữ liệu & Caching**: `SQLite`, `Redis`.
- **Môi trường triển khai**: `Docker`, `Docker Compose`.

## ⚙️ Hướng Dẫn Cài Đặt & Chạy Hệ Thống

### 1. Yêu cầu hệ thống
- Máy tính hoặc Server có sẵn **Docker** và **Docker Compose**.
- Một tài khoản Discord Developer để lấy Bot Token.

### 2. Cấu hình biến môi trường
Tạo file `.env` ở thư mục gốc của dự án và điền các thông tin sau:
```env
# Cấu hình Discord
DISCORD_TOKEN=your_discord_bot_token_here
ADMIN_ID=your_discord_user_id_here

# Bảo mật (Tạo mã khóa ngẫu nhiên bằng Python Fernet)
ENCRYPTION_KEY=your_fernet_encryption_key_here

# Tùy chọn: API Thời Tiết (Lấy từ weatherapi.com)
WEATHER_API_KEY=your_weather_api_key_here
```

### 3. Khởi động hệ thống
Toàn bộ hệ thống được đóng gói sẵn. Chỉ cần một dòng lệnh duy nhất để khởi chạy:

```bash
docker compose up -d --build
```

Docker sẽ tự động kích hoạt và kết nối:
- Container `uth_bot` (Bot Discord)
- Container `worker_vip` & `worker_low` (Celery Workers)
- Container `celery_beat` (Bộ hẹn giờ Cron)
- Container `uth_redis` (Bộ nhớ Cache & Message Broker)
- Container `uth_warp` (Proxy mạng bảo mật)

### 4. Dữ liệu lưu trữ
Mọi dữ liệu sinh ra (file CSDL `database.sqlite3`) sẽ được lưu an toàn tại thư mục `./data/` trên máy tính/server của bạn thông qua Docker Volumes, giúp dữ liệu không bị mất khi khởi động lại bot.

## 💻 Danh Sách Lệnh (Slash Commands)

Gõ phím `/` trong server hoặc tin nhắn riêng với bot trên Discord:
- `/login <mssv> <password>`: Cung cấp thông tin đăng nhập portal để bot có thể tự động tra cứu.
- `/lichhoc [ngày]`: Xem lịch học theo ngày cụ thể (Nếu để trống mặc định là hôm nay).
- `/lichtuan [ngày]`: Xem tổng quan lịch học nguyên tuần.
- `/deadline`: Quét và liệt kê các bài tập chưa làm trên khóa học.
- `/done <id>`: Đánh dấu hoàn thành một bài tập.
- `/undone <id>`: Bỏ đánh dấu hoàn thành bài tập (nếu lỡ bấm nhầm).

## 🛡️ Bảo Mật
- **Mã hóa Dữ liệu**: Mật khẩu portal của sinh viên được mã hóa 2 chiều siêu bảo mật (chuẩn Fernet/AES) trước khi lưu vào SQLite. Kể cả người nắm giữ file CSDL cũng không thể đọc được mật khẩu nếu không có `ENCRYPTION_KEY`.
- **Riêng tư Người Dùng**: Quá trình đăng nhập và trả kết quả qua lệnh Slash luôn được cài đặt ẩn (`ephemeral`), người xung quanh trong Server Discord không thể xem được tin nhắn của bạn với Bot.

## 🤝 Bản Quyền
Dự án được bảo vệ bản quyền. Vui lòng tôn trọng quyền tác giả và không sử dụng cho mục đích thương mại mà không có sự cho phép.