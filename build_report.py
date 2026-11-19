from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape
import re, os, shutil

ROOT=Path(__file__).parent
TEMPLATE=ROOT/'Mau_bao_cao_84ad12988f.docx'
OUT=ROOT/'Bao_cao_khoa_luan_DataClass.docx'
MEDIA=ROOT/'report_media'; MEDIA.mkdir(exist_ok=True)
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'; R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'; A='http://schemas.openxmlformats.org/drawingml/2006/main'; WP='http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'; PIC='http://schemas.openxmlformats.org/drawingml/2006/picture'; REL='http://schemas.openxmlformats.org/package/2006/relationships'
ET.register_namespace('w',W); ET.register_namespace('r',R); ET.register_namespace('a',A); ET.register_namespace('wp',WP); ET.register_namespace('pic',PIC)
def q(ns,t): return '{%s}%s'%(ns,t)

# diagrams rendered as vector-like clean PNGs
from PIL import Image, ImageDraw, ImageFont
font_path='C:/Windows/Fonts/arial.ttf'
def f(sz,bold=False):
 p='C:/Windows/Fonts/arialbd.ttf' if bold else font_path
 return ImageFont.truetype(p,sz)
def diagram_arch(path):
 im=Image.new('RGB',(1500,790),'white'); d=ImageDraw.Draw(im)
 def box(x,y,w,h,title,txt,color):
  d.rounded_rectangle((x,y,x+w,y+h),18,fill=color,outline='#274060',width=3)
  d.text((x+18,y+14),title,font=f(25,True),fill='#17324d')
  yy=y+55
  for line in txt.split('\n'): d.text((x+18,yy),line,font=f(19),fill='#253746'); yy+=29
 box(35,110,300,195,'Người dùng','Giáo viên\nSinh viên','#e7f1ff')
 box(420,110,390,195,'Frontend','React + TypeScript\nTrang lớp, bài tập, nộp bài\nChia sẻ và đánh giá','#e7f7ef')
 box(900,75,530,250,'Backend API','FastAPI + SQLAlchemy\nPhiên, CSRF, phân quyền\nUpload CSV/XLSX, endpoint REST','#fff1dc')
 box(900,440,530,245,'Tầng dữ liệu','SQLite: người dùng, lớp, bài, phiên bản\nTệp dataset / artifact trong volume\nWorker xử lý hàng đợi AI','#f2eaff')
 box(420,440,390,245,'DA-Agent','LangGraph: lập kế hoạch, công cụ\nDuckDB / phân tích định lượng\nE2B cho Python tùy biến','#e5f6f7')
 for a,b in [((335,205),(420,205)),((810,205),(900,205)),((1165,325),(1165,440)),((900,555),(810,555)),((810,475),(900,285))]:
  d.line((a,b),fill='#304c67',width=5); x1,y1=b; x0,y0=a
  import math
  ang=math.atan2(y1-y0,x1-x0); L=18
  p1=(x1-L*math.cos(ang-.45),y1-L*math.sin(ang-.45)); p2=(x1-L*math.cos(ang+.45),y1-L*math.sin(ang+.45)); d.polygon([b,p1,p2],fill='#304c67')
 d.text((35,25),'Kiến trúc logic tổng thể của DataClass',font=f(32,True),fill='#17324d')
 im.save(path)
def diagram_flow(path):
 im=Image.new('RGB',(1500,620),'white'); d=ImageDraw.Draw(im)
 steps=[('1. Tạo lớp','Giáo viên tạo lớp\nvà mã tham gia'),('2. Giao bài','Dataset + câu hỏi\n+ lịch chia sẻ'),('3. Phân tích','Sinh viên hỏi AI,\nviết insight, chọn chứng cứ'),('4. Nộp bài','Đóng băng phiên bản\nvà tạo tác vụ đánh giá'),('5. Học từ bạn','Mở theo lịch, review\nvà so sánh'),('6. Cải thiện','Sửa bài, ghi phản tư,\nnộp phiên bản mới')]
 xs=[30,275,520,765,1010,1255]
 for i,(title,body) in enumerate(steps):
  x=xs[i]; d.rounded_rectangle((x,190,x+210,390),18,fill=['#e7f1ff','#fff1dc','#e5f6f7','#e7f7ef','#f2eaff','#e9f4de'][i],outline='#274060',width=3)
  d.text((x+12,212),title,font=f(22,True),fill='#17324d')
  for j,line in enumerate(body.split('\n')): d.text((x+12,265+j*31),line,font=f(17),fill='#253746')
  if i<5:
   d.line((x+210,290,xs[i+1]-12,290),fill='#304c67',width=5); d.polygon([(xs[i+1]-12,290),(xs[i+1]-28,279),(xs[i+1]-28,301)],fill='#304c67')
 d.text((30,70),'Luồng học tập có kiểm soát phiên bản',font=f(32,True),fill='#17324d')
 d.text((30,470),'Mốc chia sẻ có thể độc lập với hạn nộp; giáo viên duyệt đề và quyết định điểm chính thức.',font=f(20),fill='#253746')
 im.save(path)
diagram_arch(MEDIA/'architecture.png'); diagram_flow(MEDIA/'workflow.png')

def makeparas(text):
 return [x.strip() for x in text.strip().split('\n') if x.strip()]

chapters=[]
def chapter(title, sections): chapters.append((title,sections))

chapter('CHƯƠNG 1. TỔNG QUAN ĐỀ TÀI',[
('1.1. Bối cảnh và lý do chọn đề tài',[
'''Phân tích dữ liệu ngày càng xuất hiện trong nhiều học phần thuộc kinh tế, quản trị, khoa học máy tính và các ngành ứng dụng. Người học cần biết đặt câu hỏi, làm sạch dữ liệu, lựa chọn phép tổng hợp, trực quan hóa kết quả và diễn giải phát hiện trong bối cảnh. Trong lớp học đông, việc tổ chức bài tập trên cùng một nguồn dữ liệu thường bị chia cắt giữa nhiều công cụ: nơi giao đề, nơi trao đổi, nơi nộp tệp và nơi chấm bài. Sự phân tán làm giảm khả năng theo dõi quá trình học và khiến phản hồi khó gắn với bằng chứng mà sinh viên đã dùng.''',
'''Các công cụ trợ lý tạo sinh có thể giúp người học giải thích thuật ngữ, gợi ý hướng khám phá và tạo biểu đồ. Tuy nhiên, một giao diện hội thoại đơn lẻ không tự giải quyết các yêu cầu về lớp học: ai được xem bài nào, đề đã được duyệt chưa, một lần nộp có được giữ nguyên không, bài của bạn cùng lớp mở vào lúc nào và điểm nào đã được giáo viên công bố. Nếu thiếu cơ chế nghiệp vụ, hỗ trợ AI có thể hữu ích trong chốc lát nhưng khó trở thành một quy trình học tập có thể kiểm tra.''',
'''Đề tài xây dựng DataClass, nền tảng tổ chức hoạt động học phân tích dữ liệu theo lớp và bài tập. Hệ thống kết hợp ứng dụng web, cơ sở dữ liệu quan hệ và DA-Agent phân tích CSV/XLSX. Trọng tâm là kết nối khám phá dữ liệu với câu trả lời có lập luận, lưu bằng chứng được chọn, đóng băng phiên bản bài nộp, hỗ trợ phản hồi từ AI/giáo viên/bạn học và cho phép cải thiện sau khi học từ các bài được chia sẻ.''',
'''Lý do chọn đề tài còn đến từ tính liên ngành của bài toán. Đây không chỉ là xây dựng mô hình AI mà là thiết kế một sản phẩm phần mềm có vai trò người dùng, dữ liệu riêng tư, tác vụ nền, thời gian mở chia sẻ, an toàn tệp tải lên và giới hạn của đầu ra mô hình. Việc triển khai giúp nghiên cứu cách một tác tử phân tích dữ liệu được đặt trong quy trình giáo dục có kiểm soát.''']),
('1.2. Bài toán và mục tiêu nghiên cứu',[
'''Bài toán đặt ra là hỗ trợ giáo viên tổ chức một bài tập phân tích dữ liệu chung cho lớp, đồng thời giúp sinh viên hoàn thành báo cáo theo câu hỏi và có cơ hội học từ phản hồi. Một bài tập gồm mô tả, một hoặc nhiều tệp dữ liệu, bộ câu hỏi, rubric tùy chọn, thời hạn nộp và cấu hình chia sẻ. Sinh viên tương tác với dữ liệu thông qua trợ lý, tự chịu trách nhiệm về kết luận và chọn bằng chứng sẽ đưa vào bài.''',
'''Mục tiêu tổng quát là phân tích, thiết kế và xây dựng một nền tảng web có thể quản lý lớp học và bài tập phân tích dữ liệu; tích hợp trợ lý AI theo luồng công cụ trước; bảo toàn lịch sử nộp bài; cung cấp các cơ chế chia sẻ, đánh giá chéo và cải thiện có kiểm soát; đồng thời áp dụng xác thực, phân quyền và kiểm tra quyền truy cập ở phía máy chủ.''',
'''Các mục tiêu cụ thể gồm: (i) khảo sát nhu cầu và mô hình hóa quy trình giáo viên–sinh viên; (ii) thiết kế kiến trúc React, FastAPI, SQLite/SQLAlchemy, worker và LangGraph; (iii) triển khai đăng nhập, lớp, bài tập, tải dataset, câu hỏi và phiên bản bài nộp; (iv) tích hợp phân tích dữ liệu và đánh giá AI có bằng chứng; (v) triển khai lịch chia sẻ, review đồng đẳng, so sánh bài và nộp bản cải thiện; (vi) kiểm tra các trường hợp chức năng, phân quyền và giới hạn hệ thống; (vii) đề xuất tiêu chí đánh giá thực nghiệm trong lớp học.''']),
('1.3. Đối tượng, phạm vi và phương pháp',[
'''Đối tượng nghiên cứu là quy trình hỗ trợ học phân tích dữ liệu trong phạm vi một lớp học với giáo viên, sinh viên và dịch vụ AI. Hệ thống nhận CSV/XLSX cho bài tập; xử lý câu hỏi ngôn ngữ tự nhiên, tạo bảng/biểu đồ và tổng hợp trả lời. Hai vai trò chính là giáo viên và sinh viên. Mô hình ngôn ngữ là thành phần hỗ trợ, không được coi là người chấm cuối cùng.''',
'''Phạm vi triển khai bao gồm ứng dụng React + TypeScript, API FastAPI, lưu trữ quan hệ SQLite qua SQLAlchemy, hàng đợi AI trong cơ sở dữ liệu với worker đơn máy, và DA-Agent xây dựng bằng LangGraph. Môi trường chạy có thể dùng Docker Compose. Các nhà cung cấp mô hình và E2B phụ thuộc cấu hình khóa dịch vụ. Hệ thống hiện không chứng minh hiệu quả học tập trong nghiên cứu đối chứng; cũng không phải hệ thống phát hiện đạo văn, LMS tổng quát, nền tảng cộng tác thời gian thực hay dịch vụ chịu tải quy mô lớn.''',
'''Phương pháp thực hiện gồm khảo sát mã nguồn và yêu cầu nghiệp vụ hiện có, phân tích ca sử dụng, thiết kế dữ liệu, xây dựng theo từng lớp chức năng, tích hợp tác tử, kiểm tra tự động và rà soát luồng trình diễn. Phần đánh giá trong báo cáo phân biệt kiểm thử phần mềm với đánh giá chất lượng sư phạm. Các số liệu hiệu quả học tập, độ chính xác AI, tải đồng thời và thời gian phản hồi phải được thu thập bằng kế hoạch thực nghiệm riêng; không suy diễn từ việc tính năng hoạt động.''']),
('1.4. Đóng góp và cấu trúc báo cáo',[
'''Đóng góp kỹ thuật của đề tài là một quy trình liền mạch từ giao dữ liệu đến cải thiện bài: lớp và bài tập; trợ lý dựa trên dataset; câu trả lời có chứng cứ; phiên bản nộp bất biến; chia sẻ theo thời gian/chế độ; review đồng đẳng; đánh giá của AI và giáo viên; so sánh các báo cáo; và nộp bản cải thiện. Hệ thống cũng giới hạn thông tin riêng tư theo vai trò và trạng thái công bố.''',
'''Báo cáo gồm sáu chương. Chương 1 giới thiệu bài toán và phạm vi. Chương 2 trình bày cơ sở lý thuyết và công nghệ. Chương 3 phân tích yêu cầu, tác nhân và nghiệp vụ. Chương 4 thiết kế kiến trúc, dữ liệu, bảo mật và giao diện. Chương 5 trình bày triển khai, kiểm thử và đánh giá. Chương 6 kết luận, nêu hạn chế và hướng phát triển. Phụ lục cung cấp hướng dẫn vận hành, kịch bản kiểm tra và danh mục thông tin cần hoàn thiện.'''])])

