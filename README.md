# 🌸 FLOWER HAPPY - Nền Tảng Phân Tích Dữ Liệu Kinh Doanh Thực Tế

> **FLOWER HAPPY** là ứng dụng web full-stack chuyên nghiệp phục vụ phân tích dữ liệu kinh doanh và sản xuất từ các tệp thực tế của người dùng (.xlsx, .xls, .csv, .json). Hệ thống vận hành theo quy trình khép kín 4 bước tuần tự, hoàn toàn tính toán từ dữ liệu thực tế tại thời gian chạy (runtime), không sử dụng mock data hay kết quả hardcode.

---

## 📌 Các Tính Năng Nổi Bật

### 1. Kết Nối Nguồn Dữ Liệu (Connect)
- **Đa định dạng**: Hỗ trợ kéo-thả và tải lên nhiều tệp `.xlsx`, `.xls`, `.csv`, `.json` trong cùng một phiên làm việc.
- **Xem trước & Quản lý Sheet**: Tự động phát hiện các sheet trong Excel, cho phép chọn sheet phân tích và xem trước 20 dòng đầu tiên.
- **Xác nhận kiểu dữ liệu**: Tự động suy luận kiểu dữ liệu (Văn bản, Số nguyên, Số thực/tiền tệ, Ngày tháng, Đúng/Sai, Danh mục) và cho phép người dùng tùy chỉnh trước khi nạp.
- **Thiết lập dòng tiêu đề (Header Row)**: Tự do chọn chỉ số dòng tiêu đề theo cấu trúc file thực tế.
- **Kiểm soát dung lượng & tệp**: Xác thực định dạng, cảnh báo tệp rỗng, giới hạn dung lượng tải lên theo cấu hình `.env`.

### 2. Làm Sạch & Chuẩn Hóa (Clean)
- **Hồ sơ chất lượng tự động**: Tính điểm chất lượng dữ liệu (Quality Score 0 - 100), thống kê tỷ lệ khuyết thiếu, phát hiện dòng trùng lặp hoàn toàn.
- **Phát hiện lỗi & ngoại lai**: Tự động tìm kiếm lỗi khoảng trắng thừa (trailing whitespace), không đồng nhất chữ hoa/thường, chuỗi tiền tệ dạng văn bản, điểm ngoại lai theo chuẩn IQR (Interquartile Range) và Z-Score.
- **Công cụ làm sạch linh hoạt**:
  - Làm sạch tự động 1-click (Bulk Clean)
  - Xóa dòng trùng lặp
  - Điền hoặc xóa giá trị khuyết thiếu (Mean, Median, Mode, Hằng số, Xóa dòng)
  - Chuẩn hóa văn bản (Cắt khoảng trắng, Chữ thường, Chữ HOA, Viết hoa đầu từ)
  - Chuyển đổi kiểu dữ liệu thông minh (tự động loại bỏ ký hiệu tiền tệ ₫, $, VND và dấu phẩy ngăn cách hàng nghìn)
  - Xử lý ngoại lai (Cắt ngưỡng Winsorize về biên IQR, xóa dòng hoặc gắn cờ)
  - Đổi tên cột dữ liệu
- **Bộ lọc đa điều kiện**: Kết hợp nhiều điều kiện lọc với logic **VÀ (AND)** hoặc **HOẶC (OR)**.
- **Lịch sử biến đổi & Hoàn tác**: Nhật ký ghi nhận chi tiết số dòng/cột thay đổi sau mỗi bước, hỗ trợ **Hoàn tác (Undo)** và **Đặt lại dữ liệu gốc (Reset to raw)** mà không bao giờ ghi đè lên tệp tải lên gốc.

### 3. Phân Tích Số Liệu & PivotChart (Analyze)
- **PivotChart tương tác thời gian thực**:
  - Kéo thả / lựa chọn các trường vào **Hàng (Rows)**, **Cột (Columns 2D)**, và **Giá trị (Values)**.
  - Hỗ trợ các phép toán tổng hợp: **Tổng (SUM)**, **Trung bình (AVG)**, **Đếm dòng (COUNT)**, **Tối thiểu (MIN)**, **Tối đa (MAX)**, **Trung vị (MEDIAN)**.
  - Tùy biến dạng biểu đồ trực tiếp: Cột (Bar), Đường (Line), Miền (Area), Tròn (Pie).
  - Bảng Pivot đồng bộ dữ liệu thời gian thực.
- **Đào sâu phân đoạn (Drill-Down)**: Nhấp vào bất kỳ điểm dữ liệu hay phân khúc nào trên biểu đồ/bảng pivot để mở cửa sổ xem tối đa 50 bản ghi gốc tạo nên số liệu đó.
- **Biểu đồ tùy biến**: Xây dựng đồ thị 2 chiều theo nhu cầu người dùng.
- **Ma trận tương quan Pearson**: Tự động tính toán hệ số tương quan giữa tất cả các biến số và hiển thị bản đồ nhiệt trực quan.
- **Khám phá phân bổ (Distribution)**: Tự động vẽ biểu đồ phân bổ tần suất cho biến số hoặc biến định tính.

