# 30 câu hỏi phản biện và gợi ý trả lời — DataClass

Tài liệu chuẩn bị bảo vệ project học phân tích dữ liệu với dataset dùng chung, trợ giảng AI, chia sẻ bài, đánh giá và cải thiện qua nhiều phiên bản.

**Căn cứ:** mã nguồn hiện tại trong `web-02` và `DA-Agent-drive`, ngày 07/10/2026. Các câu trả lời viết theo cách xưng “em” để có thể luyện nói. Điều chỉnh cách xưng hô theo buổi bảo vệ.

## Cách sử dụng

- Tập trả lời mỗi câu trong khoảng 30–60 giây: kết luận trước, giải thích cơ chế, rồi nêu một ví dụ hoặc giới hạn.
- Phân biệt **chức năng đã triển khai**, **kết quả kiểm thử** và **hướng phát triển**. Không trình bày định hướng như tính năng đã có.
- Chuẩn bị demo một luồng đầy đủ: giao bài → sinh viên làm và nộp → mở chia sẻ → đánh giá/AI so sánh → nộp bản cải thiện.
- Các câu dễ bị hỏi sâu: **5, 9, 18, 20, 22, 25, 27, 28, 29 và 30**.

| Nhóm | Câu | Nội dung |
|---|---|---|
| I | 1–5 | Bài toán, mục tiêu và đóng góp |
| II | 6–10 | Kiến trúc và công nghệ |
| III | 11–15 | Nghiệp vụ và tính công bằng |
| IV | 16–20 | Tạo đề, đánh giá và độ tin cậy của AI |
| V | 21–25 | AI so sánh bài và học từ bạn |
| VI | 26–30 | Kiểm thử, vận hành và giới hạn |

## I. Bài toán, mục tiêu và đóng góp

### 1. Project giải quyết vấn đề gì?

**Gợi ý trả lời:**

Em giải quyết bài toán tổ chức một bài tập phân tích dữ liệu cho cả lớp, từ giao dataset đến phản hồi và cải thiện bài. Sinh viên cùng làm trên một nguồn dữ liệu nhưng có thể chọn cách phân tích và diễn giải khác nhau. Hệ thống giúp lưu lại câu trả lời, bằng chứng và từng phiên bản, sau đó mở bài theo lịch để các bạn học từ nhau. Giáo viên, bạn học và AI có các vai trò phản hồi riêng, giúp sinh viên nhìn lại cả kết quả lẫn cách lập luận.

**Ví dụ khi demo:** cùng CSV bán lẻ, một bạn tập trung doanh thu, một bạn xem biên lợi nhuận, một bạn phân tích giới hạn do cơ cấu sản phẩm.

### 2. Hệ thống khác gì một hệ thống nộp bài hoặc chatbot phân tích dữ liệu thông thường?

**Gợi ý trả lời:**

Điểm tập trung của project là kết nối hoạt động phân tích với một quy trình học tập có lớp, bài tập, lịch chia sẻ và lịch sử cải thiện. Một cuộc trò chuyện riêng lẻ chưa quản lý được việc ai được xem bài nào, phiên bản nào đã nộp hay đánh giá đang gắn với bản nào. DataClass kết hợp trợ giảng phân tích, bài nộp có bằng chứng, đánh giá chéo và so sánh cách làm trên cùng dataset. Em không khẳng định mọi thành phần đều mới; đóng góp nằm ở cách tích hợp chúng và kiểm soát nghiệp vụ cho tình huống này.

### 3. Ai sử dụng hệ thống và quyền của mỗi người là gì?

**Gợi ý trả lời:**

Hai vai trò chính là giáo viên và sinh viên. Giáo viên tạo lớp, giao bài, tải dữ liệu, thiết lập câu hỏi và lịch, duyệt đề AI, xem bài và công bố điểm. Sinh viên tham gia bằng mã lớp, làm bài, hỏi trợ giảng, lưu nháp, nộp bài, đọc các bài được chia sẻ và đánh giá bạn khác. AI là dịch vụ hỗ trợ, không phải người dùng có quyền tự công bố đề hay quyết định điểm chính thức. Backend kiểm tra cả vai trò lẫn quan hệ với lớp, thay vì chỉ dựa vào việc giao diện có hiển thị nút hay không.

