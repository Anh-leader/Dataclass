# Dữ liệu mẫu để thử hệ thống

Mở http://127.0.0.1:5173. Các tài khoản mới dưới đây có mật khẩu chung **Demo@2026!**. Các tài khoản cũ giữ nguyên mật khẩu.

| Vai trò | Email |
| --- | --- |
| Giáo viên Demo | giaovien.demo@dataclass.local |
| Nguyễn Minh Anh | sinhvien1.demo@dataclass.local |
| Trần Quốc Bảo | sinhvien2.demo@dataclass.local |
| Lê Thu Chi | sinhvien3.demo@dataclass.local |
| Phạm Hải Dương | sinhvien4.demo@dataclass.local |
| Võ Ngọc Hà | sinhvien5.demo@dataclass.local |

Cả năm sinh viên đã tham gia hai lớp:

- **[Demo] Phân tích dữ liệu kinh doanh**, mã **DADEMO26**.
- **[Demo] Thống kê và học từ dữ liệu**, mã **STATDEMO26**.

| Bài tập | Tình huống thử |
| --- | --- |
| Doanh thu bán lẻ — đang làm | Hai sinh viên đã nộp, hai đang lưu nháp; hạn nộp chưa đến |
| Doanh thu bán lẻ — chia sẻ và cải thiện | Cả năm đã nộp, có đánh giá chéo, bình luận, điểm giáo viên; sinh viên 1 có hai phiên bản và bản ghi điều học được |
| Kết quả học tập — chờ mở chia sẻ | Có bài nộp và nháp; chia sẻ còn khóa theo lịch, chế độ sinh viên tự bật chia sẻ |
| Soạn đề kiểm tra bằng AI | Bản nháp kèm dataset để giáo viên chọn số câu, độ khó và tạo câu hỏi, đáp án bằng AI |

Dataset gốc trong `demo/datasets/`: `retail_sales.csv` có 180 dòng, `student_learning.csv` có 80 dòng. Toàn bộ là dữ liệu giả lập; không chứa thông tin sinh viên thật. Bài mẫu có đáp án tính bằng pandas và biểu đồ, bằng chứng được lưu trong các bài nộp.

Các phản hồi AI, hội thoại và điểm được **seed** đều gắn nhãn **DỮ LIỆU MẪU** để phân biệt với kết quả AI thật. Những yêu cầu AI mới thực hiện trên giao diện dùng DA-Agent và mô hình đã cấu hình trong `.env`.

## Tạo dữ liệu trên máy khác

Sau khi chạy migration, mở terminal tại `web-02/backend`:

```powershell
.venv/Scripts/python.exe -m app.seed_demo
```

Script thêm dữ liệu, sao lưu SQLite vào `var/backups`, không sửa tài khoản hoặc lớp hiện có. `var/demo-seed.json` lưu ID đã tạo; chạy lại không nhân bản hoặc ghi đè bài Demo đã được chỉnh sửa. Lịch bài tập được tính từ thời điểm seed. Giáo viên có thể điều chỉnh trong mục “Lịch chia sẻ và cải thiện”.
## Demo so sánh bài bằng AI

Bộ dữ liệu mở rộng và kịch bản trình diễn khách hàng ở [DEMO_KHACH_HANG.md](DEMO_KHACH_HANG.md). Chạy `python -m app.seed_comparison_demo` sau seed cũ để thêm một bài tập có năm cách phân tích, lịch sử cải thiện, đánh giá chéo, điểm và nhận xét so sánh mẫu. Các bài đang có được giữ nguyên.