chapter('CHƯƠNG 2. CƠ SỞ LÝ THUYẾT VÀ CÔNG NGHỆ',[
('2.1. Học tập dựa trên dữ liệu và phản hồi',[
'''Một hoạt động phân tích dữ liệu có thể xem là chuỗi gồm xác định câu hỏi, hiểu cấu trúc dữ liệu, kiểm tra chất lượng, lựa chọn phép phân tích, biểu diễn kết quả, giải thích ý nghĩa và nêu giới hạn. Sản phẩm cuối cùng không chỉ là con số hay biểu đồ: lập luận cần chỉ ra dữ liệu nào hỗ trợ kết luận, phương pháp đã dùng và điều gì chưa thể suy ra.''',
'''Phản hồi định dạng tốt giúp người học biết điểm mạnh, khoảng trống và bước sửa tiếp theo. Trong DataClass, phản hồi được phân thành ba nguồn có vai trò khác nhau. AI gợi ý kiểm tra và phát hiện thiếu sót; bạn học đưa góc nhìn và kinh nghiệm; giáo viên đưa nhận xét chuyên môn và quyết định điểm chính thức. Tách vai trò giảm nguy cơ người học hiểu một nhận xét tự động là phán quyết cuối cùng.''',
'''Đánh giá đồng đẳng có thể thúc đẩy người học đọc lập luận của người khác và tự điều chỉnh, nhưng cần cấu trúc để phản hồi cụ thể, tôn trọng và gắn với tiêu chí. Hệ thống cung cấp mức đánh giá, điểm mạnh, gợi ý cải thiện và điều học được. Bản đánh giá gắn với một phiên bản cụ thể, tránh việc sửa bài làm thay đổi ngữ cảnh của phản hồi cũ. Việc học có thực sự cải thiện cần nghiên cứu với rubric và nhóm so sánh; tính năng phần mềm tự thân không chứng minh hiệu quả sư phạm.''']),
('2.2. Trợ lý AI phân tích dữ liệu',[
'''DA-Agent sử dụng workflow dạng đồ thị để chia nhiệm vụ thành các bước. Luồng mức cao gồm trích xuất schema, phân loại câu hỏi, lập kế hoạch, chọn hành động, thực thi công cụ hoặc viết mã tùy biến trong sandbox, tổng hợp, kiểm chứng và dọn dẹp. Các câu hỏi trao đổi khái niệm có thể đi theo nhánh chat; câu hỏi yêu cầu tính toán đi qua lập kế hoạch và thực thi.''',
'''Cách tiếp cận tool-first ưu tiên thao tác xác định trước khi sinh mã tùy ý. Các phép khám phá thường gặp, truy vấn DuckDB, tổng hợp và biểu đồ tĩnh được thực hiện bằng công cụ có giao diện được định nghĩa. Khi công cụ chuẩn không đủ, tác tử có thể tạo Python và chạy trong E2B thay vì chạy mã do mô hình sinh trên máy chủ ứng dụng. Sandbox có thể tắt truy cập Internet theo cấu hình và được đóng sau yêu cầu.''',
'''Đầu ra AI có thể sai do hiểu nhầm câu hỏi, thiếu dữ liệu, lỗi kiểu dữ liệu, chọn phép tổng hợp không phù hợp hoặc diễn giải quá mức. Do đó, hệ thống cần cung cấp kiểm tra kết quả, giữ dấu vết artifact và khuyến khích người học đối chiếu giá trị. Ở luồng so sánh bài, AI đọc báo cáo đã chọn nhưng không chạy lại dataset; kết quả so sánh là phản hồi học tập, không phải kiểm chứng độc lập hay chấm điểm.''']),
('2.3. Công nghệ xây dựng hệ thống',[
'''React và TypeScript được sử dụng để xây dựng giao diện phía trình duyệt. React tổ chức giao diện thành các thành phần và trang theo trạng thái; TypeScript hỗ trợ phát hiện một số sai khác kiểu trong quá trình phát triển. Các trang hiện diện trong dự án gồm đăng nhập, dashboard, danh sách lớp, chi tiết lớp, tạo bài tập, trang làm bài và gallery bài chia sẻ.''',
'''FastAPI cung cấp API HTTP và tích hợp kiểu dữ liệu cho request/response. SQLAlchemy ánh xạ các thực thể nghiệp vụ sang cơ sở dữ liệu quan hệ; Alembic quản lý thay đổi schema. SQLite thuận tiện cho phát triển và triển khai một máy, nhưng không tự động cung cấp thông lượng hoặc điều phối đa worker như một cụm cơ sở dữ liệu chuyên dụng.''',
'''LangGraph biểu diễn quy trình tác tử thành đồ thị có node và cạnh điều kiện. pandas hỗ trợ đọc và mô tả bảng dữ liệu; DuckDB hỗ trợ truy vấn phân tích; E2B cung cấp môi trường cô lập cho mã Python được tạo khi cần. Tác vụ AI được ghi trong bảng hàng đợi, worker cập nhật trạng thái queued, running, done hoặc failed. Khi cần mở rộng, hàng đợi cơ sở dữ liệu đơn máy có thể được thay bằng dịch vụ chuyên biệt sau khi đo tải và yêu cầu phục hồi.''',
'''Docker Compose gom frontend/API/worker và cấu hình vận hành trong môi trường phát triển hoặc demo. Khóa mô hình và sandbox đặt ở biến môi trường; khóa bí mật phiên cần thay trước khi triển khai sản xuất. Tệp dataset và artifact được lưu trong volume cục bộ, vì vậy sao lưu và quyền truy cập filesystem là một phần của vận hành.''']),
('2.4. Nguyên tắc thiết kế liên quan',[
'''Nguyên tắc tối thiểu quyền yêu cầu mỗi yêu cầu API kiểm tra danh tính, vai trò, quan hệ với lớp và trạng thái công bố của tài nguyên. Việc ẩn nút trên giao diện không đủ để bảo vệ dữ liệu. Nguyên tắc bảo toàn phiên bản yêu cầu mỗi lần nộp tạo snapshot riêng của nội dung và câu trả lời; phiên bản mới không ghi đè lịch sử.''',
'''Nguyên tắc riêng tư theo thiết kế áp dụng cho đáp án nội bộ, bản nháp, bài chia sẻ tự nguyện và artifact. Luồng trợ lý, so sánh và chấm điểm có ngữ cảnh khác nhau; không đưa đáp án ẩn vào so sánh đồng đẳng. Các tệp tải lên cần giới hạn đuôi, dung lượng và thư mục lưu; đường dẫn phải được chuẩn hóa và kiểm tra nằm trong vùng cho phép.''',
'''Nguyên tắc AI có giám sát giữ giáo viên làm chủ việc duyệt đề và công bố điểm. Mọi đầu ra tự động cần được diễn đạt như hỗ trợ, có thể xem lại và không thay thế phán đoán của con người. Đối với kết luận số, hệ thống cần phân biệt số đã tính trên dữ liệu với phần diễn giải ngôn ngữ.'''])])