### 4. Vì sao xem bài của bạn có thể giúp học tốt hơn? Em đã chứng minh điều đó chưa?

**Gợi ý trả lời:**

Giả thuyết của em là việc đối chiếu nhiều cách làm giúp sinh viên nhận ra phương pháp khác, phần thiếu trong lập luận và giới hạn của kết luận. Hệ thống hỗ trợ giả thuyết đó bằng đánh giá chéo, mục ghi điều học được và bản nộp cải thiện. Tuy nhiên, việc xây được chức năng chưa chứng minh sinh viên học tốt hơn. Hiện em có thể chứng minh luồng hoạt động; để kết luận về hiệu quả học tập cần khảo sát hoặc nghiên cứu có nhóm đối chứng và đánh giá bài trước, sau khi sử dụng.

### 5. Dùng API mô hình AI và DA-Agent có sẵn thì đóng góp của em ở đâu?

**Gợi ý trả lời:**

Em trình bày rõ phần kế thừa và phần phát triển. Năng lực phân tích dữ liệu được tích hợp từ DA-Agent, còn project bổ sung quản lý lớp, bài tập, quyền truy cập, bản nộp cố định, lịch chia sẻ, đánh giá theo phiên bản và luồng học từ bạn. Em cũng tích hợp tạo đề có bước giáo viên duyệt, đánh giá AI và so sánh nhiều bài với ngữ cảnh được kiểm soát. Em không nhận rằng mình huấn luyện mô hình nền hoặc tự tạo toàn bộ DA-Agent. Đóng góp cần đánh giá bằng thiết kế, triển khai và kiểm thử hệ thống, không chỉ bằng một lời gọi API.

## II. Kiến trúc và công nghệ

### 6. Kiến trúc tổng thể của project gồm những phần nào?

**Gợi ý trả lời:**

Frontend dùng React và TypeScript để hiển thị lớp học, bài tập và phản hồi. Backend FastAPI xử lý đăng nhập, phân quyền, dữ liệu nghiệp vụ và tạo tác vụ AI. SQLite lưu người dùng, lớp, bài, phiên bản, đánh giá và hàng đợi; tệp dataset và biểu đồ được lưu riêng, có thông tin tham chiếu trong database. Worker lấy tác vụ để gọi DA-Agent hoặc mô hình ngôn ngữ rồi lưu kết quả. Cách tách này giúp API không phải giữ một yêu cầu HTTP mở trong suốt quá trình AI phân tích.

**Cách nói ngắn:** giao diện → API và database; tác vụ AI → worker → kết quả lưu lại → giao diện đọc trạng thái.

### 7. Vì sao dùng LangGraph? Hệ thống có phải nhiều agent độc lập không?

**Gợi ý trả lời:**

DA-Agent có các bước đọc cấu trúc dữ liệu, lập kế hoạch, chọn công cụ, thực thi, tổng hợp và kiểm tra câu trả lời. LangGraph biểu diễn được trạng thái và nhánh xử lý, chẳng hạn sửa code khi lỗi hoặc phân tích lại khi bằng chứng chưa đủ. Điều này giúp luồng rõ hơn một lời gọi mô hình duy nhất. Tuy nhiên, có nhiều node không tự động đồng nghĩa với nhiều agent độc lập. Với triển khai hiện tại, em mô tả đây là một workflow agent phân tích dữ liệu có nhiều bước và cơ chế điều phối.

### 8. Vì sao ưu tiên công cụ tính toán trước khi cho AI sinh Python?

**Gợi ý trả lời:**

