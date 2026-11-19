# Luồng học tập với dataset chung

Giáo viên giao một dataset cho cả lớp. Mỗi sinh viên phân tích theo câu hỏi, viết insight bằng lập luận của mình, nhận góp ý và cải thiện qua nhiều phiên bản.

1. **Giao bài:** tạo lớp, nhập tên và mô tả bài tập, thiết kế 1–20 câu hỏi, đặt điểm tối đa từng câu; tải CSV/XLSX. Rubric và đáp án chấm nội bộ là tùy chọn.
2. **Đặt lịch:** hạn nộp lần đầu và thời điểm mở xem bài của bạn cùng lớp là hai mốc riêng, nhập theo giờ Việt Nam (UTC+7). Giáo viên chọn chia sẻ tất cả bài đã nộp hoặc chỉ bài sinh viên chủ động chia sẻ.
3. **Làm bài:** sinh viên xem dữ liệu, hỏi trợ lý theo câu hỏi đang chọn, nhận bảng và biểu đồ, tự viết câu trả lời và chọn bằng chứng đưa vào bài. Nháp chỉ sinh viên đó và giáo viên của lớp xem được.
4. **Nộp bài:** mỗi lần nộp tạo một phiên bản cố định, lưu câu trả lời từng câu và các bằng chứng được chọn. Hệ thống tự xếp tác vụ đánh giá AI cho chính phiên bản đó.
5. **Học từ nhau:** đến giờ chia sẻ, trang “Bài chia sẻ” mở các bản đã nộp trong cùng lớp. Có thể lọc theo bài tập, chọn phiên bản và đối chiếu với bản đã nộp của mình.
6. **Đánh giá chéo:** sinh viên nhận xét bài của bạn khác bằng mức 1–5, điểm tốt, gợi ý cải thiện và điều học được. Một sinh viên có một đánh giá có thể sửa cho mỗi phiên bản. Đánh giá cũ không chuyển sang phiên bản mới. Bình luận vẫn có thể dùng để thảo luận chung.
7. **Đánh giá giáo viên và AI:** giáo viên chọn phiên bản đã nộp để chấm từng câu và công bố điểm. AI trả trạng thái từng câu, chất lượng tổng thể và gợi ý; nếu không thể kiểm tra dataset, hệ thống không ghi nhận kết luận số liệu là đã xác minh. Điểm giáo viên được lưu riêng cho từng phiên bản.
8. **Cải thiện:** nếu giáo viên cho phép, sinh viên đã có bài nộp được sửa nháp và nộp bản cải thiện sau hạn khi chia sẻ đã mở. Có thể ghi điều học được và thay đổi đã làm. Bài đầu, điểm và các đánh giá trước đó vẫn được lưu. Sinh viên chưa nộp lần đầu không dùng chế độ cải thiện để nộp muộn.

## Bắt đầu dùng

Khi tạo bài, có thể bật **Cho AI tạo câu hỏi và đáp án từ dataset**. Nhập thông tin, tải dataset rồi chọn số câu (1–20), độ khó và yêu cầu thêm. Bấm **Tạo câu hỏi và đáp án bằng AI**; tác vụ chạy nền và có thể xem lại khi mở bài nháp. AI thiết kế câu hỏi theo cột dữ liệu, dùng DA-Agent tính kết quả trên dataset và soạn đáp án mẫu. Giáo viên xem kết quả phân tích, sửa câu hỏi, điểm và đáp án rồi bấm **Lưu đề và đáp án đã duyệt** trước khi công bố.

Đáp án AI lưu vào đáp án chấm nội bộ và bản nháp bài tham khảo. Sinh viên không đọc được đáp án hoặc tác vụ tạo đề. Giáo viên tự quyết định có công bố bài tham khảo hay không; bài tham khảo chỉ mở cho sinh viên đã nộp lần đầu. Bộ câu hỏi không được thay sau khi đã công bố. Nếu dataset thay đổi trong lúc AI chạy, cần tạo lại đề trước khi áp dụng.

