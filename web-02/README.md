# DataClass · web-02

Nền tảng học phân tích dữ liệu bằng React, FastAPI, SQLite và graph LangGraph trong `../DA-Agent-drive`. Mọi cấu hình và dữ liệu chạy của ứng dụng nằm trong thư mục này hoặc Docker volume; graph được đưa vào container backend ở chế độ chỉ đọc.

Tài liệu chuẩn bị bảo vệ: [30 câu hỏi phản biện và gợi ý trả lời](README_PHAN_BIEN.md). Kịch bản trình diễn: [Demo với khách hàng](DEMO_KHACH_HANG.md).

## Chạy bằng Docker Compose

1. Tạo file cấu hình và đặt khóa LLM/E2B dùng bởi graph:

   ```bash
   cp .env.example .env
   ```

   Đặt `WEB02_SECRET_KEY` thành chuỗi ngẫu nhiên dài. Chọn `LLM_PROVIDER` và khóa tương ứng (`GEMINI_API_KEY` hoặc `DEEPSEEK_API_KEY`). E2B được gọi khi graph cần chạy Python tùy biến.

2. Khởi động dịch vụ:

   ```bash
   docker compose up --build -d
   ```

3. Tạo tài khoản giáo viên đầu tiên:

   ```bash
   docker compose run --rm api python -m app.bootstrap
   ```

   Nhập email, tên và mật khẩu khi được hỏi. Có thể đặt `BOOTSTRAP_TEACHER_EMAIL`, `BOOTSTRAP_TEACHER_NAME` và `BOOTSTRAP_TEACHER_PASSWORD` trong `.env` để không nhập tương tác. Lệnh chỉ tạo giáo viên khi database chưa có tài khoản giáo viên.

4. Mở `http://localhost:8080`. Giáo viên tạo lớp và gửi mã tham gia; sinh viên đăng ký rồi nhập mã đó.

Để đưa lên máy chủ HTTPS, cấu hình reverse proxy/TLS phía trước cổng frontend, đặt `WEB02_ENV=production`, `WEB02_COOKIE_SECURE=true`, đổi `WEB02_SECRET_KEY`, rồi khởi động lại. Volume `web02_data` chứa SQLite, dataset tải lên và artifact; cần sao lưu volume này định kỳ.

## Chạy khi phát triển

Backend cần Python 3.12 và `DA-Agent-drive` nằm cạnh `web-02` như trong workspace hiện tại.

```bash
cd backend
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt -r graph-requirements.txt
alembic upgrade head
python -m app.bootstrap
```

Trong terminal backend chạy `uvicorn app.main:app --reload --port 8000`; trong terminal khác chạy `python -m app.worker`; trong terminal frontend:

```bash
cd ../frontend
npm install
npm run dev
```

Vite chuyển tiếp `/api` tới FastAPI. Dữ liệu và artifact cục bộ nằm ở `web-02/var`.

## Vận hành và tích hợp graph

- Các tác vụ chat và đánh giá được lưu trong SQLite rồi worker lấy xử lý. Trạng thái gồm `queued`, `running`, `done` và `failed`.
- Backend chỉ gửi dataset của bài tập cho graph. Đáp án mẫu chỉ đi vào bước chấm nội bộ; phản hồi sinh viên chỉ nhận trạng thái tiêu chí và gợi ý giáo viên đã cấu hình.
- Đường dẫn artifact cục bộ từ câu trả lời graph được đổi thành `/api/assets/{id}`. Endpoint kiểm tra quyền người dùng trước khi trả file; báo cáo chia sẻ chỉ truy cập được biểu đồ được nhúng trong phiên bản công khai.
- Các tệp được giới hạn mặc định 10 MB mỗi tệp và 20 MB mỗi bài tập. Chỉ CSV/XLSX được nhận.
- Thay đổi schema SQLite được quản lý bằng Alembic (`backend/migrations`). Chạy `alembic upgrade head` trước khi khởi động API hoặc worker.