Các thao tác phổ biến như thống kê, nhóm dữ liệu, truy vấn và vẽ biểu đồ có thể thực hiện bằng công cụ đã định nghĩa. Dùng công cụ này giúp kiểm soát đầu vào và giảm nhu cầu sinh code tùy ý. Khi một bước cần tính toán mà công cụ chưa đáp ứng, DA-Agent mới chuyển sang Python do mô hình tạo. Mô hình dùng để lựa chọn và giải thích, còn phép tính cần có kết quả thực thi. Cách này giảm phụ thuộc vào việc mô hình tự đoán số liệu, nhưng vẫn cần kiểm tra công cụ có thực hiện đúng yêu cầu hay không.

### 9. Python do AI sinh có an toàn không? Có chạy trực tiếp trên máy chủ không?

**Gợi ý trả lời:**

Trong DA-Agent hiện tại, Python được sinh chạy trong sandbox E2B, không chạy trực tiếp trong tiến trình ứng dụng trên máy chủ. Dataset được chuyển vào sandbox, đầu ra được lấy về dưới dạng kết quả và artifact; truy cập Internet của sandbox mặc định bị tắt. Có giới hạn thời gian sống của sandbox và số lần sửa lỗi/phân tích lại trong cấu hình. Tuy nhiên, prompt yêu cầu code an toàn không phải một bảo đảm tuyệt đối. Khi vận hành thực tế vẫn cần kiểm tra giới hạn tài nguyên, quyền mạng, vòng đời sandbox và việc dữ liệu được gửi sang dịch vụ bên ngoài.

### 10. Vì sao chọn SQLite? Có đủ cho một trường đại học không?

**Gợi ý trả lời:**

SQLite phù hợp giai đoạn demo và triển khai một máy vì dễ thiết lập, sao lưu và kiểm tra dữ liệu. Project dùng khóa ngoại, chế độ WAL và thời gian chờ khi database đang bận để hỗ trợ hoạt động của API và worker. Tuy vậy, em chưa chứng minh cấu hình này đáp ứng tải của toàn trường; khả năng ghi đồng thời và mở rộng nhiều máy là hạn chế cần đánh giá. Khi nhu cầu tăng, hướng phát triển là chuyển database sang PostgreSQL và dùng hàng đợi tác vụ phù hợp hơn. Việc đã dùng SQLAlchemy hỗ trợ tổ chức mã truy cập dữ liệu, nhưng chuyển hệ thống vẫn cần kiểm thử và migration.

## III. Nghiệp vụ và tính công bằng

### 11. Làm thế nào bảo đảm sinh viên cùng phân tích một dataset và một bộ câu hỏi?

**Gợi ý trả lời:**

Dataset và câu hỏi được gắn với bài tập, sinh viên trong lớp truy cập cùng bài đó. Sau khi công bố, hệ thống chặn việc tải thêm dataset và thay bộ câu hỏi để tránh yêu cầu thay đổi giữa lúc sinh viên đang làm. Khi áp dụng đề AI, backend cũng kiểm tra dataset có thay đổi so với lúc tạo đề hay không. Như vậy, tính nhất quán được kiểm soát bằng nghiệp vụ chứ không chỉ bằng nhắc nhở giáo viên. Nếu muốn tăng khả năng kiểm chứng về lâu dài, em sẽ bổ sung mã băm nội dung tệp và quản lý phiên bản dataset rõ ràng hơn.

### 12. Vì sao phải tách bản nháp và phiên bản bài nộp?

**Gợi ý trả lời:**

Bản nháp là phần sinh viên còn chỉnh sửa; phiên bản đã nộp là căn cứ để nhận xét và chấm. Mỗi lần nộp, hệ thống chụp lại câu trả lời từng câu, nội dung báo cáo, thời điểm nộp và các bằng chứng được chọn. Sửa bản nháp sau đó không ghi đè phiên bản cũ. Nếu chỉ có một bản luôn thay đổi, giáo viên và AI có thể đang đánh giá nội dung khác với nội dung đã nộp. “Cố định” ở đây là theo luồng ứng dụng, không có nghĩa database chống được mọi thao tác sửa trực tiếp của quản trị viên.