chapter('CHƯƠNG 3. PHÂN TÍCH YÊU CẦU VÀ NGHIỆP VỤ',[
('3.1. Tác nhân và nhu cầu',[
'''Giáo viên tạo lớp, công bố mã tham gia, xây dựng bài tập, tải dataset, cấu hình câu hỏi và lịch. Giáo viên có thể thiết lập rubric hoặc đáp án chấm nội bộ, yêu cầu AI hỗ trợ tạo đề, duyệt nội dung trước khi công bố, theo dõi bài nộp, đưa điểm và công bố kết quả. Chỉ giáo viên sở hữu lớp được thực hiện các thao tác quản trị lớp.''',
'''Sinh viên tham gia lớp bằng mã, xem bài đã công bố, khám phá dữ liệu, trò chuyện với trợ lý theo câu hỏi, soạn câu trả lời, chọn artifact làm bằng chứng, lưu nháp và nộp bài. Khi đến thời điểm mở chia sẻ, sinh viên có thể xem các bài được phép xem, đánh giá đồng đẳng, so sánh bài và nộp phiên bản cải thiện nếu được bật.''',
'''Worker là tác nhân kỹ thuật chạy nền, không phải người dùng tương tác. Nó lấy tác vụ đã xếp hàng, tải ngữ cảnh được cho phép, gọi dịch vụ AI/phân tích và lưu kết quả. Quản trị viên vận hành cấu hình biến môi trường, cơ sở dữ liệu, volume và sao lưu. Nhà cung cấp mô hình là dịch vụ bên ngoài có thể nhận nội dung được gửi để xử lý.''']),
('3.2. Yêu cầu chức năng',[
'''Nhóm quản lý danh tính và lớp gồm đăng nhập, phiên người dùng, tạo lớp, tham gia bằng mã và kiểm tra vai trò. Nhóm quản lý bài gồm tạo bài ở trạng thái nháp, tải CSV/XLSX, thêm từ 1 đến 20 câu hỏi, điểm tối đa, rubric, đáp án riêng, hạn nộp, thời điểm mở chia sẻ và chế độ chia sẻ. Bài đã công bố không cho sửa bộ câu hỏi nhằm bảo toàn tính nhất quán.''',
'''Nhóm làm bài gồm hiển thị dataset và câu hỏi, hội thoại trợ lý, hiển thị bảng/biểu đồ, lưu câu trả lời Markdown và lựa chọn artifact. Sinh viên có thể sửa bản nháp trước khi nộp. Khi nộp, hệ thống tạo phiên bản đóng băng và tác vụ đánh giá AI cho chính phiên bản đó. Trạng thái công việc cho phép theo dõi tác vụ nền.''',
'''Nhóm phản hồi gồm đánh giá AI theo câu hỏi, nhận xét giáo viên, công bố điểm theo phiên bản, review đồng đẳng, bình luận thảo luận và so sánh tối đa ba bài khác. Các bài trong chế độ tự nguyện chỉ được đưa vào ngữ cảnh nếu chủ bài bật chia sẻ. Khi bản cải thiện được nộp, hệ thống giữ phiên bản ban đầu, điểm và review cũ.''',
'''Nhóm quản trị dữ liệu gồm tải artifact qua endpoint có kiểm tra quyền; giới hạn loại và kích thước tệp; phục hồi tác vụ còn dang dở khi worker khởi động; và quản lý schema bằng migration. Dữ liệu demo được gắn nhãn riêng để không nhầm với kết quả phân tích thực tế.''']),
('3.3. Yêu cầu phi chức năng',[
'''Bảo mật: xác thực người dùng, kiểm tra quyền truy cập ở API, bảo vệ CSRF, hash mật khẩu bằng PBKDF2, giới hạn upload, kiểm soát đường dẫn và không đặt bí mật trong mã nguồn. Tính riêng tư: đáp án, bản nháp, điểm chưa công bố và bài không chia sẻ không lộ cho bạn học. Tính toàn vẹn: mỗi phiên bản lưu snapshot và gắn mốc thời gian.''',
'''Tính dễ sử dụng: giao diện phải làm rõ trạng thái bài, hạn nộp, thời điểm mở chia sẻ, trạng thái AI và phân biệt phản hồi với điểm chính thức. Tính bảo trì: phân tách frontend, API, worker và graph; migration có thể xem xét; cấu hình môi trường tách khỏi mã. Tính khả chuyển: triển khai demo qua Docker Compose và có hướng dẫn thiết lập phụ thuộc.''',
'''Hiệu năng và khả năng mở rộng chưa được xác nhận bằng benchmark tải trong tài liệu dự án. Worker đơn máy phù hợp luồng demo/nhóm nhỏ nhưng có thể tạo nút thắt khi nhiều tác vụ dài cùng chờ. Mục tiêu đáp ứng cụ thể, số người dùng đồng thời và SLO cần được xác định trước khi triển khai lớp thực tế.''']),
('3.4. Quy trình nghiệp vụ',[
'''Quy trình bắt đầu khi giáo viên tạo lớp và công bố mã. Giáo viên tạo bài nháp, cung cấp dataset, thiết kế câu hỏi và cấu hình thời điểm. Nếu sử dụng AI tạo đề, hệ thống tạo gợi ý và phân tích; giáo viên xem, chỉnh sửa và duyệt trước khi công bố. Bài được công bố trở thành đề chung, giúp mọi sinh viên làm trên cùng nguồn dữ liệu và bộ câu hỏi.''',
'''Sinh viên chọn câu hỏi, đặt yêu cầu cho trợ lý, xem kết quả và tự viết câu trả lời. Người học có thể đưa bảng hoặc biểu đồ phù hợp vào phần chứng cứ. Bản nháp chỉ hiển thị cho chính sinh viên và giáo viên lớp. Khi nộp, một phiên bản cố định được tạo, đồng thời tác vụ đánh giá được xếp hàng. Mốc hạn nộp và mốc mở xem bài được tách riêng để tránh lộ bài quá sớm.''',
'''Sau giờ mở chia sẻ, người dùng được phép truy cập các phiên bản theo cấu hình. Sinh viên có thể chọn bài để review hoặc yêu cầu AI so sánh. Giáo viên đánh giá và công bố điểm. Nếu bài cho phép cải thiện, sinh viên ghi điều học được và thay đổi đã làm rồi nộp bản mới. Mỗi phiên bản có lịch sử riêng; review cũ vẫn gắn với phiên bản cũ.''']),
('3.5. Quy tắc nghiệp vụ và tiêu chí chấp nhận',[
'''Một người dùng chỉ có một membership cho một lớp; một sinh viên chỉ có một submission gốc cho mỗi bài tập; mỗi submission có thể có nhiều phiên bản với số thứ tự duy nhất. Mỗi câu hỏi trong một bài có thứ tự duy nhất. Một sinh viên chỉ có một review cho một phiên bản và có thể chỉnh sửa review của mình. Một phiên bản so sánh phải thuộc đúng bài tập và quyền truy cập phải còn hợp lệ tại thời điểm truy xuất.''',
'''Hệ thống chấp nhận bài tập khi giáo viên có quyền sở hữu lớp, định dạng dữ liệu được hỗ trợ, giới hạn dung lượng không bị vượt, cấu hình thời gian hợp lệ và ít nhất một câu hỏi đã được thiết lập. Bài chỉ có thể xem theo trạng thái công bố. Sinh viên không thể xem đáp án chấm nội bộ. Artifact chỉ được trả về sau khi backend xác nhận tài nguyên thuộc phạm vi quyền được phép.''',
'''Tiêu chí chấp nhận ở cấp sản phẩm gồm: hoàn thành được luồng giáo viên giao bài; sinh viên tham gia, phân tích, nộp; phiên bản đầu không bị thay đổi khi cải thiện; thời điểm chia sẻ và chế độ chia sẻ được tuân thủ; AI job có trạng thái và lỗi rõ ràng; và người không có quyền nhận từ chối ở API kể cả khi gọi endpoint trực tiếp.'''])])

chapter('CHƯƠNG 4. THIẾT KẾ HỆ THỐNG',[
('4.1. Kiến trúc tổng thể',[
'''Kiến trúc phân thành bốn lớp. Lớp giao diện là React/TypeScript trong trình duyệt. Lớp API là FastAPI xử lý xác thực, nghiệp vụ, phân quyền và tạo việc nền. Lớp dữ liệu gồm SQLite, các thư mục upload/artifact và migration. Lớp phân tích gồm worker, dịch vụ AI và đồ thị DA-Agent; khi cần mã Python tùy biến, graph có thể dùng sandbox E2B.''',
'''Giao diện gửi request HTTPS/HTTP tới API; API đọc/ghi cơ sở dữ liệu và tạo AIJob. Worker lấy job, dựng ngữ cảnh được phép, gọi chức năng tương ứng rồi lưu kết quả và artifact. Giao diện truy vấn trạng thái job để hiển thị tiến độ. Tệp không được nhúng trực tiếp vào đường dẫn công khai; endpoint asset kiểm tra người dùng trước khi trả tệp.''',
'''Mô hình hiện tại hướng tới triển khai một máy. Docker Compose hỗ trợ gom dịch vụ, nhưng không đồng nghĩa hệ thống đã có HA, cân bằng tải hay vận hành đa vùng. Nếu cần mở rộng, cần tách kho tệp, chuyển cơ sở dữ liệu, bổ sung hàng đợi chuyên biệt và quan sát worker theo yêu cầu thực tế.''']),
('4.2. Thiết kế thành phần',[
'''Frontend nhóm chức năng theo trang: đăng nhập, dashboard, lớp, chi tiết lớp, tạo bài, làm bài và bài chia sẻ. Các thành phần dịch vụ giao tiếp API. Giao diện cần phản ánh rõ trạng thái nháp/công bố, thời gian, lựa chọn chia sẻ và tình trạng các tác vụ AI. Các kết quả Markdown có thể chứa bảng và công thức; nội dung hiển thị phải được xử lý an toàn.''',
'''Backend main.py tập trung các tuyến API và kiểm tra quyền. models.py mô tả thực thể SQLAlchemy. security.py quản lý hash/xác minh mật khẩu. ai_service.py điều phối graph và các tác vụ đánh giá; exam_generation.py tạo đề; peer_comparison.py kiểm soát nguồn cho phép và xây ngữ cảnh so sánh; worker.py thực thi các job. Tách module giúp các quy tắc như quyền chia sẻ có thể được kiểm tra ở một nơi.''',
'''DA-Agent graph.py khai báo StateGraph, node và cạnh điều kiện. Các node trích xuất schema, lập kế hoạch, chọn công cụ, thực thi, tạo câu trả lời tổng hợp, kiểm chứng và dọn dẹp. Công cụ chuẩn được ưu tiên; nhánh coder/execution dùng cho tình huống cần Python. Kết quả public của graph là final_answer; artifact cần ánh xạ sang endpoint backend trước khi hiện với người dùng từ xa.''']),
('4.3. Thiết kế dữ liệu',[
'''Mô hình dữ liệu xoay quanh User, Classroom, Membership, Assignment, AssignmentQuestion, Submission và SubmissionVersion. User có vai trò giáo viên/sinh viên. Classroom thuộc một giáo viên; Membership liên kết người dùng với lớp. Assignment thuộc lớp, lưu cấu hình thời gian, trạng thái, dataset, rubric, đáp án và chế độ chia sẻ. AssignmentQuestion lưu nội dung, thứ tự và điểm tối đa.''',
'''Submission đại diện quan hệ giữa sinh viên và bài tập, giữ bản nháp hiện tại và cấu hình chia sẻ. SubmissionAnswer lưu nội dung theo câu hỏi và danh sách artifact được chọn. SubmissionVersion là bản snapshot khi nộp, gồm nội dung Markdown, ảnh chụp câu trả lời, thời gian, trạng thái cải thiện, phản tư, review và điểm. Ràng buộc duy nhất bảo vệ thứ tự phiên bản và ngăn trùng submission/review theo người.''',
'''AIJob lưu chủ sở hữu, bài tập, submission/phiên bản/câu hỏi liên quan, loại job, trạng thái, prompt, kết quả và lỗi. Artifact liên kết job với đường dẫn tệp và kiểu nội dung. PeerReview lưu mức đánh giá, điểm tốt, góp ý và điều học được. Comment phục vụ thảo luận; SubmissionVote là biểu quyết đơn giản. Thiết kế lưu điểm ở phiên bản để tránh kết quả mới ghi đè lịch sử.''',
'''Tệp dataset được tham chiếu trong dataset_json và lưu dưới thư mục upload; artifact nằm trong vùng riêng. Trước khi worker đọc, đường dẫn được resolve và kiểm tra nằm bên trong upload directory. Cơ sở dữ liệu lưu metadata và nội dung nghiệp vụ; sao lưu cần bao gồm cả database lẫn volume tệp để tránh mất liên kết.''']),
('4.4. Luồng xử lý AI và hàng đợi',[
'''Khi có yêu cầu phân tích hoặc chấm, API xác thực người dùng và quyền trên bài, sau đó tạo AIJob trạng thái queued. Worker claim job bằng cập nhật có điều kiện sang running để tránh hai lần lấy cùng một job ở luồng thông thường. Job được thực thi theo loại: chat/gợi ý, tạo đề, review nháp/bài nộp hoặc so sánh. Kết quả được lưu dưới dạng JSON và trạng thái chuyển done; lỗi được ghi lại và chuyển failed.''',
'''Worker xử lý job nền giúp request của trình duyệt không phải chờ tác vụ AI dài. Tuy nhiên worker đơn là thành phần giới hạn thông lượng. Cơ chế phục hồi job chạy quá hạn khi khởi động giúp giảm nguy cơ job mắc kẹt, nhưng cần kiểm tra retry, tính lặp an toàn và xử lý job gọi dịch vụ đã thành công nhưng lưu kết quả thất bại. Đây là rủi ro vận hành cần đo và cải thiện.''',
'''So sánh bài sử dụng ngữ cảnh các phiên bản được chọn, kiểm tra bài cùng lớp, mốc chia sẻ, chế độ công khai/tự nguyện và số lượng nguồn. Tác vụ không chạy lại DA-Agent và không đọc lại CSV. Kết quả gắn với ID phiên bản; khi quyền chia sẻ thay đổi, API đánh giá lại quyền truy xuất kết quả đã lưu.''']),
('4.5. Thiết kế bảo mật và quyền riêng tư',[
'''Phiên đăng nhập được ký bằng secret key; cấu hình sản xuất yêu cầu khóa khác mặc định và cookie secure. Request thay đổi dữ liệu cần CSRF token. Mật khẩu được băm PBKDF2-HMAC-SHA256 với salt riêng và số vòng lặp cấu hình trong mã hiện tại. So sánh hash dùng phép so sánh chống timing cơ bản.''',
'''Phân quyền được kiểm tra theo lớp, bài, submission, phiên bản và artifact. Giáo viên chỉ quản trị lớp mình; sinh viên cần là thành viên; người xem bài bạn phải qua thời điểm mở và quy tắc share_mode. Đáp án chấm nội bộ và bài nháp không đưa vào giao diện chia sẻ. Đường dẫn upload kiểm soát resolve và đuôi tệp, kích thước, tránh path traversal. Markdown loại bỏ HTML thô theo tài liệu nghiệp vụ; nội dung công thức cần cấu hình renderer phù hợp.''',
'''Có giới hạn đáng lưu ý: một phần nội dung được gửi tới nhà cung cấp mô hình; tệp có thể được tải lên E2B khi cần chạy Python tùy biến. Vì vậy không thể khẳng định dữ liệu luôn nằm trong máy chủ cục bộ. Trước khi sử dụng dữ liệu thật cần xác định căn cứ xử lý, thông báo cho người học, loại bỏ dữ liệu nhạy cảm, cấu hình lưu trữ và xem xét điều khoản dịch vụ bên ngoài.''']),
('4.6. Thiết kế giao diện và khả năng sử dụng',[
'''Luồng giao diện nên làm rõ vị trí hiện tại: lớp, bài, câu hỏi và phiên bản. Trang tạo bài cần giúp giáo viên kiểm tra file, câu hỏi, rubric, đáp án nội bộ và lịch trước khi công bố. Màn hình tạo đề AI mặc định cho phép giáo viên duyệt và sửa từng câu; chỉ thao tác lưu đã duyệt mới ghi bộ câu hỏi chính thức.''',
'''Trang làm bài cần phân biệt kết quả khám phá của trợ lý với câu trả lời do sinh viên viết. Người học xem tên artifact và chọn bằng chứng gắn với từng câu. Nút nộp cần xác nhận trạng thái, vì thao tác tạo snapshot có ý nghĩa khác lưu nháp. Sau nộp, trang hiển thị tình trạng AI job nhưng không biến nhận xét AI thành điểm đã công bố.''',
'''Trang chia sẻ cần nêu rõ ai được phép xem và thời điểm mở. Nhận xét đồng đẳng nên dùng nhãn hướng dẫn cụ thể thay vì hộp bình luận chung. Chức năng AI so sánh cần liệt kê bài/phiên bản đang chọn và nhắc rằng nội dung không được kiểm tra lại trên CSV. Khả năng truy cập bàn phím, tương phản màu và bố cục màn hình nhỏ cần được đưa vào đánh giá giao diện.'''])])

