# Chạy DataClass trên Windows

Project chính nằm trong `web-02`; `DA-Agent-drive` là bộ máy AI mà backend sử dụng. Thư mục `src` ở ngoài cùng chỉ có một file trống.

## Khởi động

Nhấp đúp `start.bat` trong thư mục `web-02`, hoặc mở PowerShell tại thư mục đó và chạy:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\start.ps1
```

Script chạy ngầm ba dịch vụ: FastAPI ở cổng 8000, AI worker và Vite ở cổng 5173. Trình duyệt tự mở **http://127.0.0.1:5173** khi API và giao diện đã sẵn sàng. Có thể đóng cửa sổ khởi động; các dịch vụ vẫn chạy. Chạy lại script sẽ sử dụng các tiến trình đã khởi động, không tạo thêm worker.

Để chạy mà không mở trình duyệt, thêm `-NoBrowser`.

## Đăng nhập

Tài khoản giáo viên có sẵn: `teacher@example.edu` / `H6BDOVUBGW`.

Sinh viên có thể đăng ký trên giao diện và tham gia lớp bằng mã lớp.

## Dừng

Mở PowerShell tại `web-02`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\stop.ps1
```

Script chỉ dừng các tiến trình DataClass đã được `start.ps1` ghi nhận.

## Log và dữ liệu

- Log API: `var/run/backend.err.log` và `backend.out.log`.
- Log worker: `var/run/worker.err.log` và `worker.out.log`.
- Log giao diện: `var/run/frontend.err.log` và `frontend.out.log`.
- Database: `var/web02.sqlite3`; dataset: `var/uploads`; biểu đồ: `var/artifacts`.
- Cấu hình backend và khóa AI được đọc từ `.env` trong `web-02`.
- Khi chạy, script cập nhật schema bằng Alembic. Nếu thư mục project bị di chuyển, script sửa các đường dẫn dataset/biểu đồ cũ khi tìm được tệp tương ứng và sao lưu database vào `var/backups` trước khi thay đổi.

## Cài lại môi trường khi cần

Backend cần Python 3.12. Nếu có `uv`, chạy tại `web-02`:

```powershell
uv python install 3.12
uv venv --python 3.12 --seed backend/.venv
uv pip install --python backend/.venv/Scripts/python.exe -r backend/requirements.txt -r backend/graph-requirements.txt
```

Nếu không có `uv`, dùng Python 3.12 đã cài để tạo venv và chạy pip theo README.

Frontend:

```powershell
cd frontend
npm.cmd install
npm.cmd run build
```

Database hiện đã có tài khoản và lớp học, không cần chạy lại bootstrap. Không cần Docker khi chạy theo hướng dẫn này.