### 13. Vì sao hạn nộp và thời điểm mở chia sẻ là hai mốc riêng? Đổi URL có xem sớm được không?

**Gợi ý trả lời:**

Hạn nộp kiểm soát thời gian làm bài, còn giờ mở chia sẻ kiểm soát thời gian học từ bạn. Giáo viên có thể đặt chia sẻ sau khi các bạn đã nộp để giảm việc xem lời giải trước khi tự làm. Backend kiểm tra thời điểm, thành viên lớp, trạng thái bài tập và chế độ chia sẻ khi lấy bài hoặc yêu cầu AI so sánh. Vì vậy, đổi ID trong URL không tự tạo quyền xem. Khi lớp dùng chế độ tự nguyện, hệ thống còn kiểm tra sinh viên có bật chia sẻ bài hay không.

### 14. Cho sửa bài sau hạn có làm mất tính công bằng hoặc thay đổi điểm cũ không?

**Gợi ý trả lời:**

Em tách bài nộp ban đầu và bài cải thiện để giáo viên có thể đánh giá cả quá trình. Sau hạn, sinh viên chỉ được nộp bản cải thiện nếu đã có bài nộp trước đó, giáo viên cho phép và đã đến thời điểm chia sẻ. Người chưa nộp không dùng luồng cải thiện để nộp lần đầu muộn. Bản cải thiện tạo phiên bản mới, không xóa điểm hoặc nhận xét của bản gốc; phiên bản mới cần được chấm riêng. Cách tính điểm cuối cùng giữa các phiên bản là chính sách học phần của giáo viên, hệ thống chưa tự áp đặt công thức đó.

### 15. Đánh giá chéo có bị thiên vị hoặc đánh giá qua lại để tăng điểm không?

**Gợi ý trả lời:**

Đánh giá chéo hiện dùng để phản hồi học tập, tách khỏi điểm chính thức của giáo viên. Sinh viên không tự đánh giá bài mình; mỗi người có một đánh giá có thể sửa cho mỗi phiên bản, gồm mức 1–5, điểm tốt, góp ý và điều học được. Cấu trúc này khuyến khích nhận xét có nội dung và giúp truy lại người đánh giá. Nhưng nó chưa loại bỏ thiên vị hoặc thông đồng. Nếu dùng đánh giá chéo để tính điểm, cần nghiên cứu thêm việc phân công người đánh giá, ẩn danh, phát hiện bất thường và cơ chế giáo viên kiểm tra.

## IV. Tạo đề, đánh giá và độ tin cậy của AI

### 16. AI tạo câu hỏi và đáp án từ dataset theo quy trình nào?

**Gợi ý trả lời:**

Giáo viên chọn số câu, độ khó và yêu cầu thêm. Hệ thống tính thông tin cấu trúc, thống kê trên dữ liệu và phân biệt rõ các dòng xem trước với toàn bộ dataset, rồi yêu cầu mô hình đề xuất câu hỏi. DA-Agent tiếp tục phân tích để tạo kết quả làm căn cứ cho đáp án mẫu. Đầu ra được kiểm tra số câu và các đáp án tương ứng. Giáo viên xem, chỉnh sửa và lưu đề đã duyệt trước khi công bố; đáp án AI không tự trở thành một đề thi được phê duyệt.

### 17. Nếu câu hỏi AI tạo không phù hợp hoặc đáp án sai thì xử lý thế nào?

**Gợi ý trả lời:**

Kiểm tra định dạng và số lượng chỉ phát hiện được lỗi cấu trúc, chưa bảo đảm câu hỏi phù hợp về mặt chuyên môn. Vì vậy, luồng tạo đề có bước giáo viên duyệt câu hỏi, số liệu, cách tính và giới hạn trước khi dùng. Em yêu cầu AI bám các cột dữ liệu và không đòi kết luận nhân quả khi dữ liệu không hỗ trợ, nhưng đó vẫn là ràng buộc bằng prompt. Giáo viên có thể sửa nội dung và điểm từng câu. Hướng đánh giá tiếp theo là có bộ tiêu chí và người chuyên môn kiểm tra tính trả lời được, độ khó và mức phù hợp mục tiêu học tập.