chapter('CHƯƠNG 5. TRIỂN KHAI, KIỂM THỬ VÀ ĐÁNH GIÁ',[
('5.1. Môi trường và cấu hình triển khai',[
'''Ứng dụng có thể chạy trong cấu trúc dự án hiện tại: web-02 chứa frontend, backend FastAPI và hướng dẫn Docker Compose; DA-Agent-drive chứa graph phân tích. Backend yêu cầu Python 3.12 theo tài liệu cài đặt, frontend dựa trên React/TypeScript và công cụ Node tương ứng. Các phiên bản phụ thuộc chính được khai báo trong requirements.txt và lock/config của frontend.''',
'''Quy trình phát triển gồm cài dependency backend/graph, khởi tạo migration Alembic, tạo giáo viên đầu tiên, chạy API, worker và frontend. Với Docker, cần sao chép env.example sang .env, thiết lập WEB02_SECRET_KEY, nhà cung cấp mô hình và khóa tương ứng, sau đó build và chạy dịch vụ. E2B chỉ được gọi khi graph cần chạy Python tùy biến.''',
'''Dữ liệu runtime nằm trong web-02/var hoặc Docker volume. SQLite, upload và artifacts cần được sao lưu đồng bộ. Khi triển khai HTTPS, đặt reverse proxy/TLS phía trước, cấu hình production và cookie secure, thay khóa mặc định. Không đưa .env, token demo hay khóa dịch vụ vào báo cáo công khai hoặc kho mã.''']),
('5.2. Các chức năng đã triển khai',[
'''Theo tài liệu và mã nguồn dự án, hệ thống hỗ trợ tạo lớp và bài, dataset chung, từ 1 đến 20 câu hỏi, hạn nộp, lịch mở chia sẻ và chế độ chia sẻ. Sinh viên tương tác với trợ lý theo câu hỏi, viết câu trả lời, chọn chứng cứ, lưu nháp và nộp bài. Phiên bản đầu được lưu cố định; bản cải thiện có thể được nộp khi giáo viên cho phép.''',
'''Hệ thống có chức năng AI tạo đề và đáp án gợi ý từ dataset, nhưng giáo viên phải duyệt trước khi áp dụng. AI đánh giá bài theo câu hỏi và đưa trạng thái/gợi ý; điểm giáo viên được lưu riêng và phải được công bố. Sinh viên có thể đánh giá chéo và so sánh bài được phép xem. AI so sánh báo cáo theo nội dung đã nộp, không thực thi lại phân tích trên file dữ liệu.''',
'''Hạ tầng xử lý gồm hàng đợi AIJob với trạng thái, worker và bảng Artifact. API cung cấp kiểm soát quyền theo vai trò/lớp/bài; endpoint tài sản xác thực quyền trước khi trả file. Mã nguồn có các kiểm thử backend chuyên cho quy tắc nghiệp vụ, quyền, phiên bản và seed demo.''']),
('5.3. Chiến lược kiểm thử',[
'''Kiểm thử đơn vị nên tập trung vào hàm không phụ thuộc hạ tầng: kiểm tra hash mật khẩu, parse thời gian, xác thực cấu hình, quy tắc chọn phiên bản và chuyển đổi trạng thái. Kiểm thử tích hợp dùng database riêng để xác minh API và mô hình quan hệ. Không chạy kiểm thử trên database chứa dữ liệu demo/ứng dụng.''',
'''Kiểm thử chức năng theo luồng gồm giáo viên tạo lớp, tạo bài và công bố; sinh viên tham gia, hỏi trợ lý và nộp; mở chia sẻ đúng thời điểm; review/so sánh; giáo viên công bố điểm; sinh viên nộp bản cải thiện. Mỗi bước cần xác minh dữ liệu cơ sở và hiển thị giao diện. Kiểm thử âm tính cần thử người ngoài lớp, xem trước giờ, lấy đáp án ẩn, tải artifact của người khác và truy cập phiên bản đã thu hồi chia sẻ.''',
'''Kiểm thử tệp cần bao gồm loại được phép, tệp giả mạo đuôi, kích thước vượt mức, CSV lỗi encoding/cột rỗng, XLSX nhiều sheet, đường dẫn tương đối và lỗi thiếu file. Kiểm thử worker bao gồm job thành công, thất bại, mất kết nối dịch vụ, worker khởi động lại và artifact không hợp lệ. Kiểm thử giao diện bao gồm độ rộng màn hình, trạng thái tải/lỗi và khả năng điều hướng bàn phím.''']),
('5.4. Kết quả kiểm thử phần mềm',[
'''Tài liệu bảo vệ của dự án ghi nhận 37 kiểm thử backend đã qua tại một lần kiểm tra trong quá trình phát triển. Các nhóm được nhắc đến gồm câu hỏi/đáp án, chia sẻ và cải thiện, tạo đề AI, so sánh bài, bảo vệ dữ liệu và seed demo. Tài liệu cũng đề cập build frontend và thử luồng trình duyệt ở nhiều độ rộng màn hình. Đây là thông tin dự án ghi nhận; báo cáo này không tự chạy lại các kiểm thử.''',
'''Con số 37 phản ánh số trường hợp kiểm thử đã chạy trong một lần ghi nhận, không phải tỷ lệ độ phủ mã, không chứng minh hệ thống không còn lỗi và không đo độ chính xác AI. Kết quả cụ thể theo test case, môi trường, commit và thời điểm cần được nhóm trích xuất từ log CI/terminal để bổ sung vào bản nộp cuối. Nếu nhóm đã chạy lại sau lần ghi nhận, cần cập nhật đúng phiên bản và tổng số.''',
'''Về mặt hành vi, tài liệu dự án ghi nhận các quy tắc xem bài sớm, truy cập bài người khác, thu hồi chia sẻ và bảo toàn phiên bản được kiểm thử. Các kiểm thử đó cung cấp bằng chứng cho những trường hợp đã xét, nhưng không bao phủ mọi tổ hợp quyền, mọi cấu hình triển khai hoặc cuộc tấn công thực tế.''']),
('5.5. Đánh giá AI và hiệu quả học tập',[
'''Chưa có căn cứ trong tài liệu dự án để công bố một tỷ lệ chính xác tổng quát của AI hoặc kết luận sinh viên học tốt hơn. Để đánh giá AI, cần tạo bộ bài chuẩn có nhãn chuyên gia: kết luận đúng, sai số liệu, thiếu chứng cứ, diễn giải vượt dữ liệu và trường hợp không đủ thông tin. So sánh nhận xét AI với đánh giá độc lập, đo precision/recall theo loại lỗi, độ đồng thuận với người chấm và tỷ lệ góp ý hữu ích.''',
'''Để đánh giá hiệu quả học tập, cần nghiên cứu trước–sau hoặc thiết kế nhóm so sánh, sử dụng rubric thống nhất và người chấm không biết nhóm nếu khả thi. Chỉ số có thể gồm chất lượng câu hỏi phân tích, độ chính xác phép tính, liên kết giữa chứng cứ và kết luận, khả năng nêu giới hạn, điểm rubric, thời gian hoàn thành và phản hồi cảm nhận. Cần xác định cỡ mẫu, cách chọn lớp, đồng thuận tham gia, xử lý dữ liệu cá nhân và kế hoạch phân tích trước khi thu thập.''',
'''Đối với so sánh bài, đo tính hữu ích bằng khảo sát người dùng và đánh giá chuyên gia xem nhận xét có trích đúng điểm khác biệt, có tránh kết luận thiếu căn cứ và có đề xuất hành động cụ thể không. Kết quả so sánh không thay thế đánh giá trên dataset; nếu hai bài nêu số liệu khác nhau, nên gợi ý kiểm tra lại phép tính.''']),
('5.6. Phân tích hạn chế và rủi ro',[
'''Rủi ro AI gồm ảo giác, suy luận vượt dữ liệu, lỗi khi dữ liệu bẩn, biến động theo mô hình/nhà cung cấp, chi phí và độ trễ. Đầu ra cần được xem xét, đặc biệt số liệu và nhận định quan trọng. Tác tử tool-first và bước validation giảm một phần lỗi nhưng không đảm bảo mọi câu trả lời đúng.''',
'''Rủi ro dữ liệu gồm lộ thông tin qua nhà cung cấp mô hình hoặc sandbox, quản lý khóa không an toàn, file độc hại, truy cập chéo lớp và sao lưu thiếu. Cần giới hạn dữ liệu nhạy cảm, kiểm soát quyền, ghi nhận thời gian lưu và xây chính sách xóa. Một nền tảng học tập cũng cần quy định cách dùng AI, minh bạch nguồn hỗ trợ và đánh giá độc lập.''',
'''Rủi ro vận hành gồm SQLite/worker đơn máy, hàng đợi bị nghẽn, job kéo dài, mất tiến trình, volume đầy và dữ liệu backup không nhất quán. Cần giám sát độ trễ, số job queued/failed, dung lượng disk, lỗi nhà cung cấp, thời gian phản hồi và tỷ lệ retry. Trước khi mở rộng người dùng cần tải thử theo mô hình sử dụng dự kiến.''',
'''Giới hạn chức năng gồm so sánh bài không chạy lại CSV và không đọc ảnh biểu đồ; hệ thống không phát hiện đạo văn; chia sẻ không thể thu hồi nội dung người dùng đã xem hoặc sao chép; chưa có bằng chứng thực nghiệm về hiệu quả học tập; và chưa có benchmark tải thể hiện quy mô triển khai. Những giới hạn này cần được truyền đạt cho người dùng và hội đồng.''']),
('5.7. Kịch bản trình diễn nghiệm thu',[
'''Kịch bản trình diễn nên dùng dữ liệu mẫu không nhạy cảm. Giáo viên đăng nhập, tạo lớp, thêm bài tập với CSV/XLSX, câu hỏi và lịch mở chia sẻ. Nếu trình diễn sinh đề AI, giáo viên kiểm tra kết quả, chỉnh câu hỏi và lưu phiên bản đã duyệt. Giáo viên công bố bài và sinh viên tham gia lớp bằng mã.''',
'''Sinh viên chọn câu hỏi, yêu cầu trợ lý phân tích một cột hoặc so sánh nhóm, kiểm tra bảng/biểu đồ và tự viết kết luận kèm giới hạn. Sinh viên chọn artifact làm bằng chứng rồi nộp bài. Trình diễn trạng thái queued/running/done, kết quả đánh giá và việc phiên bản được khóa. Trước giờ chia sẻ, thử mở bài người khác để chứng minh API từ chối.''',
'''Sau thời điểm mở, bật xem bài và thực hiện một review có cấu trúc. Chọn các phiên bản được phép để yêu cầu so sánh; nhấn mạnh đây là nhận xét trên báo cáo, không tính lại dữ liệu. Giáo viên nhập điểm, công bố nhận xét; sinh viên ghi điều học được, sửa bài và nộp bản cải thiện. Cuối cùng đối chiếu lịch sử để thấy phiên bản đầu và các đánh giá cũ còn nguyên.'''])])

