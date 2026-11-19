# AI so sánh bài, Thảo luận và gợi ý theo câu hỏi

Toàn ứng dụng dùng chung tông xanh dương, nền sáng và font Segoe UI/Arial. Các giá trị màu/font nằm trong `frontend/src/styles/tokens.css`, giao diện chung và màn hình tài khoản trong `frontend/src/styles/theme.css`. Sidebar, tổng quan, lớp học, bài tập sinh viên/giáo viên và hộp thoại cùng sử dụng bộ màu này. Đăng nhập/đăng ký có chọn vai trò, hiện/ẩn mật khẩu và thông báo lỗi đồng bộ.

Giao diện Thảo luận gồm danh sách bài có tìm kiếm ở bên trái và bài được chọn ở bên phải, với tab bài làm/thảo luận, xem trước biểu đồ đính kèm, mở toàn bộ bài và đánh giá. Trên điện thoại, danh sách chuyển thành các thẻ cuộn ngang.

AI so sánh dùng hai thẻ chọn chế độ, bảng sinh viên có tìm kiếm/chọn nhiều bài và kết quả theo tab tổng quan/từng câu hỏi. Tổng quan phân biệt điểm mạnh, phần cần cải thiện và hướng phát triển bằng ba nhóm màu. Kiểm tra giao diện với lớp demo tạm: `python tests/ui_learning_smoke.py --visual`.

## Luồng sử dụng

- Menu **AI so sánh bài** (`/comparison`) và **Thảo luận** (`/discussion`) độc lập. Từ bài tập, sinh viên có thể mở trực tiếp từng chức năng và giữ bộ lọc lớp/bài tập. Đường dẫn cũ `/gallery` vẫn mở Thảo luận.
- **So sánh bài với người khác** tự chọn bản cuối cùng có `submitted_at < due_at` cho mỗi sinh viên. Không cho chọn bản cũ hơn, bản cải thiện hay bản nháp. Có thể chọn từng bạn hoặc chọn tất cả những bạn được phép chia sẻ. Worker xử lý theo nhóm tối đa ba bài để giới hạn ngữ cảnh, sau đó ghép đủ nhận xét của tất cả bài được chọn.
- **So sánh 2 phiên bản của mình** cố định bản cuối trước hạn và cho chọn một bản mới nộp lại từ thời điểm hết hạn. AI nhận xét thay đổi, tiến bộ và điểm cần tiếp tục cải thiện. Không có bài trước hạn hoặc chưa có bản cải thiện thì giao diện giải thích và dẫn về bài tập.
- Hai chế độ có lịch sử riêng; kết quả lưu theo phiên bản cố định. Khi đọc lịch sử, quyền thành viên, lịch mở chia sẻ và quyền chia sẻ vẫn được kiểm tra lại. Lịch sử cũ vẫn được giữ dù về sau có thêm phiên bản nộp.
- **Thảo luận** hiển thị bài đã nộp, lịch sử phiên bản, bình luận mở sẵn dưới mỗi bài, đánh giá 1–5 và góp ý. Có bình chọn **Bài hay** cho toàn bài, mỗi người một lượt, được thu hồi, không tự bình chọn. Sắp xếp theo bình chọn, bình luận hoặc tên sinh viên. Điểm giáo viên độc lập với bình chọn/đánh giá của lớp.
- Mỗi câu hỏi có nút **Gợi ý ý tưởng**. Gợi ý được lưu theo người dùng và nội dung câu hỏi; yêu cầu lặp trả lại tác vụ/kết quả đã có. Thất bại có thể thử lại.

## Giới hạn nội dung AI gợi ý

`backend/app/question_hints.py` định nghĩa các hướng tư duy đã duyệt: làm rõ yêu cầu, chọn biến, phân nhóm, chất lượng dữ liệu, thống kê, trực quan hóa, kiểm định, dự đoán, giới hạn và bằng chứng. AI chỉ chọn mã hướng phù hợp theo câu hỏi công khai. Server chỉ hiển thị văn bản có sẵn trong danh mục, không hiển thị nội dung tự do do AI sinh ra, kể cả khi AI trả mã chứa đáp án hoặc sinh viên yêu cầu bỏ qua quy tắc.

Luồng gợi ý và chat trợ giảng không nhận đáp án mẫu, không chạy graph giải bài, không đọc dataset, không sinh bảng kết quả/code/biểu đồ chứa đáp án. Chat dùng cùng cơ chế chọn hướng tư duy. Luồng chấm bài nội bộ, tạo đề và bài tham khảo giáo viên vẫn có chức năng riêng.

## Cơ sở dữ liệu và chạy ứng dụng

Migration mới `0005_submission_votes` chỉ bổ sung bảng bình chọn, khóa duy nhất `(submission_id, voter_id)` và khóa ngoại. Nâng cấp database trước khi chạy API/worker:

```powershell
cd backend
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
# Terminal khác, cùng thư mục backend:
.\.venv\Scripts\python.exe -m app.worker
# Terminal frontend:
npm.cmd run dev
```

AI thật cần cấu hình nhà cung cấp/khóa trong `.env` và worker đang chạy.

## Kiểm tra

```powershell
# Trong backend, dùng database tạm riêng:
.\.venv\Scripts\python.exe -m pytest tests -q
# Trong frontend:
npm.cmd run build
# Trong backend, kiểm tra trên Chrome với AI giả lập và dữ liệu tạm:
.\.venv\Scripts\python.exe tests/ui_learning_smoke.py
```

Smoke test cần Chrome và thư viện Playwright có sẵn; nó tự mở API/Vite trên loopback cổng 8009/4189 và đóng các tiến trình đã tạo sau khi kiểm tra. Các thao tác kiểm tra gồm so sánh với bạn, so sánh hai bản của mình, bình chọn, bình luận, đánh giá, gợi ý từng câu và bố cục di động. Không gọi LLM thật.