### 18. Làm sao biết nhận xét AI đáng tin và không bịa số liệu?

**Gợi ý trả lời:**

Ở luồng đánh giá câu trả lời, hệ thống yêu cầu DA-Agent kiểm tra trên dataset trước, rồi dùng kết quả đó để tạo phản hồi có cấu trúc theo từng câu. Nếu không thực hiện được bước kiểm tra dữ liệu, hệ thống không giữ trạng thái “đạt” như thể số liệu đã được xác minh và đánh dấu chất lượng tổng thể là chưa đủ bằng chứng. Tuy nhiên, code chạy được không có nghĩa cách phân tích đúng, còn bước diễn giải bằng mô hình vẫn có thể sai. Em giảm rủi ro bằng bằng chứng thực thi và kiểm tra đầu ra, đồng thời giữ giáo viên làm người quyết định điểm và tổ chức đánh giá trên bộ bài chuẩn.

### 19. Không có rubric thì AI đánh giá thế nào? Nhận xét AI có phải điểm không?

**Gợi ý trả lời:**

Nếu có rubric, AI dùng tiêu chí giáo viên cung cấp. Nếu không có, luồng đánh giá từng câu dùng các khía cạnh như độ phù hợp câu hỏi, phương pháp, bằng chứng, insight và giới hạn kết luận. AI trả trạng thái như đạt, đạt một phần hoặc cần cải thiện, cùng gợi ý và nhận xét tổng thể. Đây là phản hồi hỗ trợ học tập, không phải điểm số chính thức. Giáo viên chấm theo từng câu, chọn phiên bản và quyết định công bố điểm; rubric trống cũng khiến đánh giá ít chuẩn hóa hơn nên em khuyến khích thiết lập tiêu chí khi cần so sánh chất lượng.

### 20. Đáp án mẫu có thể bị lộ cho sinh viên qua API hoặc phản hồi AI không?

**Gợi ý trả lời:**

Hệ thống kiểm soát hai lớp. Ở API, sinh viên không được đọc đáp án nội bộ hoặc tác vụ tạo đề; bài tham khảo chỉ mở khi giáo viên công bố và sinh viên đã nộp bài. Ở luồng AI, trợ giảng và so sánh bài không được đưa đáp án nội bộ vào ngữ cảnh; luồng đánh giá có dùng đáp án ẩn để đối chiếu nhưng yêu cầu chỉ trả góp ý, không trả lời giải. Em phân biệt phân quyền API có thể kiểm thử với khả năng mô hình diễn đạt lại thông tin: prompt không bảo đảm tuyệt đối không rò rỉ. Cần tiếp tục thử các câu hỏi đối kháng và hạn chế nội dung nhạy cảm trong ngữ cảnh đánh giá.

## V. AI so sánh bài và học từ bạn

### 21. AI so sánh bài của sinh viên với bài khác dựa trên những gì?

**Gợi ý trả lời:**

Sinh viên chọn một phiên bản bài mình và từ một đến ba phiên bản của các bạn khác trong cùng bài tập. AI nhận nội dung các báo cáo đã nộp, câu hỏi và mô tả bằng chứng được chọn, rồi so sánh theo từng câu. Kết quả gồm điểm mạnh, phần cần bổ sung của bài gốc; tương đồng, khác biệt và điều học được từ từng bạn; các bước cải thiện tiếp theo. Mục tiêu là giải thích khác biệt trong phương pháp và lập luận. Kết quả không tự chấm điểm hoặc xếp hạng sinh viên.

**Ví dụ:** chỉ ra việc bài A nhìn tổng doanh thu, còn bài B tính biên lợi nhuận nên đưa ra góc nhìn khác về hiệu quả.

