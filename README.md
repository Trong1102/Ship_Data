# CAN-SHIP: Hệ Thống Quản Lý Dữ Liệu Tàu Biển

Hệ thống giám sát và quản lý dữ liệu tàu biển thời gian thực, bao gồm Backend API, Frontend Dashboard và Simulator giả lập dữ liệu hành trình.

## 🚀 Tính Năng Chính

- **Live Dashboard**: Giám sát vị trí tàu trên bản đồ tương tác (Leaflet).
- **Chỉ số thời gian thực**: Theo dõi RPM, Tốc độ, Tiêu thụ nhiên liệu.
- **Phân tích lịch sử**: Xem lại lộ trình hành trình và biểu đồ nhiên liệu theo khoảng thời gian.
- **Simulator**: Giả lập dữ liệu tàu di chuyển thực tế với chu kỳ tùy chỉnh.

## 🛠 Công Nghệ Sử Dụng

- **Backend**: Python, FastAPI, SQLAlchemy, SQLite.
- **Frontend**: React (Vite), TailwindCSS, Lucide React, Recharts, React-Leaflet.
- **Simulator**: Python (Requests).

## 📂 Cấu Trúc Dự Án

```text
CAN-SHIP/
├── backend/          # FastAPI Server & Database logic
├── frontend/         # React Application (Dashboard UI)
├── ship_simulator/   # Python script giả lập dữ liệu tàu
├── schema.json       # Cấu trúc Database chi tiết
└── .gitignore        # Các file không đẩy lên git
```

## ⚙️ Hướng Dẫn Cài Đặt

### 1. Backend
```bash
cd backend
# Tạo môi trường ảo (nếu chưa có)
python -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
# Chạy server
uvicorn main:app --reload
```

### 2. Frontend
```bash
cd frontend
npm install
npm run dev
```

### 3. Simulator
```bash
cd ship_simulator
# Sử dụng venv của backend hoặc tạo mới
python run_simulation.py
```

## 📊 Database Schema
Chi tiết cấu trúc bảng (Users, Ships, Telemetry) có thể tìm thấy trong file [schema.json](./schema.json).

---
*Dự án được phát triển để hỗ trợ quản lý và phân tích năng lượng vận hành tàu thủy.*