chapter('CHƯƠNG 6. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN',[
('6.1. Kết luận',[
'''Đề tài đã xây dựng DataClass như một nền tảng hỗ trợ học phân tích dữ liệu theo lớp. Điểm trọng tâm là kết nối trợ lý phân tích với tiến trình học có bài tập, câu trả lời, chứng cứ, phiên bản, chia sẻ và phản hồi. Giáo viên có thể kiểm soát đề và điểm; sinh viên có không gian thực hành, nhận phản hồi và cải thiện bài. Hệ thống sử dụng React/TypeScript, FastAPI, SQLite/SQLAlchemy, worker và graph LangGraph; mã nguồn đã mô tả các quy tắc bảo mật và kiểm thử liên quan.''',
'''Phạm vi đạt được là triển khai phần mềm và các luồng nghiệp vụ chính theo tài liệu dự án. Chưa đủ căn cứ để tuyên bố hệ thống làm tăng kết quả học tập, AI đạt độ chính xác cụ thể hoặc chịu tải lớn. Kết luận cần được hiểu trong phạm vi chức năng và kiểm thử đã ghi nhận.''']),
('6.2. Hướng phát triển',[
'''Ưu tiên tiếp theo là thiết kế bộ đánh giá AI có nhãn chuyên gia, đo độ hữu ích/độ chính xác theo nhóm lỗi và nghiên cứu tác động học tập trong lớp thật. Song song, cần cải thiện quan sát hệ thống: log có cấu trúc, dashboard job, thông báo lỗi, theo dõi độ trễ và chi phí, kiểm soát retry/idempotency.''',
'''Về hạ tầng, có thể chuyển database sang hệ quản trị phù hợp nhiều kết nối, dùng hàng đợi chuyên biệt, lưu tệp đối tượng và tách worker theo loại tác vụ. Mọi thay đổi nên dựa trên benchmark và yêu cầu vận hành, kèm backup/restore được diễn tập. Về chức năng, có thể thêm gợi ý bài phù hợp, đánh giá ẩn danh hoặc trích dẫn nguồn trong báo cáo, nhưng phải duy trì phân quyền và minh bạch.''',
'''Về quản trị dữ liệu, cần thiết lập thời hạn lưu, quy trình xóa/xuất dữ liệu, thông báo nhà cung cấp AI, hướng dẫn dữ liệu nhạy cảm và cơ chế phản hồi nội dung sai. Về khả năng tiếp cận, tiếp tục đánh giá keyboard, screen reader, tương phản, đa ngôn ngữ và khả năng dùng trên thiết bị di động.'''])])