### 22. AI so sánh có kiểm tra lại CSV và đọc được nội dung biểu đồ không?

**Gợi ý trả lời:**

Trong chức năng so sánh hiện tại, câu trả lời là **không**. AI dùng một lượt gọi mô hình có cấu trúc để đối chiếu báo cáo, không chạy lại DA-Agent và không gửi ảnh để đọc nội dung hình. Tên và loại bằng chứng giúp mô tả bài có đính kèm gì, không chứng minh biểu đồ đúng. Khi hai bài đưa số khác nhau, chức năng này nên chỉ ra khác biệt và đề xuất kiểm tra thay vì kết luận bài nào đúng. Giao diện nêu rõ giới hạn này; kiểm chứng số liệu thuộc luồng phân tích/đánh giá trên dataset.

### 23. Nếu bài được sửa hoặc bạn thu hồi chia sẻ, kết quả so sánh cũ còn hợp lệ không?

**Gợi ý trả lời:**

Một kết quả so sánh được gắn với các phiên bản cố định, nên sửa bản nháp hoặc nộp phiên bản mới không thay nội dung đã được so sánh. Muốn đánh giá bản mới, người dùng chọn lại phiên bản. Khi truy xuất lịch sử hoặc kết quả, backend kiểm tra các bài nguồn còn được phép xem theo cấu hình chia sẻ hiện tại hay không. Trong chế độ tự nguyện, thu hồi chia sẻ khiến kết quả dùng bài đó không còn được trả lại; lùi thời điểm mở cũng chặn truy cập. Hệ thống không thể thu hồi nội dung người dùng đã đọc hoặc tự sao chép trước đó.

### 24. Vì sao chỉ so sánh 1–3 bài? Hệ thống có tự tìm bài tương tự bằng RAG không?

**Gợi ý trả lời:**

Giới hạn ba bài giúp giữ ngữ cảnh vừa phải, nhận xét cụ thể theo từng bạn và kiểm soát độ dài, chi phí. Backend kiểm tra các phiên bản thuộc cùng bài tập và mỗi bài thuộc một sinh viên khác nhau; kết quả phải tham chiếu đúng ID câu hỏi và phiên bản được chọn. Hiện người dùng chủ động chọn bài, không có hệ thống truy hồi vector hoặc tự tìm bài tương tự bằng RAG. Với luồng này, lựa chọn trực tiếp giúp người dùng biết rõ AI đang đọc bài nào. Nếu lớp lớn, em có thể nghiên cứu tìm kiếm hoặc gợi ý bài phù hợp, nhưng phải giữ các kiểm tra quyền truy cập.

### 25. Chức năng so sánh có phát hiện đạo văn hoặc ngăn sinh viên sao chép không?

**Gợi ý trả lời:**

Hiện project không phải hệ thống xác định đạo văn. Các bài dùng cùng dataset và câu hỏi nên có thể trùng số liệu hoặc phương pháp mà không đủ căn cứ kết luận sao chép. Em giảm nguy cơ xem bài sớm bằng lịch chia sẻ, giữ bản nộp ban đầu và yêu cầu ghi điều học được khi cải thiện. AI so sánh hướng đến học phương pháp, không đưa cáo buộc gian lận. Nếu cần đánh giá tính độc lập, nên kết hợp xem lịch sử bài, yêu cầu giải thích trực tiếp và chính sách học phần; nhận xét AI hoặc mức tương đồng đơn lẻ không đủ làm bằng chứng kết luận.

## VI. Kiểm thử, vận hành và giới hạn

### 26. Em đã kiểm thử project như thế nào? 37 tests có chứng minh hệ thống hoàn toàn đúng không?

**Gợi ý trả lời:**

