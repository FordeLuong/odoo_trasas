# HƯỚNG DẪN SỬ DỤNG — PHÂN HỆ QUẢN LÝ HỒ SƠ & TÀI LIỆU (DMS)

Module kế thừa từ **Documents Enterprise** của Odoo 19, bổ sung quy trình phê duyệt truy cập, cảnh báo hết hạn, và lịch sử truy cập cho doanh nghiệp.

---

## 1. Thiết lập cây thư mục (HCNS)

**Vị trí**: App **Documents** → Sidebar bên trái

**Thao tác**:
1. Mở App **Documents** → Nhấn vào **Company** trên sidebar.
2. Nhấn nút **+ Add Folder** để tạo thư mục con (VD: Hồ sơ, Hợp đồng, Giấy phép...).
3. Thư mục hỗ trợ phân cấp Parent/Child — có thể tạo nhiều tầng lồng nhau.

> Đây là tính năng có sẵn của Odoo Documents Enterprise.

---

## 2. Tải hồ sơ & Nhập thông tin cơ bản (HCNS)

### 2a. Tải file lên thư mục
- Chọn thư mục mong muốn → Nhấn **New** → **Upload** hoặc **kéo-thả file** trực tiếp.

### 2b. Nhập thông tin cơ bản trên tài liệu
**Vị trí**: Mở chi tiết tài liệu → Phần **"Thông tin hồ sơ TRASAS"**

Các trường bổ sung:

| Trường | Mô tả |
|--------|-------|
| Loại hồ sơ | Hợp đồng / Giấy phép / Phụ lục / Nội quy / Chứng chỉ... |
| Số hiệu văn bản | Mã số trên văn bản gốc |
| Cơ quan cấp | Tên cơ quan / bộ phận ban hành |
| Ngày cấp | Ngày ban hành |
| Ngày hết hiệu lực | Để trống nếu không có thời hạn |
| Độ mật | Công khai / Nội bộ / Mật / Tuyệt mật |
| Phòng ban quản lý | Phòng ban chịu trách nhiệm |
| Người phụ trách | Nhân viên quản lý trực tiếp |

---

## 3. Phân quyền truy cập (HCNS)

**3 nhóm quyền chính** (Settings → Users → Tab quyền):

| Nhóm | Khả năng |
|------|----------|
| **Nhân viên** | Xem tài liệu được cấp, tạo yêu cầu truy cập |
| **Quản lý HCNS** | CRUD tất cả tài liệu, duyệt yêu cầu, quản lý thư mục |
| **Ban Giám đốc** | Xem toàn bộ tài liệu, không cần gửi yêu cầu |

---

## 4. Lưu trữ cấu trúc & Phiên bản

- **Phiên bản tài liệu**: Mở file → **Manage Versions** → Upload phiên bản mới. Odoo tự động lưu lịch sử các phiên bản cũ.
- **Lịch sử truy cập (Audit Trail)**: Menu **Quản lý Hồ sơ** → **Lịch sử truy cập** (chỉ HCNS thấy). Ghi nhận ai đã xem/tải/chỉnh sửa file nào, lúc nào.

---

## 5. Cảnh báo tài liệu sắp hết hạn (Tự động)

**Cách hoạt động**:
- Hệ thống quét **hàng ngày** qua Cron Job.
- Trước **30 ngày** hết hạn → Tự động tạo **Activity nhắc việc** cho Người phụ trách + Chuyển trạng thái sang *"Sắp hết hạn"*.
- Đến ngày hết hạn → Tự động chuyển sang *"Hết hiệu lực"* + Gửi thông báo Chatter tới phòng ban liên quan.

**Yêu cầu**: Điền trường **Ngày hết hiệu lực** trên tài liệu để hệ thống nhận diện.

---

## 6. Báo cáo ISO *(Giai đoạn sau)*

Sẽ bổ sung:
- Danh mục tài liệu hiệu lực
- Ma trận phân phối tài liệu
- Danh sách tài liệu hết hạn
- Xuất Excel

---

## 7–10. Quy trình Yêu cầu Truy cập Tài liệu

**Vị trí**: Menu **Quản lý Hồ sơ** → **Yêu cầu truy cập**

### Bước 7: Nhân viên tạo yêu cầu
1. Nhấn **Tạo** → Điền:
   - Tài liệu cần truy cập (chọn nhiều file)
   - Thư mục cần truy cập (nếu muốn xem cả folder)
   - Loại quyền: *Chỉ xem* hoặc *Xem và Chỉnh sửa*
   - Thời hạn: 1 ngày / 3 ngày / 1 tuần / 1 tháng / Vĩnh viễn
   - **Mục đích truy cập** (bắt buộc)
2. Nhấn nút **Gửi yêu cầu** → Trạng thái chuyển sang *"Chờ duyệt"*
3. Hệ thống tự động tạo Activity nhắc việc cho HCNS.

### Bước 8: HCNS phê duyệt
1. HCNS mở danh sách Yêu cầu truy cập (mặc định lọc *"Chờ duyệt"*)
2. Mở yêu cầu → Xem mục đích truy cập
3. **Nhấn "Phê duyệt"** hoặc **"Từ chối"** (có thể ghi lý do từ chối)

### Bước 9: Hệ thống tự động cấp quyền
- Khi HCNS nhấn **Phê duyệt**:
  - Hệ thống tự động **gán quyền truy cập** trên từng tài liệu/thư mục cho nhân viên
  - Quyền có **thời hạn** theo lựa chọn (VD: 7 ngày)
  - Thông báo Chatter ghi nhận đầy đủ

### Bước 10: Nhân viên truy cập
- Sau khi được duyệt, nhân viên có thể vào App **Documents** để xem/tải file đã được cấp quyền.
- Khi hết thời hạn, **Cron tự động thu hồi** quyền truy cập → Trạng thái yêu cầu chuyển sang *"Hết hạn"*.

---

## 11. Ban Giám đốc truy cập trực tiếp

- BGĐ (nhóm quyền **Ban Giám đốc**) có thể mở App **Documents** và **xem toàn bộ tài liệu** mà không cần gửi yêu cầu.
- Đây là quyền **chỉ đọc** (read-only) mặc định — không thể sửa/xóa.

---

## 12. Thu hồi & Cập nhật văn bản (HCNS)

### Thu hồi văn bản hết hiệu lực
1. Mở chi tiết tài liệu → Nhấn nút **"Thu hồi"** (màu đỏ, chỉ HCNS thấy)
2. Hệ thống tự động:
   - Chuyển trạng thái sang *"Đã thu hồi"*
   - **Gửi thông báo Chatter** tới toàn bộ nhân viên phòng ban liên quan

### Kích hoạt lại
- Nếu cần sử dụng lại tài liệu đã thu hồi → Nhấn nút **"Kích hoạt lại"** (màu xanh)

### Cập nhật phiên bản
- Upload file mới lên cùng tài liệu → Sử dụng tính năng **Manage Versions** có sẵn của Odoo.

---

## Tóm tắt trạng thái tài liệu

| Trạng thái | Màu | Ý nghĩa |
|------------|-----|---------|
| Hiệu lực | 🟢 Xanh lá | Tài liệu đang có hiệu lực |
| Sắp hết hạn | 🟡 Vàng | Còn ≤ 30 ngày trước khi hết hạn |
| Hết hiệu lực | 🔴 Đỏ | Đã quá ngày hết hiệu lực |
| Đã thu hồi | ⚪ Xám | HCNS đã thu hồi, không còn sử dụng |