# Append additional material blocks to reach a substantive ~65-page thesis (not padding).
def appendix_sections():
 return [
 ('PHỤ LỤC A. HƯỚNG DẪN CÀI ĐẶT VÀ VẬN HÀNH',[
  ('A.1. Chuẩn bị môi trường',['''Mã nguồn chia thành hai thư mục ngang hàng: web-02 chứa ứng dụng lớp học và DA-Agent-drive chứa graph phân tích. Cần bảo đảm các đường dẫn tương đối trong cấu hình phù hợp với cấu trúc này. Tạo môi trường ảo Python riêng cho backend, cài requirements.txt và graph-requirements.txt theo README. Frontend cần cài dependency bằng npm.''','''Tạo file .env từ .env.example; không dùng khóa mẫu ở môi trường chia sẻ. Đặt WEB02_SECRET_KEY ngẫu nhiên, chọn provider và cung cấp khóa tương ứng. E2B_API_KEY cần thiết khi tác tử phải chạy Python tùy biến. Không in giá trị bí mật ra console hoặc báo cáo.''']),
  ('A.2. Khởi tạo và chạy',['''Tại backend, áp dụng migration Alembic trước khi chạy API. Tạo tài khoản giáo viên bootstrap bằng lệnh được README hướng dẫn. Chạy uvicorn app.main:app trên cổng phát triển, chạy python -m app.worker ở tiến trình riêng, rồi khởi chạy Vite frontend. Trong Docker Compose, khởi động dịch vụ, bootstrap tài khoản và truy cập giao diện tại địa chỉ cấu hình.''','''Nếu ứng dụng báo database chưa khởi tạo, kiểm tra migration. Nếu job cứ queued, xác nhận worker đang hoạt động và đọc log. Nếu graph lỗi cấu hình, kiểm tra provider/khóa và các dependency graph. Nếu artifact không mở được, xác minh job thành công, đường dẫn file còn tồn tại và quyền truy cập người dùng.''']),
  ('A.3. Sao lưu, khôi phục và cập nhật',['''Sao lưu phải bao gồm cơ sở dữ liệu SQLite, thư mục upload, artifact và cấu hình không bí mật cần thiết để khôi phục. Dừng ghi hoặc tạo snapshot nhất quán trước khi sao lưu database cùng tệp. Thử khôi phục định kỳ vào môi trường riêng, kiểm tra migration và liên kết artifact. Không coi việc có bản sao lưu là đủ nếu chưa thử khôi phục.''','''Trước khi cập nhật, đọc migration mới, tạo backup, áp dụng migration và kiểm tra luồng đăng nhập/giao bài/nộp/asset. Dữ liệu demo cần tách nhãn khỏi dữ liệu thật. Thay đổi schema phải được quản lý qua Alembic, tránh chỉnh tay database triển khai.''']),
  ('A.4. Vận hành an toàn',['''Dùng HTTPS, đặt WEB02_ENV=production và COOKIE_SECURE=true. Giới hạn quyền truy cập máy chủ, không mở cổng database ra Internet, xoay khóa khi có nghi ngờ lộ. Cập nhật phụ thuộc và sao lưu theo chính sách. Chỉ dùng dataset mà lớp có quyền xử lý; loại bỏ tên, email, mã định danh cá nhân nếu không cần thiết.''','''Theo dõi dung lượng volume, job queued/running/failed, lỗi API, độ trễ dịch vụ AI và số lần retry. Có quy trình thông báo người dùng khi dịch vụ ngoài lỗi. Không đặt thông tin định danh cá nhân vào prompt nếu không cần. Định kỳ rà soát endpoint asset và quyền sau khi thay đổi chế độ chia sẻ.'''])]),
 ('PHỤ LỤC B. MA TRẬN KIỂM THỬ THAM KHẢO',[
  ('B.1. Ca kiểm thử chức năng',['''TC01 – Đăng nhập hợp lệ: dùng tài khoản đã tạo; kết quả mong đợi là phiên hoạt động và trang dashboard phù hợp vai trò. TC02 – Sai mật khẩu: đăng nhập bị từ chối, không tiết lộ mật khẩu lưu. TC03 – Tạo lớp: giáo viên có lớp mới và mã tham gia duy nhất. TC04 – Sinh viên tham gia: mã đúng tạo membership; mã sai bị từ chối.''','''TC05 – Tạo bài hợp lệ: giáo viên tải CSV/XLSX, thêm câu hỏi, lịch và lưu nháp. TC06 – Loại file không hỗ trợ: API từ chối. TC07 – File quá lớn: API từ chối theo giới hạn. TC08 – Công bố bài: sinh viên thành viên thấy bài; người ngoài lớp không thấy. TC09 – Sửa bộ câu hỏi sau công bố: thao tác không được phép.''','''TC10 – Trợ lý phân tích: yêu cầu hợp lệ sinh artifact hoặc câu trả lời và job hoàn tất. TC11 – Lỗi provider: job ghi trạng thái lỗi rõ ràng. TC12 – Lưu nháp: nội dung vẫn còn sau tải lại trang. TC13 – Nộp bài: hệ thống tạo version snapshot. TC14 – Nộp cải thiện: phiên bản mới tăng số thứ tự, phiên bản cũ không đổi.''','''TC15 – Xem chia sẻ trước giờ: bị từ chối. TC16 – Chế độ all: bài nộp xuất hiện sau giờ mở. TC17 – Chế độ opt-in: chỉ bài đã bật chia sẻ xuất hiện. TC18 – Review: lưu rating, điểm mạnh, góp ý, điều học. TC19 – Review trùng người/phiên bản: cập nhật bản đã có, không tạo bản thứ hai. TC20 – So sánh nhiều hơn số tối đa: bị từ chối.''','''TC21 – Thu hồi chia sẻ: API không trả kết quả so sánh dùng nguồn không còn hợp lệ. TC22 – Giáo viên công bố điểm: sinh viên xem được điểm của đúng phiên bản. TC23 – Sinh viên khác xem đáp án: bị từ chối. TC24 – Truy cập artifact chéo lớp: bị từ chối. TC25 – Khôi phục job dở: job quá hạn được đưa về hàng đợi theo chính sách.''']),
  ('B.2. Ca kiểm thử bảo mật và dữ liệu',['''Kiểm tra quyền phải bao gồm gọi API trực tiếp, thay ID trong URL/request body và dùng phiên hết hạn. Kiểm tra CSRF với token thiếu/sai. Kiểm tra file có tên chứa đường dẫn tương đối, ký tự Unicode, đuôi kép và nội dung không khớp MIME. Kiểm tra HTML thô trong Markdown không được thực thi.''','''Kiểm tra dữ liệu bao gồm CSV rỗng, dấu phân cách khác, Unicode, giá trị thiếu, cột trùng tên, hàng rất dài, dữ liệu lẫn kiểu và XLSX nhiều worksheet. Ghi nhận lỗi nào được thông báo thân thiện, lỗi nào cần log nội bộ. Không để stack trace hoặc bí mật provider xuất hiện trong phản hồi trình duyệt.''']),
  ('B.3. Phiếu ghi nhận kết quả',['''Với mỗi ca, điền: ID, ngày giờ, commit, môi trường, người kiểm tra, dữ liệu đầu vào, bước thực hiện, kết quả mong đợi, kết quả thực tế, trạng thái Pass/Fail/Blocked, ảnh chụp/log, mã lỗi và người xử lý. Một kiểm thử chỉ được đánh dấu Pass khi có bằng chứng và phiên bản chạy được xác định.''','''Tổng số ca đã chạy: [BỔ SUNG]. Số pass: [BỔ SUNG]. Số fail: [BỔ SUNG]. Số blocked: [BỔ SUNG]. Commit/hash: [BỔ SUNG]. Môi trường: [BỔ SUNG]. Các lỗi tồn tại và mức độ: [BỔ SUNG]. Không suy ra tỷ lệ chất lượng AI từ số lượng test phần mềm.'''])]),
 ('PHỤ LỤC C. MÔ HÌNH DỮ LIỆU VÀ API',[
  ('C.1. Tóm tắt quan hệ dữ liệu',['''User (1) – (n) Membership; Classroom (1) – (n) Membership; User giáo viên (1) – (n) Classroom; Classroom (1) – (n) Assignment; Assignment (1) – (n) AssignmentQuestion; Assignment (1) – (n) Submission; User sinh viên (1) – (n) Submission; Submission (1) – (n) SubmissionVersion; Submission (1) – (n) SubmissionAnswer; SubmissionVersion (1) – (n) PeerReview; AIJob (1) – (n) Artifact. Các ràng buộc duy nhất giữ một membership mỗi cặp lớp/người, một submission gốc mỗi cặp bài/sinh viên, một thứ tự phiên bản mỗi submission và một review mỗi người/phiên bản.''','''Mô hình không thay thế tài liệu schema thực tế. Khi bổ sung sơ đồ ERD chính thức, cần lấy tên cột, kiểu dữ liệu, nullable, khóa ngoại và index từ models.py/migration đúng commit. Bảng AIJob có thể dùng cho nhiều loại tác vụ; trường prompt/result lưu cấu trúc phụ thuộc loại job.''']),
  ('C.2. Nhóm API nghiệp vụ',['''API xác thực cung cấp session/CSRF; API lớp xử lý tạo lớp, danh sách và tham gia; API bài tập xử lý tạo/sửa nháp/công bố, dataset và câu hỏi; API submission xử lý nháp, nộp, phiên bản, chia sẻ, review, bình luận và điểm; API AI tạo tác vụ và đọc trạng thái; API assets xác minh quyền tải artifact. Tên route cụ thể cần đối chiếu OpenAPI tại phiên bản chạy.''','''So sánh bài có các thao tác liệt kê phiên bản được phép, tạo yêu cầu với base_version_id và peer_version_ids, xem job/result. API cần xác minh quyền ở cả lúc tạo lẫn lúc lấy lại kết quả. Kết quả dùng ID phiên bản cố định, nhưng quyền chia sẻ được đánh giá lại khi truy xuất.''']),
  ('C.3. Trạng thái và chuyển đổi',['''Assignment có vòng đời draft → published; trạng thái published khóa bộ câu hỏi theo quy tắc hiện tại. AIJob chuyển queued → running → done hoặc failed; phục hồi có thể đưa một số job running quá hạn về queued. SubmissionVersion được tạo khi nộp; các bản cải thiện tạo version mới. Điểm có trạng thái chưa công bố/công bố. Quyền xem bài phụ thuộc trạng thái assignment, thời điểm sharing_open_at, share_mode, shared flag và quan hệ thành viên.'''])]),
 ('PHỤ LỤC D. KỊCH BẢN DEMO VÀ HƯỚNG DẪN NGƯỜI DÙNG',[
  ('D.1. Giáo viên',['''Đăng nhập bằng tài khoản đã bootstrap. Tạo một lớp thực hành, ghi lại mã lớp trong phạm vi demo. Tạo bài “Khám phá dữ liệu bán lẻ”, tải dataset mẫu đã rà soát thông tin nhạy cảm, nhập câu hỏi về doanh thu/nhóm sản phẩm và cấu hình rubric. Thiết lập hạn nộp, giờ mở chia sẻ và chế độ chia sẻ. Kiểm tra câu hỏi, file và thời gian trước khi công bố.''','''Nếu dùng tạo đề AI, gửi yêu cầu với số lượng câu và độ khó phù hợp, chờ job, xem từng câu và kết quả phân tích, chỉnh sửa, bấm lưu đề đã duyệt. Không công bố đầu ra chưa kiểm tra. Sau khi sinh viên nộp, mở dashboard bài nộp, xem đánh giá AI và tự nhập nhận xét/điểm. Công bố điểm khi đã xem xét.''']),
  ('D.2. Sinh viên',['''Đăng ký/đăng nhập và tham gia lớp bằng mã. Mở bài đã công bố, đọc mô tả, kiểm tra hạn và lịch chia sẻ. Chọn câu hỏi, yêu cầu trợ lý thực hiện phân tích cụ thể. Kiểm tra số liệu/biểu đồ, so sánh với dữ liệu và viết kết luận bằng lời của mình. Nêu phương pháp, bằng chứng và giới hạn. Lưu nháp trước khi nộp.''','''Khi nộp, kiểm tra bản xem trước và xác nhận. Sau đó xem trạng thái đánh giá AI; dùng gợi ý như đầu vào để rà soát chứ không sao chép máy móc. Khi chia sẻ mở, đọc bài bạn, để lại phản hồi theo tiêu chí và ghi lại điều học được. Nếu cho phép cải thiện, chỉnh bài, nêu thay đổi và nộp phiên bản mới.''']),
  ('D.3. Mẫu rubric phân tích',['''Câu hỏi và mục tiêu (0–4): câu hỏi rõ, phù hợp dữ liệu. Phương pháp (0–4): phép lọc/tổng hợp/so sánh đúng và giải thích được. Bằng chứng (0–4): số liệu hoặc biểu đồ liên quan, nhãn và đơn vị rõ. Diễn giải (0–4): kết luận bám bằng chứng, phân biệt tương quan với nhân quả. Giới hạn (0–4): nêu thiếu dữ liệu, thiên lệch, bất định và điều cần kiểm tra thêm. Cộng điểm và quy đổi cần được giáo viên điều chỉnh theo học phần; đây là khung tham khảo, không phải rubric đã phê duyệt.'''])]),
 ('PHỤ LỤC E. KẾ HOẠCH ĐÁNH GIÁ THỰC NGHIỆM',[('E.1. Câu hỏi nghiên cứu',['''Câu hỏi nghiên cứu 1: mức độ nhất quán của phản hồi AI so với chuyên gia là bao nhiêu? Câu hỏi 2: chất lượng lập luận và bằng chứng của người học thay đổi ra sao sau vòng phản hồi? Câu hỏi 3: người học đánh giá tính hữu ích và độ tin cậy của luồng chia sẻ như thế nào? Câu hỏi 4: thời gian phản hồi và lỗi hệ thống thay đổi theo tải ra sao?''','''Thiết kế gợi ý: chọn nhiều lớp/học phần tương đương, dùng dataset và rubric chung, thu bài trước/sau hoặc nhóm dùng DataClass và nhóm quy trình hiện hành. Hai người chấm độc lập đánh giá bài đã ẩn danh; tính độ đồng thuận. Mẫu nghiên cứu, tiêu chí đưa vào/loại trừ và phân tích thống kê cần được phê duyệt trước. Không sử dụng điểm môn học làm thước đo duy nhất.''']),('E.2. Chỉ số và đạo đức',['''Đánh giá AI: lập tập dữ liệu vàng, gán nhãn tối thiểu hai chuyên gia, đo nhãn theo từng loại lỗi, precision/recall/F1, độ đồng thuận và tỷ lệ nhận xét không có chứng cứ. Đánh giá trải nghiệm: bảng hỏi Likert, câu hỏi mở, phỏng vấn ngắn và nhật ký thời gian. Đánh giá tải: đo p50/p95 thời gian API, thời gian job, queue depth, tỉ lệ thất bại, CPU/RAM, chi phí AI cho các kịch bản tải có kiểm soát.''','''Đạo đức và dữ liệu: thông báo rõ việc dùng AI và dịch vụ bên ngoài, có cơ chế đồng thuận, ẩn danh, giới hạn lưu giữ, cho phép rút dữ liệu theo chính sách và không đưa bản nháp vào huấn luyện nếu chưa có căn cứ. Báo cáo phải công khai hạn chế, mất dữ liệu, thiên lệch chọn mẫu và khác biệt giữa phiên bản mô hình.'''])]),
 ('PHỤ LỤC F. THÔNG TIN CẦN HOÀN THIỆN TRƯỚC KHI NỘP',[('F.1. Danh sách hoàn thiện',['''Thông tin bìa: [BỔ SUNG HỌ VÀ TÊN SINH VIÊN], [BỔ SUNG MÃ SINH VIÊN], [BỔ SUNG LỚP], [BỔ SUNG NGÀNH/KHOA NẾU KHÁC MẪU], [BỔ SUNG GIẢNG VIÊN HƯỚNG DẪN], [BỔ SUNG HỌC KỲ/NĂM HỌC], [BỔ SUNG NGÀY THÁNG].''','''Thông tin kỹ thuật cần xác nhận: phiên bản commit cuối, phiên bản Python/Node/React/FastAPI/SQLite, provider/model đã dùng, số câu hỏi/file giới hạn hiện hành, migration cuối, cấu hình triển khai demo, và ảnh chụp giao diện thật. Bổ sung ảnh thật thay cho sơ đồ logic nếu yêu cầu hội đồng minh chứng UI.''','''Thông tin đánh giá cần xác nhận: số test chạy trên commit cuối, log và môi trường; kết quả build frontend; các lỗi đã biết; benchmark nếu đã thực hiện; khảo sát người dùng nếu có phê duyệt. Nếu chưa có nghiên cứu người dùng, giữ nguyên cách diễn đạt rằng hiệu quả học tập chưa được kiểm chứng.''','''Thông tin học thuật cần rà soát: tài liệu tham khảo cần đối chiếu đúng phiên bản tiêu chuẩn, trích dẫn trong từng chương, kiểm tra DOI/URL, quy định của trường về sử dụng AI và định dạng; cập nhật mục lục, danh mục bảng/hình tự động bằng Microsoft Word; rà soát Turnitin theo quy định của đơn vị.'''])])]

def add_para(body, text, style='Normal', bold=False, italic=False, align=None, pagebreak=False):
 p=ET.SubElement(body,q(W,'p'))
 ppr=ET.SubElement(p,q(W,'pPr'))
 style_map={'Title':'Heading1','Subtitle':'Heading2','Caption':'Normal'}
 st=ET.SubElement(ppr,q(W,'pStyle')); st.set(q(W,'val'),style_map.get(style,style))
 if align:
  jc=ET.SubElement(ppr,q(W,'jc')); jc.set(q(W,'val'),align)
 if pagebreak:
  r=ET.SubElement(p,q(W,'r')); br=ET.SubElement(r,q(W,'br')); br.set(q(W,'type'),'page'); return p
 r=ET.SubElement(p,q(W,'r')); rpr=ET.SubElement(r,q(W,'rPr'))
 if bold: ET.SubElement(rpr,q(W,'b'))
 if italic: ET.SubElement(rpr,q(W,'i'))
 t=ET.SubElement(r,q(W,'t')); t.text=text; t.set('{http://www.w3.org/XML/1998/namespace}space','preserve')
 return p