Bộ kiểm thử backend đã chạy qua 37 bài tại lần kiểm tra được ghi nhận trong quá trình phát triển. Các nhóm chính gồm câu hỏi/đáp án, chia sẻ và cải thiện, tạo đề AI, so sánh bài, bảo vệ dữ liệu và seed demo. Test dùng database riêng; các tình huống như xem sớm, truy cập bài người khác, thu hồi chia sẻ và giữ nguyên phiên bản được kiểm tra. Em còn build frontend và thử các luồng qua trình duyệt trên nhiều độ rộng màn hình. Những kiểm tra này chứng minh hành vi trong các tình huống đã xét, không chứng minh mọi lỗi đều được loại bỏ hoặc nội dung AI luôn đúng.

### 27. Em sẽ đo độ chính xác AI và hiệu quả học tập bằng tiêu chí nào?

**Gợi ý trả lời:**

Em tách hai mục tiêu. Với AI, cần bộ bài được chuyên gia gán nhãn, gồm bài đúng, sai số liệu, thiếu bằng chứng và kết luận vượt dữ liệu; đo khả năng nhận ra lỗi, mức đồng thuận với người chấm, tỷ lệ nhận xét không có căn cứ và độ hữu ích của gợi ý. Với học tập, so sánh chất lượng lập luận trước và sau sử dụng bằng cùng rubric, có người đánh giá độc lập và nhóm đối chứng nếu điều kiện cho phép. Thời gian phản hồi và trải nghiệm người dùng là chỉ số bổ sung. Hiện chưa có nghiên cứu đủ để công bố một tỷ lệ chính xác hay mức cải thiện học tập cụ thể.

**Khi bị yêu cầu một con số:** nêu kết quả đã đo và cách đo; không lấy số tests hoặc vài lần demo làm tỷ lệ chính xác của AI.

### 28. Project bảo vệ tài khoản và dữ liệu thế nào? Dataset có rời máy chủ không?

**Gợi ý trả lời:**

Mật khẩu được băm bằng PBKDF2 với salt riêng; API dùng phiên đăng nhập, CSRF và kiểm tra quyền với lớp, bài, phiên bản và artifact. Upload có giới hạn loại tệp, dung lượng và đường dẫn; Markdown bỏ HTML thô, công thức dùng cấu hình không tin cậy nội dung. Tuy nhiên, một phần nội dung được gửi đến nhà cung cấp mô hình, và tệp được đưa lên E2B khi cần chạy Python tùy biến. Vì vậy em không nói dữ liệu luôn ở máy nội bộ. Demo dùng dữ liệu giả lập; trước khi dùng dữ liệu thật cần xác định phạm vi được phép xử lý, loại bỏ thông tin nhạy cảm, cấu hình bảo mật và chính sách lưu trữ phù hợp.

### 29. Vì sao AI có lúc chạy lâu? Nếu mất mạng, worker dừng hoặc chi phí tăng thì sao?

**Gợi ý trả lời:**

Đánh giá từng câu có thể gọi DA-Agent nhiều lần, còn tác vụ phải chờ nhau ở worker hiện tại; tốc độ cũng phụ thuộc mô hình, sandbox và giới hạn lượt gọi. Riêng hai lần thử chức năng so sánh đã ghi nhận khoảng chín giây, nhưng đó không phải cam kết thời gian cho mọi yêu cầu. Job được lưu với trạng thái chờ, đang chạy, hoàn thành hoặc thất bại; tác vụ chạy dở quá thời gian quy định được đưa lại vào hàng đợi khi worker khởi động. Yêu cầu so sánh trùng phiên bản có thể dùng lại kết quả, giúp giảm gọi AI. Để vận hành ổn định hơn cần theo dõi độ trễ, chi phí, tải và cải thiện cơ chế retry/timeout, không chỉ thêm hiệu ứng chờ trên giao diện.

### 30. Hạn chế lớn nhất của project và hướng phát triển tiếp theo là gì?

**Gợi ý trả lời:**

