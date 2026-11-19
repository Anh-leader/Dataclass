# Dataset giả lập

- `datasets/retail_sales.csv`: 180 đơn hàng trong sáu tháng năm 2026. `units` là số lượng; `unit_price`, `revenue`, `cost`, `profit` dùng VND. `revenue = units × unit_price`, `profit = revenue − cost`. Mỗi vùng gắn với một loại sản phẩm để có thể thảo luận giới hạn khi so sánh vùng.
- `datasets/student_learning.csv`: 80 mã sinh viên giả lập, hai nhóm A/B. Giờ học mỗi tuần, tỷ lệ chuyên cần theo phần trăm, điểm bài tập và điểm thi theo thang 10. Dữ liệu có tương quan giờ học/điểm nhưng không dùng làm bằng chứng về quan hệ nhân quả trong thực tế.

Dữ liệu được sinh bằng seed cố định trong `backend/app/seed_demo.py`. Xem `../DU_LIEU_MAU.md` để đăng nhập và thử luồng nghiệp vụ.