def add_image(body, filename, rid, caption, cx=7800000, cy=4100000):
 p=ET.SubElement(body,q(W,'p')); pp=ET.SubElement(p,q(W,'pPr')); ET.SubElement(pp,q(W,'jc')).set(q(W,'val'),'center')
 run=ET.SubElement(p,q(W,'r')); drawing=ET.SubElement(run,q(W,'drawing')); inline=ET.SubElement(drawing,q(WP,'inline'))
 ET.SubElement(inline,q(WP,'extent'),{'cx':str(cx),'cy':str(cy)}); ET.SubElement(inline,q(WP,'docPr'),{'id':'1','name':filename})
 gf=ET.SubElement(inline,q(WP,'graphicFrameLocks')); gf.set('noChangeAspect','1')
 graphic=ET.SubElement(inline,q(A,'graphic')); gd=ET.SubElement(graphic,q(A,'graphicData')); gd.set('uri',PIC)
 pic=ET.SubElement(gd,q(PIC,'pic')); nv=ET.SubElement(pic,q(PIC,'nvPicPr')); ET.SubElement(nv,q(PIC,'cNvPr'),{'id':'0','name':filename}); ET.SubElement(nv,q(PIC,'cNvPicPr'))
 fill=ET.SubElement(pic,q(PIC,'blipFill')); ET.SubElement(fill,q(A,'blip'),{q(R,'embed'):rid}); stretch=ET.SubElement(fill,q(A,'stretch')); ET.SubElement(stretch,q(A,'fillRect'))
 sp=ET.SubElement(pic,q(PIC,'spPr')); xf=ET.SubElement(sp,q(A,'xfrm')); ET.SubElement(xf,q(A,'off'),{'x':'0','y':'0'}); ET.SubElement(xf,q(A,'ext'),{'cx':str(cx),'cy':str(cy)}); geom=ET.SubElement(sp,q(A,'prstGeom')); geom.set('prst','rect'); ET.SubElement(geom,q(A,'avLst'))
 add_para(body,caption,'Caption',align='center')

with ZipFile(TEMPLATE) as zin:
 files={n:zin.read(n) for n in zin.namelist()}
document=ET.fromstring(files['word/document.xml']); body=document.find(q(W,'body'))
sect=body.find(q(W,'sectPr'))
for child in list(body):
 if child is not sect: body.remove(child)
rels=ET.fromstring(files['word/_rels/document.xml.rels'])
maxid=0
for rel in rels:
 m=re.fullmatch(r'rId(\d+)',rel.get('Id',''))
 if m:maxid=max(maxid,int(m.group(1)))
imgids=[]
for name in ['architecture.png','workflow.png']:
 maxid+=1; rid=f'rId{maxid}'; imgids.append(rid)
 rel=ET.SubElement(rels,q(REL,'Relationship'),{'Id':rid,'Type':'http://schemas.openxmlformats.org/officeDocument/2006/relationships/image','Target':'media/'+name})
 files['word/media/'+name]=(MEDIA/name).read_bytes()

# Title pages follow the original school's cover pattern; personal identifiers are explicit fill-in fields.
for x in ['ĐẠI HỌC KINH TẾ QUỐC DÂN','TRƯỜNG CÔNG NGHỆ','KHOA CÔNG NGHỆ THÔNG TIN','KHÓA LUẬN TỐT NGHIỆP']:
 add_para(body,x,'Title',bold=True,align='center')
 add_para(body,'',pagebreak=True)
add_para(body,'XÂY DỰNG NỀN TẢNG HỌC PHÂN TÍCH DỮ LIỆU DATACLASS','Title',bold=True,align='center')
add_para(body,'TÍCH HỢP TRỢ GIẢNG AI VÀ QUY TRÌNH HỌC TẬP CÓ PHIÊN BẢN','Subtitle',align='center')
for _ in range(4): add_para(body,'')
for x in ['Sinh viên: [BỔ SUNG HỌ VÀ TÊN]','Mã sinh viên: [BỔ SUNG]','Lớp: [BỔ SUNG]','Ngành: [BỔ SUNG]','Khoa: Công nghệ thông tin','Giảng viên hướng dẫn: [BỔ SUNG]']:
 add_para(body,x,'Normal',align='center')
for _ in range(5): add_para(body,'')
add_para(body,'Hà Nội, năm 2026','Normal',align='center')
add_para(body,'',pagebreak=True)
add_para(body,'THÔNG TIN KHÓA LUẬN','Heading1',bold=True,align='center')
for x in ['Tên đề tài: Xây dựng nền tảng học phân tích dữ liệu DataClass tích hợp trợ giảng AI','Sinh viên thực hiện: [BỔ SUNG]','Mã sinh viên: [BỔ SUNG]','Giảng viên hướng dẫn: [BỔ SUNG]','Đơn vị: Trường Công nghệ – Đại học Kinh tế Quốc dân','Thời gian thực hiện: [BỔ SUNG HỌC KỲ/NĂM HỌC]']:
 add_para(body,x)
add_para(body,'',pagebreak=True)
add_para(body,'MỤC LỤC','Heading1',bold=True,align='center')
p=ET.SubElement(body,q(W,'p')); pp=ET.SubElement(p,q(W,'pPr')); ET.SubElement(pp,q(W,'pStyle')).set(q(W,'val'),'Normal')
r=ET.SubElement(p,q(W,'r')); fld=ET.SubElement(r,q(W,'fldChar')); fld.set(q(W,'fldCharType'),'begin')
r=ET.SubElement(p,q(W,'r')); ins=ET.SubElement(r,q(W,'instrText')); ins.text=' TOC \\o "1-3" \\h \\z \\u '; ins.set('{http://www.w3.org/XML/1998/namespace}space','preserve')
r=ET.SubElement(p,q(W,'r')); ET.SubElement(r,q(W,'fldChar')).set(q(W,'fldCharType'),'separate')
add_para(body,'Mở tài liệu bằng Microsoft Word và chọn Update entire table để cập nhật số trang.','Normal',italic=True)
r=ET.SubElement(p,q(W,'r')); ET.SubElement(r,q(W,'fldChar')).set(q(W,'fldCharType'),'end')

front=[('LỜI CAM ĐOAN','Khóa luận này được thực hiện bởi sinh viên có tên ghi trên bìa. Các nội dung, mã nguồn, dữ liệu và tài liệu tham khảo sử dụng trong báo cáo cần được trích dẫn theo quy định. Các chức năng và kết quả được mô tả dựa trên mã nguồn/tài liệu dự án; nội dung chưa có bằng chứng được đánh dấu là cần bổ sung hoặc hướng đánh giá. Sinh viên chịu trách nhiệm rà soát tính chính xác, quyền sử dụng dữ liệu và quy định về hỗ trợ AI trước khi nộp.'),('LỜI CẢM ƠN','Em xin cảm ơn giảng viên hướng dẫn, thầy cô trong Trường Công nghệ và các cá nhân đã hỗ trợ em trong quá trình hoàn thành đề tài. Em cũng xin cảm ơn các tác giả, cộng đồng phần mềm nguồn mở và những người đã xây dựng các công cụ được sử dụng trong hệ thống. Phần này cần được cá nhân hóa với lời cảm ơn đúng thực tế trước khi nộp.'),('DANH MỤC CÁC TỪ VIẾT TẮT','AI — Trí tuệ nhân tạo (Artificial Intelligence)\nAPI — Giao diện lập trình ứng dụng (Application Programming Interface)\nCSRF — Giả mạo yêu cầu liên trang\nCSV — Định dạng dữ liệu phân tách bằng dấu phẩy\nERD — Sơ đồ thực thể – liên kết\nHTTP — Giao thức truyền siêu văn bản\nJSON — Ký hiệu đối tượng JavaScript\nLMS — Hệ thống quản lý học tập\nORM — Ánh xạ đối tượng – quan hệ\nREST — Phong cách kiến trúc dịch vụ web\nSQL — Ngôn ngữ truy vấn có cấu trúc\nXLSX — Định dạng bảng tính Microsoft Excel\nUTC — Giờ phối hợp quốc tế\nE2B — Môi trường thực thi mã cô lập theo dịch vụ E2B\nLLM — Mô hình ngôn ngữ lớn')]
for title,txt in front:
 add_para(body,title,'Heading1',bold=True,align='center')
 for line in txt.split('\n'): add_para(body,line)
 add_para(body,'',pagebreak=True)

add_para(body,'DANH MỤC BẢNG','Heading1',bold=True,align='center')
for s in ['Bảng 1.1. Mục tiêu và phạm vi đề tài','Bảng 2.1. Thành phần công nghệ chính','Bảng 3.1. Tác nhân và quyền hạn','Bảng 3.2. Yêu cầu chức năng','Bảng 3.3. Yêu cầu phi chức năng','Bảng 4.1. Các thực thể dữ liệu chính','Bảng 5.1. Nhóm kiểm thử','Bảng 5.2. Chỉ số đề xuất cho đánh giá AI','Bảng B.1. Ma trận ca kiểm thử tham khảo'] : add_para(body,s)
add_para(body,'DANH MỤC HÌNH','Heading1',bold=True,align='center')
for s in ['Hình 3.1. Luồng học tập có kiểm soát phiên bản','Hình 4.1. Kiến trúc logic tổng thể của DataClass'] : add_para(body,s)
add_para(body,'',pagebreak=True)
add_para(body,'MỞ ĐẦU','Heading1',bold=True,align='center')
for text in ['Đề tài tập trung xây dựng một môi trường học phân tích dữ liệu trong đó việc đặt câu hỏi, chạy phân tích, diễn giải, nộp báo cáo và nhận phản hồi được kết nối thành một quy trình. Thay vì chỉ cung cấp một chatbot độc lập, DataClass tổ chức hoạt động theo lớp, bài tập và phiên bản; giáo viên duyệt nội dung và công bố đánh giá, sinh viên giữ trách nhiệm với lập luận của mình.','Báo cáo xuất phát từ mã nguồn và tài liệu dự án có sẵn. Vì vậy, mô tả kiến trúc và nghiệp vụ cố gắng phản ánh chức năng đang có, còn các kết quả chưa được xác nhận được trình bày như việc cần bổ sung. Cách phân định này đặc biệt quan trọng khi đánh giá AI: việc một yêu cầu chạy thành công không đồng nghĩa kết luận đúng, và số lượng kiểm thử không phải thước đo kết quả học tập.','Các chương tiếp theo lần lượt giới thiệu nền tảng lý thuyết, yêu cầu, thiết kế, triển khai và kế hoạch đánh giá. Báo cáo dự kiến có độ dài khoảng 65 trang sau khi Word cập nhật mục lục và phân trang theo thiết lập cục bộ; số trang thực tế có thể thay đổi theo phiên bản Office, font và máy in.'] : add_para(body,text)
add_para(body,'Bảng 1.1. Mục tiêu và phạm vi đề tài','Caption',align='center')
def add_table(rows,widths=None):
 tbl=ET.SubElement(body,q(W,'tbl')); pr=ET.SubElement(tbl,q(W,'tblPr')); borders=ET.SubElement(pr,q(W,'tblBorders'))
 for edge in ['top','left','bottom','right','insideH','insideV']:
  e=ET.SubElement(borders,q(W,edge)); e.set(q(W,'val'),'single'); e.set(q(W,'sz'),'6'); e.set(q(W,'color'),'7F8C99')
 for ri,row in enumerate(rows):
  tr=ET.SubElement(tbl,q(W,'tr'))
  for val in row:
   tc=ET.SubElement(tr,q(W,'tc')); p=ET.SubElement(tc,q(W,'p')); pp=ET.SubElement(p,q(W,'pPr')); ET.SubElement(pp,q(W,'jc')).set(q(W,'val'),'left')
   r=ET.SubElement(p,q(W,'r')); rp=ET.SubElement(r,q(W,'rPr'))
   if ri==0: ET.SubElement(rp,q(W,'b'))
   t=ET.SubElement(r,q(W,'t')); t.text=val; t.set('{http://www.w3.org/XML/1998/namespace}space','preserve')
