# Kịch bản demo DataClass

Mở **http://127.0.0.1:5173**. Hệ thống đã có dữ liệu và đang chạy trên máy này.

## Tài khoản

Mật khẩu chung cho các tài khoản demo: **`Demo@2026!`**.

| Vai trò | Email |
|---|---|
| Giáo viên | `giaovien.demo@dataclass.local` |
| Sinh viên 1 — Nguyễn Minh Anh | `sinhvien1.demo@dataclass.local` |
| Sinh viên 2 — Trần Quốc Bảo | `sinhvien2.demo@dataclass.local` |
| Sinh viên 3 — Lê Thu Chi | `sinhvien3.demo@dataclass.local` |
| Sinh viên 4 — Phạm Hải Dương | `sinhvien4.demo@dataclass.local` |
| Sinh viên 5 — Võ Ngọc Hà | `sinhvien5.demo@dataclass.local` |

Hai lớp: **Phân tích dữ liệu kinh doanh**, mã `DADEMO26`; **Thống kê và học từ dữ liệu**, mã `STATDEMO26`. Năm sinh viên đã có trong cả hai lớp.

## Trình diễn trong khoảng 10–15 phút

1. **Giao bài và soạn đề AI:** đăng nhập giáo viên, vào lớp Thống kê, mở **[Demo] Soạn đề kiểm tra bằng AI**. Có sẵn CSV, câu hỏi và đáp án được sinh bằng AI thật để xem ngay; duyệt câu hỏi, bảng số liệu, công thức và đáp án riêng tư. Có thể chỉnh sửa trước khi công bố. Muốn diễn luồng từ đầu, tạo bài tập mới, chọn tạo đề bằng AI và tải `demo/datasets/student_learning.csv`. Chọn 3 câu để thời gian chạy phù hợp buổi demo.
2. **Làm bài và trợ giảng:** đăng nhập sinh viên 3 hoặc 4, mở **[Demo] Doanh thu bán lẻ — đang làm**. Xem dữ liệu, bản nháp, câu trả lời từng câu và lịch sử gợi ý/biểu đồ. Chỉnh câu trả lời, chọn bằng chứng rồi lưu nháp. Nộp nếu muốn diễn việc tạo phiên bản cố định và AI đánh giá.
3. **Bảo vệ bài trước giờ mở:** mở **[Demo] Kết quả học tập — chờ mở chia sẻ**. Bài vẫn riêng tư; trang chia sẻ hiển thị thời điểm mở. AI so sánh chưa được phép chạy.
4. **Học từ năm cách phân tích:** mở lớp Kinh doanh → **[Demo khách] So sánh 5 cách phân tích doanh thu**, rồi bấm **Xem bài cùng lớp**. Hoặc vào [trang demo so sánh](http://127.0.0.1:5173/gallery?class=7&assignment=10) trên máy hiện tại.
5. **AI so sánh:** chọn phiên bản bài gốc và 1–3 bài bạn khác. Các kết quả mẫu đã lưu cho mọi tài khoản giúp trình diễn ngay. Mở từng câu để xem điểm mạnh, phần thiếu, tương đồng, khác biệt và điều có thể học. Bấm **So sánh bằng AI** để gửi yêu cầu thật; trạng thái thể hiện đang chờ/đang xử lý và kết quả được lưu vào lịch sử. Có thể rời trang rồi quay lại. Yêu cầu trùng các phiên bản đã so sánh thật sẽ dùng lại kết quả đã lưu.
6. **Đánh giá chéo và thảo luận:** bên dưới phần AI là năm bài chia sẻ. Chọn phiên bản, đọc bảng/biểu đồ, đánh giá sao và viết điểm mạnh, góp ý, điều học được. Có sẵn nhận xét và thảo luận mẫu; sinh viên chỉ sửa đánh giá của chính mình và không tự đánh giá bài mình.
7. **Cải thiện có lưu lịch sử:** quay lại bài tập, sửa phần lập luận, ghi điều học từ bạn và nộp bản cải thiện. Sinh viên 1 đã có hai phiên bản để xem ngay. Bản gốc, đánh giá chéo và điểm giáo viên của bản gốc vẫn được giữ lại.
8. **Giáo viên đánh giá:** đăng nhập giáo viên, mở bài demo so sánh → bài nộp sinh viên. Chọn từng phiên bản, xem phản hồi AI/đánh giá chéo, chấm theo từng câu và công bố điểm. Ba sinh viên đã có điểm mẫu; bản cải thiện của sinh viên 1 chưa được chấm để trình diễn thao tác này. Giáo viên cũng có thể chọn một sinh viên làm bài gốc và so sánh với các bài khác trong trang chia sẻ.
9. **Đáp án tham khảo:** bài demo so sánh có đáp án tham khảo đã công bố. Sinh viên đã nộp mới được xem; đáp án riêng tư và điểm chưa công bố không được đưa vào ngữ cảnh AI so sánh.

## Nội dung mới đã chuẩn bị

CSV bán lẻ có **180 đơn hàng, 10 cột**, tổng doanh thu **742.510.000 VND**, lợi nhuận **228.308.000 VND**. Bài tập demo mới có ba câu, năm bài nộp, sáu phiên bản, năm biểu đồ, năm đánh giá chéo, năm bình luận, ba điểm mẫu và sáu nhận xét so sánh mẫu (năm sinh viên, một giáo viên).

| Bài sinh viên | Điểm nhấn để trình diễn |
|---|---|
| 1 | Kiểm tra dữ liệu, công thức, tổng hợp doanh thu; đã có bản cải thiện |
| 2 | Biên lợi nhuận: Bắc 40%, Trung 32%, Nam 28%; phân biệt quy mô và hiệu quả |
| 3 | Tỷ trọng doanh thu, biểu đồ tròn; phân biệt tỷ trọng và tỷ suất |
| 4 | Thiếu phép tính và có đề xuất vượt bằng chứng, để minh họa góp ý |
| 5 | Cơ cấu sản phẩm và giới hạn suy luận; không kết luận nhân quả theo vùng |

Nhận xét tạo bằng script có nhãn **DỮ LIỆU MẪU**. Kết quả gọi AI thật hiển thị **Nhận xét đã lưu** và không có nhãn mẫu. AI so sánh chỉ đọc báo cáo đã nộp, không chạy lại CSV hoặc đọc nội dung ảnh, không cho điểm chính thức. Nếu nhà cung cấp AI giới hạn lượt gọi hoặc hàng đợi đang bận, vẫn có thể trình diễn bằng các kết quả đã lưu.

## Khởi động lại và bổ sung dữ liệu

Tại thư mục `web-02`:

```powershell
powershell -ExecutionPolicy Bypass -File start.ps1
```

Để tạo dữ liệu trên một database mới đã migration, chạy lần lượt trong `web-02/backend`:

```powershell
.\.venv\Scripts\python.exe -m app.seed_demo
.\.venv\Scripts\python.exe -m app.seed_comparison_demo
```

Các script chạy lại sẽ giữ dữ liệu đã có, không đặt lại mật khẩu hoặc sửa bài đang làm. Script bổ sung tạo bản sao lưu SQLite trước khi thêm dữ liệu. Mã bài/lớp trên máy mới nằm trong `var/demo-seed.json` và `var/demo-comparison.json`; liên kết có ID trong tài liệu này áp dụng cho database trên máy hiện tại.
