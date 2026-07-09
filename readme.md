# 📅 UTH Calendar Bot

[![Docker Image](https://img.shields.io/badge/Docker-Enabled-blue?logo=docker)](https://hub.docker.com/r/vanphat111/uth-calendar)
[![Python Version](https://img.shields.io/badge/Python-3.11+-yellow?logo=python)](https://www.python.org/)
[![Celery](https://img.shields.io/badge/Worker-Celery-green?logo=celery)](https://docs.celeryq.dev/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0.html)

Một trợ lý Telegram thông minh, hiệu năng cao giúp sinh viên **Đại học Giao thông Vận tải TP.HCM (UTH)** quản lý lịch học và deadline tự động. Hệ thống được thiết kế theo kiến trúc microservices và vận hành ổn định trên các server cá nhân thông qua Docker.

## 🚀 Tính năng nổi bật

* 🔔 **Nhắc lịch Portal:** Tự động gửi lịch học vào các khung giờ 05:00, 12:00 và 17:00 hàng ngày.
* 📑 **Quét Deadline định kỳ:** Tự động thông báo bài tập mới vào 19:00 thứ Hai hàng tuần.
* 🔍 **Quét Deadline tùy chỉnh:** Chủ động chọn ngày bắt đầu và số ngày muốn quét thông qua giao diện nút bấm.
* 💰 **Ủng hộ (Donate) tự động:** Hỗ trợ tạo mã VietQR động theo định mức hoặc số tiền tùy chọn qua cổng PayOS.
* 🛡️ **Khởi động an toàn (Fail-safe):** Tự động kiểm tra nghiêm ngặt các biến môi trường cốt lõi khi khởi động.
* 🛑 **Cảnh báo Tạm ngưng:** Tự động nhận diện và hiển thị trạng thái môn học bị tạm nghỉ từ hệ thống Portal.
* 🔐 **Cơ chế Auto-Relogin:** Tự động gia hạn Session và làm mới Sesskey khi hết hạn để đảm bảo dữ liệu luôn cập nhật.
* 🔒 **Bảo mật dữ liệu:** Mã hóa thông tin tài khoản sinh viên bằng chuẩn **AES-256** trước khi lưu trữ vào Database.
* ⚡ **Xử lý bất đồng bộ:** Sử dụng Celery và Redis để phân tách các tác vụ quét dữ liệu nặng, giúp Bot phản hồi nhanh.

## 🛠 Tech Stack

* **Language:** Python 3.11+
* **Library:** `pyTelegramBotAPI` (Telebot), `payos`
* **Task Queue:** Celery (Distributed Task Queue)
* **Broker & Cache:** Redis
* **Database:** PostgreSQL
* **Security:** `cryptography` (Fernet AES-256)
* **Deployment:** Docker & Docker Compose

---

## ⚙️ Cấu hình hệ thống

Chuẩn bị file `.env` với các tham số cấu hình dưới đây để vận hành hệ thống:

### 1. Cấu hình cốt lõi (Bắt buộc)
| Biến | Mô tả |
| :--- | :--- |
| `TELE_TOKEN` | API Token của Bot lấy từ @BotFather |
| `ADMIN_ID` | ID Telegram của quản trị viên để nhận báo lỗi/góp ý |
| `DB_HOST` | Địa chỉ kết nối host của PostgreSQL |
| `DB_NAME` | Tên cơ sở dữ liệu hệ thống |
| `DB_USER` | Tên người dùng quyền cấu hình Database |
| `DB_PASS` | Mật khẩu truy cập Database |
| `CELERY_BROKER_URL` | URL kết nối hàng đợi Redis (Ví dụ: `redis://uth_redis:6379/0`) |
| `ENCRYPTION_KEY` | Khóa mã hóa thông tin AES-256 được tạo bởi thư viện Fernet |

### 2. Cấu hình tính năng mở rộng (Tùy chọn)
*Nếu thiếu các biến này, chức năng tương ứng sẽ tự động ẩn trên Menu Bot.*

| Biến | Mô tả | Chức năng ảnh hưởng |
| :--- | :--- | :--- |
| `WEATHER_API_KEY` | API Key lấy từ nền tảng [weatherapi](https://www.weatherapi.com/) | Hiển thị thời tiết theo ca học tại các cơ sở |
| `PAYOS_CLIENT_ID` | Client ID được cấp từ ứng dụng PayOS cá nhân | Khởi tạo cổng nhận Donate tự động |
| `PAYOS_API_KEY` | API Key kết nối cổng thanh toán của PayOS | Khởi tạo cổng nhận Donate tự động |
| `PAYOS_CHECKSUM_KEY` | Checksum Key dùng để xác thực gói tin bảo mật PayOS | Khởi tạo cổng nhận Donate tự động |

---

## 📦 Hướng dẫn triển khai (Docker)

Sử dụng Docker Compose để triển khai nhanh toàn bộ hạ tầng:

1. **Tải mã nguồn:**
    ```bash
    git clone https://github.com/vanphat111/uthCalendar.git
    cd uthCalendar
    ```
2. **Thiết lập môi trường:** Tạo file `.env` và cấu hình các biến môi trường cần thiết theo bảng hướng dẫn phía trên.
3. **Khởi chạy hệ thống:**
    ```bash
    docker compose up -d --build
    ```

Hệ thống sẽ tự khởi động các container bao gồm **Bot Engine**, **Celery Worker**, **PostgreSQL** và **Redis**.

---

## 🤝 Đóng góp (Contribution)

Dự án được phát triển bởi [**vanphat111**](https://github.com/vanphat111) (sinh viên UTH) với mục đích hỗ trợ cộng đồng. Mọi Pull Request hoặc báo lỗi đều được trân trọng.

1. Fork dự án.
2. Tạo branch mới: `git checkout -b feature/AmazingFeature`
3. Commit thay đổi: `git commit -m 'feat: add some AmazingFeature'`
4. Gửi Pull Request.

**Link dự án:** [https://github.com/vanphat111/uthCalendar](https://github.com/vanphat111/uthCalendar)