add_table([['Nhóm','Mục tiêu','Phạm vi/giới hạn'],['Sản phẩm','Nền tảng học phân tích dữ liệu','Ứng dụng web theo lớp và bài tập'],['AI','Hỗ trợ khám phá và phản hồi','Không thay thế người chấm; có thể sai'],['Bằng chứng','Lưu câu trả lời và artifact','Không khẳng định hiệu quả học tập nếu chưa đo'],['Vận hành','Triển khai demo một máy','Chưa có benchmark tải quy mô lớn']])

for ci,(title,sections) in enumerate(chapters):
 add_para(body,'',pagebreak=True); add_para(body,title,'Heading1',bold=True,align='center')
 for si,(stitle,paras) in enumerate(sections):
  add_para(body,stitle,'Heading2',bold=True)
  for text in paras: add_para(body,text)
  if ci==0 and si==0:
   add_para(body,'Bảng 1.2. Ranh giới giữa chức năng và bằng chứng','Caption',align='center')
   add_table([['Nội dung','Trạng thái báo cáo'],['Luồng lớp, bài, nộp, chia sẻ','Được mô tả trong mã/tài liệu dự án'],['37 kiểm thử backend','Được ghi nhận trong tài liệu; cần đối chiếu log cuối'],['Độ chính xác AI','Chưa có chỉ số xác nhận'],['Tác động học tập','Cần nghiên cứu với người học']])
  if ci==1 and si==2:
   add_para(body,'Bảng 2.1. Thành phần công nghệ chính','Caption',align='center')
   add_table([['Thành phần','Công nghệ','Vai trò'],['Giao diện','React, TypeScript','Luồng lớp, bài, phân tích'],['API','FastAPI','Nghiệp vụ và kiểm soát quyền'],['CSDL','SQLite, SQLAlchemy','Lưu dữ liệu quan hệ'],['Agent','LangGraph','Điều phối phân tích dữ liệu'],['Sandbox','E2B','Thực thi Python tùy biến'],['Worker','Python worker','Tác vụ AI nền']])
  if ci==2 and si==0:
   add_para(body,'Bảng 3.1. Tác nhân và quyền hạn','Caption',align='center')
   add_table([['Tác nhân','Nhiệm vụ chính','Ràng buộc'],['Giáo viên','Tạo lớp, đề, chấm điểm','Chỉ lớp sở hữu'],['Sinh viên','Làm bài, nộp, review','Thành viên lớp; theo lịch'],['Worker','Thực thi AI job','Chỉ ngữ cảnh được phép'],['Nhà cung cấp AI','Xử lý nội dung được gửi','Dịch vụ bên ngoài']])
  if ci==2 and si==1:
   add_para(body,'Bảng 3.2. Yêu cầu chức năng','Caption',align='center')
   add_table([['Mã','Yêu cầu','Ưu tiên'],['FR-01','Đăng nhập và phân vai trò','Cao'],['FR-02','Tạo lớp và tham gia bằng mã','Cao'],['FR-03','Tạo bài, dataset, câu hỏi và lịch','Cao'],['FR-04','Phân tích và trả lời theo câu hỏi','Cao'],['FR-05','Nộp phiên bản cố định','Cao'],['FR-06','Mở chia sẻ và đánh giá chéo','Cao'],['FR-07','Đánh giá AI/giáo viên','Cao'],['FR-08','Cải thiện và so sánh phiên bản','Trung bình']])
  if ci==3 and si==0:
   add_image(body,'architecture.png',imgids[0],'Hình 4.1. Kiến trúc logic tổng thể của DataClass',cx=7800000,cy=4104000)
  if ci==3 and si==2:
   add_para(body,'Bảng 4.1. Các thực thể dữ liệu chính','Caption',align='center')
   add_table([['Thực thể','Ý nghĩa','Quan hệ tiêu biểu'],['User','Tài khoản/role','Membership, Submission'],['Classroom','Lớp học','Assignment, Membership'],['Assignment','Bài tập và cấu hình','Question, Submission, AIJob'],['SubmissionVersion','Snapshot bài nộp','Review, AIJob'],['AIJob','Tác vụ nền','Artifact'],['PeerReview','Phản hồi đồng đẳng','Version, reviewer']])
  if ci==4 and si==2:
   add_para(body,'Bảng 5.1. Nhóm kiểm thử','Caption',align='center')
   add_table([['Nhóm','Ví dụ','Bằng chứng'],['Chức năng','Tạo bài, nộp, chia sẻ','API/UI và DB riêng'],['Phân quyền','Xem sớm, chéo lớp','HTTP status và dữ liệu'],['Tệp','CSV/XLSX, dung lượng','Kết quả parser/API'],['Worker','Job thành công/lỗi','Trạng thái và log'],['Giao diện','Màn hình/keyboard','Ảnh và checklist']])
  if ci==4 and si==4:
   add_para(body,'Bảng 5.2. Chỉ số đề xuất cho đánh giá AI','Caption',align='center')
   add_table([['Mục tiêu','Chỉ số gợi ý','Cách thu thập'],['Phát hiện lỗi','Precision/Recall/F1','Bài gán nhãn chuyên gia'],['Độ đồng thuận','Kappa/ICC phù hợp loại điểm','Hai người chấm độc lập'],['Hữu ích','Tỷ lệ góp ý được đánh giá hữu ích','Khảo sát và phỏng vấn'],['Vận hành','p50/p95, lỗi, queue depth','Log benchmark']])
  if ci==2 and si==3:
   add_image(body,'workflow.png',imgids[1],'Hình 3.1. Luồng học tập có kiểm soát phiên bản',cx=7800000,cy=3224000)

for title,sections in appendix_sections():
 add_para(body,'',pagebreak=True); add_para(body,title,'Heading1',bold=True,align='center')
 for stitle,paras in sections:
  add_para(body,stitle,'Heading2',bold=True)
  for text in paras: add_para(body,text)
  if title.startswith('PHỤ LỤC B') and stitle.startswith('B.1'):
   add_para(body,'Bảng B.1. Ma trận ca kiểm thử tham khảo','Caption',align='center')
   add_table([['ID','Mục tiêu','Kết quả mong đợi'],['TC01–04','Tài khoản/lớp','Xác thực và membership hợp lệ'],['TC05–09','Tạo bài','Quy tắc file, đề và publish đúng'],['TC10–14','Phân tích/nộp','Job và snapshot đúng'],['TC15–20','Chia sẻ/review','Tuân thủ lịch/chế độ'],['TC21–25','Quyền/worker','Từ chối truy cập trái phép']])

add_para(body,'TÀI LIỆU THAM KHẢO','Heading1',bold=True,align='center')
refs=[
'[1] React, “React Documentation.” [Trực tuyến]. Có tại: https://react.dev/ (truy cập 17/10/2026).',
'[2] FastAPI, “FastAPI Documentation.” [Trực tuyến]. Có tại: https://fastapi.tiangolo.com/ (truy cập 17/10/2026).',
'[3] SQLAlchemy, “SQLAlchemy Documentation.” [Trực tuyến]. Có tại: https://docs.sqlalchemy.org/ (truy cập 17/10/2026).',
'[4] LangChain, “LangGraph Documentation.” [Trực tuyến]. Có tại: https://docs.langchain.com/oss/python/langgraph/ (truy cập 17/10/2026).',
'[5] DuckDB Foundation, “DuckDB Documentation.” [Trực tuyến]. Có tại: https://duckdb.org/docs/ (truy cập 17/10/2026).',
'[6] SQLite, “SQLite Documentation.” [Trực tuyến]. Có tại: https://www.sqlite.org/docs.html (truy cập 17/10/2026).',
'[7] OWASP Foundation, “OWASP Application Security Verification Standard.” [Trực tuyến]. Có tại: https://owasp.org/www-project-application-security-verification-standard/ (truy cập 17/10/2026).',
'[8] M. T. Chi and R. Wylie, “The ICAP Framework: Linking Cognitive Engagement to Active Learning Outcomes,” Educational Psychologist, vol. 49, no. 4, pp. 219–243, 2014, doi: 10.1080/00461520.2014.965823.',
'[9] D. Nicol and D. Macfarlane-Dick, “Formative assessment and self-regulated learning: a model and seven principles of good feedback practice,” Studies in Higher Education, vol. 31, no. 2, pp. 199–218, 2006, doi: 10.1080/03075070600572090.',
'[10] Dự án DataClass, “README, luồng nghiệp vụ, mã nguồn web-02 và DA-Agent-drive,” tài liệu nội bộ trong workspace, phiên bản truy cập 17/10/2026.',
'[11] A. Vaswani et al., “Attention Is All You Need,” in Advances in Neural Information Processing Systems, 2017.',
'[12] National Institute of Standards and Technology, “Artificial Intelligence Risk Management Framework (AI RMF 1.0),” NIST AI 100-1, 2023, doi: 10.6028/NIST.AI.100-1.'
]
for x in refs: add_para(body,x)
add_para(body,'Ghi chú: cần đối chiếu quy định trích dẫn của trường, kiểm tra chính xác phiên bản/trang truy cập và bổ sung trích dẫn trong nội dung. Không để nguồn tham khảo trong danh mục nếu không được sử dụng trong thân bài.','Normal',italic=True)

# title style and field update
settings=ET.fromstring(files['word/settings.xml'])
upd=settings.find(q(W,'updateFields'))
if upd is None: upd=ET.SubElement(settings,q(W,'updateFields'))
upd.set(q(W,'val'),'true')
files['word/settings.xml']=ET.tostring(settings,encoding='utf-8',xml_declaration=True)
files['word/document.xml']=ET.tostring(document,encoding='utf-8',xml_declaration=True)
files['word/_rels/document.xml.rels']=ET.tostring(rels,encoding='utf-8',xml_declaration=True)
# content type entries for image assets
ct=ET.fromstring(files['[Content_Types].xml'])
for ext,ctype in [('png','image/png')]:
 if not any(x.get('Extension')==ext for x in ct): ET.SubElement(ct,'{http://schemas.openxmlformats.org/package/2006/content-types}Default',{'Extension':ext,'ContentType':ctype})
files['[Content_Types].xml']=ET.tostring(ct,encoding='utf-8',xml_declaration=True)
with ZipFile(OUT,'w',ZIP_DEFLATED) as z:
 for n,data in files.items():z.writestr(n,data)
print(OUT)
print('paragraphs',len(body.findall(q(W,'p'))),'tables',len(body.findall(q(W,'tbl'))),'bytes',OUT.stat().st_size)