Ba hạn chế chính là phụ thuộc dịch vụ AI bên ngoài, chưa có đánh giá thực nghiệm đủ về chất lượng phản hồi và hiệu quả học tập, và cấu hình một máy/worker chưa được kiểm chứng cho tải lớn. Ngoài ra, so sánh hiện chỉ đọc báo cáo, chưa đọc ảnh hay kiểm chứng lại dataset; kiểm soát chia sẻ cũng không thay thế hệ thống phát hiện đạo văn. Em ưu tiên hoàn thiện đánh giá trên bộ bài chuẩn, quan sát hàng đợi và xử lý lỗi, rồi nghiên cứu mở rộng database/hàng đợi theo số liệu tải thực tế. Sau đó mới bổ sung các chức năng như gợi ý bài để đọc, đánh giá ẩn danh hoặc kiểm chứng sâu hơn, thay vì mở rộng tính năng khi chưa đo được chất lượng cốt lõi.

## Các điểm cần nhớ khi trả lời

| Có thể khẳng định | Không nên khẳng định |
|---|---|
| Đã triển khai và kiểm thử các luồng lớp, bài tập, phiên bản, chia sẻ, đánh giá và so sánh | Đã chứng minh sinh viên học tốt hơn nếu chưa có nghiên cứu |
| AI có dùng bằng chứng tính toán ở luồng phân tích/đánh giá | Mọi kết luận AI đều đúng chỉ vì code chạy thành công |
| AI so sánh nội dung các phiên bản đã chọn | AI so sánh đã đọc ảnh hoặc kiểm tra lại CSV |
| Backend kiểm tra quyền và điều kiện chia sẻ | Có thể thu hồi mọi bản sao sau khi người dùng đã đọc |
| Giáo viên duyệt đề và quyết định điểm chính thức | AI tự công bố đề hoặc chấm điểm cuối cùng |
| Có dữ liệu và nhận xét mẫu được gắn nhãn để demo | Nhận xét do seed tạo đều là kết quả gọi AI thật |
| Đã dùng sandbox và các kiểm tra bảo mật cụ thể | An toàn tuyệt đối hoặc dữ liệu không bao giờ rời máy |
| 37 tests đã qua ở lần kiểm tra đã ghi nhận | Độ chính xác AI là 100% hoặc tải lớn đã được bảo đảm |

## Tài liệu và mã nguồn để mở khi bị hỏi sâu

- [Luồng nghiệp vụ](LUONG_NGHIEP_VU.md): giao bài, lịch chia sẻ, cải thiện và tham khảo đáp án.
- [Kịch bản demo](DEMO_KHACH_HANG.md): tài khoản và thứ tự trình diễn.
- [API và kiểm tra quyền](backend/app/main.py): phân quyền, bài nộp, chia sẻ và chấm điểm.
- [Worker](backend/app/worker.py): hàng đợi và kết quả tác vụ.
- [Đánh giá AI](backend/app/ai_service.py): kiểm tra trên dataset và giới hạn khi thiếu bằng chứng.
- [Tạo đề AI](backend/app/exam_generation.py): hồ sơ dữ liệu, câu hỏi và đáp án.
- [So sánh bài](backend/app/peer_comparison.py): nguồn được phép xem, phiên bản và đầu ra có cấu trúc.
- [Kiểm thử so sánh](backend/tests/test_peer_comparison.py): quyền, lịch, ngữ cảnh cố định và dữ liệu demo.
- [Cách ly database test](backend/tests/conftest.py): tránh chạy kiểm thử trên dữ liệu ứng dụng.
- [Workflow DA-Agent](../DA-Agent-drive/graph/graph.py): các node và nhánh xử lý.
- [Sandbox Python](../DA-Agent-drive/graph/e2b_executor.py): chạy code trong E2B.

**Thông điệp xuyên suốt khi bảo vệ:** project tổ chức một vòng học tập có thể theo dõi trên dataset dùng chung; AI cung cấp gợi ý và phản hồi, còn sinh viên chịu trách nhiệm lập luận và giáo viên quyết định đánh giá chính thức.