Màn hình duyệt đề mặc định hiển thị câu hỏi và đáp án đã định dạng, hỗ trợ bảng Markdown và công thức LaTeX. Dùng các nút “Câu 1”, “Câu 2”… để đi nhanh; có thể mở hoặc thu gọn tất cả câu. Bấm **Chỉnh sửa** trên từng câu để sửa nội dung và điểm, rồi **Xem trình bày** để kiểm tra. Nội dung sửa chỉ được lưu vào hệ thống khi bấm **Lưu đề và đáp án đã duyệt**.

Công thức trong dòng dùng `$...$`, công thức riêng dòng dùng `$$` trên hai dòng bao quanh biểu thức. Ví dụ `$\bar{x}$` hoặc:

```latex
$$
\bar{x} = \frac{1}{n}\sum_{i=1}^{n}x_i
$$
```

Hệ thống cũng nhận `\(...\)` và `\[...\]`. Bảng, công thức và biểu đồ được hiển thị trong bài tham khảo, hội thoại AI và bài đã nộp.

Xem `DU_LIEU_MAU.md` để đăng nhập tài khoản giáo viên và năm sinh viên Demo, thử các bài đang làm, đã chia sẻ và cải thiện.

Mở `http://127.0.0.1:5173`. Giáo viên vào một lớp và tạo bài tập. Trong trang quản lý bài, mục **Lịch chia sẻ và cải thiện** cho phép cập nhật lịch và cách chia sẻ. Sinh viên vào **Bài chia sẻ** sau khi đến giờ mở.

Bài tập mới mặc định chia sẻ tất cả bản đã nộp theo lịch và cho nộp bản cải thiện. Bài tập có sẵn trước lần cập nhật này giữ cách chia sẻ tự chọn và hạn nộp cũ; giáo viên có thể đổi trong mục lịch.

## Dữ liệu và kiểm thử

Migration `0004_peer_learning` thêm lịch chia sẻ, đánh giá chéo và thông tin từng phiên bản; dữ liệu cũ được giữ. Database được sao lưu trong `var/backups` trước khi nâng cấp.

Các kiểm thử backend dùng database riêng được cấu hình trong `backend/tests/conftest.py`. Bộ dữ liệu Demo được thêm vào các lớp có nhãn riêng; tài khoản, lớp và bài cũ giữ nguyên.
## AI so sánh các bài đã nộp

Trang **Bài chia sẻ và đánh giá chéo** có phần **AI so sánh bài**. Sinh viên chọn phiên bản bài mình và 1–3 bài của các sinh viên khác; giáo viên chọn bài gốc của một sinh viên. Chỉ mở sau thời điểm chia sẻ và chỉ sử dụng các bài được phép xem theo cấu hình toàn lớp/tự nguyện.

AI dùng một lượt gọi có cấu trúc để so sánh báo cáo theo từng câu hỏi: điểm mạnh và phần cần bổ sung của bài gốc; tương đồng, khác biệt và phương pháp có thể học từ từng bạn; gợi ý cải thiện. Không chạy lại DA-Agent, không đưa đáp án riêng tư, bản nháp hoặc điểm chưa công bố vào ngữ cảnh. Nhận xét hỗ trợ học tập, không phải điểm chính thức hay kiểm chứng dữ liệu độc lập.

Kết quả gắn với phiên bản cố định, lưu trong lịch sử và tiếp tục xử lý khi rời trang. Yêu cầu trùng phiên bản dùng lại tác vụ/kết quả. Khi thu hồi chia sẻ hoặc lùi giờ mở, API chặn việc xem lại các kết quả dùng bài không còn được phép xem. API: `GET /api/assignments/{id}/ai/comparisons`, `POST /api/assignments/{id}/ai/compare-submissions` (base_version_id, peer_version_ids), `GET /api/jobs/{id}`. Không cần migration mới vì sử dụng hàng đợi AIJob hiện có.