### 4. Báo Cáo Hoạt Động & Xuất Tệp (Report)
- **Động cơ trích xuất Insight tự động**:
  - **Điểm yếu & Lỗ hổng dữ liệu**: Phát hiện sự tập trung dữ liệu khuyết thiếu theo phân khúc nhóm hàng/khu vực; cảnh báo độ biến thiên cao (Coefficient of Variation).
  - **Vấn đề kinh doanh phát hiện từ số liệu**: Phát hiện rủi ro tập trung Pareto (Top khách hàng/sản phẩm chiếm tỷ trọng áp đảo), phân khúc hoạt động kém hiệu quả so với trung bình, sụt giảm chu kỳ theo thời gian, bản ghi âm bất thường. **Mỗi phát hiện đều trích dẫn chính xác số liệu và cột tương ứng**.
  - **Khuyến nghị hành động**: Đề xuất các giải pháp kinh doanh cụ thể, xếp hạng theo mức độ Tác động (Cao / Trung bình / Thấp) và Nỗ lực (Dễ / Trung bình / Phức tạp).
  - **Liên kết trực tiếp tới PivotChart**: Mỗi vấn đề trong báo cáo đều có nút mở cấu hình PivotChart tương ứng trong trang Phân tích để người dùng tiếp tục khai phá.
- **Tùy chọn xuất tệp chuyên nghiệp**:
  - Xuất báo cáo Excel đa bảng tính (`.xlsx`): Gồm 4 sheet: "Tổng quan", "Vấn đề & Phát hiện", "Giải pháp đề xuất", "Dữ liệu đã làm sạch".
  - Xuất báo cáo PDF chuẩn in ấn (`.pdf`): Tổng hợp KPI, bảng phân tích vấn đề và kế hoạch hành động.
  - Xuất ảnh biểu đồ PNG (`.png`): Chụp màn hình bảng điều khiển chất lượng cao.

---

## 🛠️ Yêu Cầu Hệ Thống & Cài Đặt

### Yêu cầu tiên quyết:
- **Node.js**: phiên bản `>= 20.0.0`
- **Python**: phiên bản `>= 3.10`

### 1. Cài đặt ban đầu (Một lệnh duy nhất)
Chạy lệnh setup để tạo môi trường ảo Python `venv`, cài đặt các thư viện backend và cài đặt các gói frontend:

```bash
npm run setup
```

Hoặc thực hiện thủ công nếu muốn:
```bash
# 1. Tạo file cấu hình từ file mẫu
copy .env.example .env

# 2. Tạo môi trường ảo Python và cài đặt backend
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r backend/requirements.txt

# 3. Cài đặt frontend
cd frontend
npm install
cd ..
```

---

## 🚀 Khởi Chạy Ứng Dụng

Chạy một lệnh duy nhất để khởi động đồng thời cả Backend (FastAPI) và Frontend (Vite):

```bash
npm run dev
```

Sau khi khởi chạy:
- **Giao diện Web**: [http://localhost:3000](http://localhost:3000)
- **Tài liệu API tương tác (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Địa chỉ bind**: Mặc định cả hai server gắn với địa chỉ an toàn `127.0.0.1`.

---

## 🧪 Chạy Kiểm Thử (Unit Tests & E2E)

Hệ thống đi kèm bộ kiểm thử tự động toàn diện kiểm tra logic làm sạch, thuật toán insight và luồng tích hợp từ đầu đến cuối (E2E):

```bash
npm run test
```

Tất cả các bài kiểm thử:
- `backend/tests/test_cleaner.py`: Kiểm thử phát hiện trùng lặp, điền missing values, chuẩn hóa văn bản, bộ lọc điều kiện.
- `backend/tests/test_analyzer.py`: Kiểm thử tính toán ma trận tương quan, pivot 2 chiều, drill down.
- `backend/tests/test_reporter.py`: Kiểm thử động cơ insight tự động, đánh giá rủi ro tập trung Pareto.
- `backend/tests/test_e2e_flow.py`: Kiểm thử luồng liên thông 4 bước từ tải file Excel, làm sạch, phân tích pivot đến xuất file PDF và Excel.

---

## ⚙️ Biến Môi Trường (.env)

| Biến | Mặc định | Ý nghĩa |
|------|----------|---------|
| `HOST` | `127.0.0.1` | Địa chỉ IP bind server nội bộ |
| `BACKEND_PORT` | `8000` | Cổng dịch vụ FastAPI |
| `FRONTEND_PORT` | `3000` | Cổng dịch vụ Vite Frontend |
| `UPLOAD_DIR` | `./data/uploads` | Thư mục lưu trữ tệp tải lên theo phiên |
| `MAX_UPLOAD_SIZE_MB` | `50` | Giới hạn dung lượng tải lên (MB) |
| `SESSION_CLEANUP_TTL_SECONDS` | `86400` | Thời gian hết hạn phiên làm việc (giây) |

---

## 📂 Dữ Liệu Kiểm Thử Sẵn Có

Trong thư mục `data/` có sẵn tệp dữ liệu kinh doanh hoa tươi thực tế phục vụ kiểm thử:
- `data/sample_flower_business.xlsx`
- `data/sample_flower_business.csv`
Tệp gồm 354 giao dịch với đầy đủ các cột: `Ma_Don`, `Ngay_Dat`, `Khu_Vuc`, `Khach_Hang`, `SanPham`, `So_Luong`, `Don_Gia`, `Doanh_Thu`, `Chi_Phi`, `Loi_Nhuan`, `Ghi_Chu`.
