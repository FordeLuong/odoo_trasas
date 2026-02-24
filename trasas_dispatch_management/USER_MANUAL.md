# Hướng dẫn Sử dụng - Module Quản lý Công văn đến

## Mục lục

1. [Giới thiệu](#giới-thiệu)
2. [Vai trò và Phân quyền](#vai-trò-và-phân-quyền)
3. [Quy trình Xử lý Công văn](#quy-trình-xử-lý-công-văn)
4. [Hướng dẫn Chi tiết](#hướng-dẫn-chi-tiết)
5. [Tìm kiếm và Lọc](#tìm-kiếm-và-lọc)
6. [Thông báo và Cảnh báo](#thông-báo-và-cảnh-báo)
8. [Hướng dẫn: Quản lý Công văn đi](#hướng-dẫn-quản-lý-công-văn-đi)
9. [Câu hỏi Thường gặp](#câu-hỏi-thường-gặp)

---

## Giới thiệu

Module **Quản lý Công văn** gồm 2 phần chính:
1.  **Công văn đến:** Tiếp nhận và xử lý văn bản từ bên ngoài.
2.  **Công văn đi:** Soạn thảo, trình ký, ban hành và gửi văn bản đi.

---


## Câu hỏi Thường gặp (Chung)
... (Giữ nguyên phần cũ) ...

### Tính năng chính

- ✅ Tiếp nhận và số hóa công văn
- ✅ Phân loại theo loại văn bản và độ khẩn
- ✅ Phân công người xử lý
- ✅ Theo dõi tiến độ và hạn xử lý
- ✅ Quản lý phản hồi
- ✅ Cảnh báo quá hạn tự động
- ✅ Lưu trữ và tra cứu

---

## Vai trò và Phân quyền

### 1. Nhân viên/Văn thư (User)

**Quyền hạn:**
- Xem công văn được giao
- Cập nhật tiến độ xử lý
- Gửi phản hồi

**Không được:**
- Tiếp nhận công văn mới
- Xác nhận phản hồi
- Xóa công văn

### 2. Phòng HCNS

**Quyền hạn:**
- Tất cả quyền của User
- Tiếp nhận công văn đến
- Phân công người xử lý
- Xác nhận phản hồi
- Tạo và quản lý loại văn bản

**Không được:**
- Xóa công văn
- Chuyển về nháp (chỉ Manager)

### 3. Quản lý (Manager)

**Quyền hạn:**
- Toàn quyền trên hệ thống
- Xóa công văn
- Chuyển về nháp
- Cấu hình hệ thống

---

## Quy trình Xử lý Công văn

### Sơ đồ Quy trình

```
┌─────────────────────────────────────────────────────────────┐
│                    CÔNG VĂN ĐẾN                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  Bước 1: HCNS Tiếp nhận               │
        │  - Tạo hồ sơ công văn                 │
        │  - Scan/Upload file                   │
        │  - Phân loại                          │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  Bước 2: HCNS Phân công               │
        │  - Gán người xử lý                    │
        │  - Đặt hạn xử lý                      │
        │  - Đánh dấu cần phản hồi (nếu có)     │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  Bước 3: HCNS Click "Tiếp nhận"       │
        │  → Trạng thái: ĐANG XỬ LÝ            │
        │  → Gửi thông báo cho người xử lý      │
        └───────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
                ▼                       ▼
    ┌─────────────────────┐   ┌─────────────────────┐
    │  KHÔNG CẦN PHẢN HỒI │   │    CẦN PHẢN HỒI     │
    └─────────────────────┘   └─────────────────────┘
                │                       │
                │                       ▼
                │           ┌───────────────────────────┐
                │           │ Bước 4: Người xử lý       │
                │           │ - Soạn thảo phản hồi      │
                │           │ - Upload file phản hồi    │
                │           │ - Nhập số văn bản         │
                │           └───────────────────────────┘
                │                       │
                │                       ▼
                │           ┌───────────────────────────┐
                │           │ Bước 5: Click "Gửi phản hồi" │
                │           │ → Trạng thái: CHỜ XÁC NHẬN│
                │           │ → Thông báo cho HCNS      │
                │           └───────────────────────────┘
                │                       │
                │                       ▼
                │           ┌───────────────────────────┐
                │           │ Bước 6: HCNS kiểm tra     │
                │           │ - Xem file phản hồi       │
                │           │ - Click "Xác nhận phản hồi"│
                │           └───────────────────────────┘
                │                       │
                ▼                       ▼
        ┌───────────────────────────────────────┐
        │  HCNS Click "Hoàn thành"              │
        │  → Trạng thái: HOÀN THÀNH             │
        │  → Lưu trữ                            │
        └───────────────────────────────────────┘
```

### Trạng thái Công văn

| Trạng thái | Màu sắc | Ý nghĩa |
|-----------|---------|---------|
| **Mới** | 🔵 Xanh | Công văn vừa tạo, chưa tiếp nhận |
| **Đang xử lý** | 🟡 Vàng | Đã tiếp nhận, đang chờ xử lý |
| **Chờ xác nhận** | 🟡 Vàng | Đã có phản hồi, chờ HCNS xác nhận |
| **Hoàn thành** | 🟢 Xanh lá | Đã hoàn tất xử lý |
| **Đã hủy** | ⚫ Xám | Công văn bị hủy |

---

## Hướng dẫn Chi tiết

### A. Dành cho HCNS

#### 1. Tiếp nhận Công văn Mới

**Bước 1: Tạo công văn**
1. Vào menu **Công văn → Công văn đến**
2. Click nút **Tạo**
3. Điền thông tin:
   - **Số hiệu văn bản**: Số văn bản gốc (VD: 123/CV-ABC)
   - **Ngày văn bản**: Ngày trên văn bản gốc
   - **Ngày đến**: Ngày nhận được (tự động = hôm nay)
   - **Nơi gửi**: Chọn từ danh sách hoặc tạo mới
   - **Loại văn bản**: Công văn, Quyết định, Thông báo...
   - **Hình thức**: Bản giấy hoặc Bản điện tử
   - **Độ khẩn**: Thường, Khẩn, Hỏa tốc
   - **Trích yếu**: Tóm tắt nội dung

**Bước 2: Upload file**
1. Chuyển sang tab **Đính kèm**
2. Click **Tải lên file** hoặc kéo thả file vào
3. Nếu là bản giấy: Nhập **Nơi lưu bản giấy** (VD: Tủ A, Ngăn 3)

**Bước 3: Phân công xử lý**
1. Chuyển sang tab **Nội dung & Xử lý**
2. Chọn **Người xử lý** (có thể chọn nhiều người)
3. Đặt **Hạn xử lý**
4. Nếu cần phản hồi: Tick ✅ **Cần phản hồi**
5. Nhập **Ý kiến chỉ đạo** (nếu có)

**Bước 4: Tiếp nhận**
1. Click nút **Tiếp nhận**
2. Hệ thống sẽ:
   - Chuyển trạng thái → **Đang xử lý**
   - Tạo Activity cho người xử lý
   - Gửi thông báo email

#### 2. Xác nhận Phản hồi

Khi người xử lý gửi phản hồi:

1. Bạn sẽ nhận thông báo trong Chatter
2. Mở công văn, kiểm tra:
   - Tab **Kết quả phản hồi**
   - Số văn bản phản hồi
   - File phản hồi
3. Nếu OK: Click **Xác nhận phản hồi**
4. Công văn chuyển sang **Hoàn thành**

#### 3. Hoàn thành Trực tiếp

Với công văn **KHÔNG cần phản hồi**:

1. Mở công văn đang xử lý
2. Click nút **Hoàn thành**
3. Công văn chuyển sang **Hoàn thành**

> **Lưu ý:** Nút "Hoàn thành" chỉ hiện với công văn không cần phản hồi. Nếu cần phản hồi, phải chờ người xử lý gửi phản hồi trước.

---

### B. Dành cho Người Xử lý

#### 1. Xem Công văn Được Giao

**Cách 1: Từ Thông báo**
- Click vào thông báo email
- Hoặc click vào Activity trong Odoo

**Cách 2: Từ Menu**
1. Vào menu **Công văn → Công văn đến**
2. Click filter **Của tôi**
3. Xem danh sách công văn được giao

#### 2. Xử lý và Gửi Phản hồi

**Bước 1: Soạn thảo phản hồi**
- Soạn văn bản phản hồi (ngoài hệ thống)
- Lưu file PDF/Word

**Bước 2: Cập nhật vào hệ thống**
1. Mở công văn cần xử lý
2. Chuyển sang tab **Kết quả phản hồi**
3. Nhập **Số văn bản phản hồi** (VD: 456/PH-DEPT)
4. Upload **File phản hồi**
5. Nhập **Ghi chú kết quả** (nếu cần)

**Bước 3: Gửi phản hồi**
1. Click nút **Gửi phản hồi**
2. Hệ thống kiểm tra:
   - ✅ Có số văn bản phản hồi?
   - ✅ Có file phản hồi?
3. Nếu thiếu → Báo lỗi
4. Nếu đủ:
   - Chuyển trạng thái → **Chờ xác nhận**
   - Gửi thông báo cho HCNS

**Bước 4: Chờ xác nhận**
- HCNS sẽ kiểm tra và xác nhận
- Bạn sẽ nhận thông báo khi hoàn thành

---

## Tìm kiếm và Lọc

### Filters Nhanh

Tại màn hình danh sách, click vào các filter:

| Filter | Hiển thị |
|--------|----------|
| **Chờ xử lý** | Công văn đang xử lý |
| **Chờ xác nhận** | Công văn đã có phản hồi, chờ HCNS xác nhận |
| **Quá hạn** | Công văn đã quá hạn xử lý |
| **Cần phản hồi** | Công văn yêu cầu phản hồi |
| **Đã hoàn thành** | Công văn đã hoàn tất |
| **Của tôi** | Công văn được giao cho bạn |

### Tìm kiếm

Gõ vào ô tìm kiếm để tìm theo:
- Số đến (CV-IN-2026-0001)
- Số hiệu văn bản
- Trích yếu nội dung
- Nơi gửi

### Nhóm theo

Click **Nhóm theo** để xem công văn theo:
- Loại văn bản
- Nơi gửi
- Trạng thái
- Độ khẩn

---

## Thông báo và Cảnh báo

### 1. Thông báo Công văn Mới

**Khi nào:** HCNS tiếp nhận công văn và gán cho bạn

**Nội dung:**
- Số đến
- Số hiệu văn bản
- Nơi gửi
- Trích yếu
- Hạn xử lý
- Link trực tiếp đến công văn

**Cách nhận:**
- Email
- Activity trong Odoo
- Chatter notification

### 2. Cảnh báo Quá hạn

**Khi nào:** Công văn quá hạn xử lý

**Tần suất:** Hàng ngày lúc 8:00 sáng

**Nội dung:**
- Danh sách công văn quá hạn
- Hạn xử lý
- Số ngày quá hạn

**Người nhận:**
- Người xử lý
- Người tạo công văn

### 3. Thông báo Phản hồi Mới

**Khi nào:** Người xử lý gửi phản hồi

**Người nhận:** HCNS

**Nội dung:**
- Thông báo có phản hồi mới
- Người gửi
- Link đến công văn

---

## Câu hỏi Thường gặp

### Q1: Tôi không thấy nút "Tiếp nhận"?

**A:** Bạn không có quyền HCNS. Chỉ HCNS và Manager mới thấy nút này. Liên hệ quản trị viên để được cấp quyền.

### Q2: Tại sao không thấy nút "Gửi phản hồi"?

**A:** Kiểm tra:
- Công văn có ở trạng thái **Đang xử lý** không?
- Công văn có tick ✅ **Cần phản hồi** không?
- Bạn có phải người xử lý không?

### Q3: Click "Gửi phản hồi" bị lỗi?

**A:** Kiểm tra đã nhập đủ:
- ✅ Số văn bản phản hồi
- ✅ File phản hồi

Cả 2 thông tin đều bắt buộc.

### Q4: Làm sao biết công văn nào quá hạn?

**A:** 
- Dòng màu **đỏ** trong danh sách
- Ribbon **Quá hạn** trên form
- Click filter **Quá hạn**
- Nhận email cảnh báo hàng ngày

### Q5: Có thể sửa công văn đã hoàn thành không?

**A:** 
- User/HCNS: Không
- Manager: Có thể click **Về nháp** để sửa

### Q6: Làm sao xem lịch sử thay đổi?

**A:** Cuộn xuống cuối form, xem tab **Chatter**. Tất cả thay đổi được ghi lại.

### Q7: Công văn không cần phản hồi thì xử lý thế nào?

**A:** 
- HCNS tiếp nhận như bình thường
- Người xử lý xử lý (ngoài hệ thống)
- HCNS click **Hoàn thành** khi xong

### Q8: Có thể gán nhiều người xử lý không?

**A:** Có. Chọn nhiều người trong trường **Người xử lý**. Tất cả đều nhận thông báo.

### Q9: Thay đổi hạn xử lý sau khi tiếp nhận?

**A:** 
- HCNS/Manager: Có thể sửa trực tiếp
- User: Không thể sửa, liên hệ HCNS

### Q10: File đính kèm có giới hạn dung lượng không?

**A:** Tùy cấu hình server. Thông thường:
- File đơn: Max 25MB
- Tổng: Max 100MB/công văn

---

## Liên hệ Hỗ trợ

**Vấn đề kỹ thuật:**
- Email: it-support@trasas.com
- Hotline: 1900-xxxx

**Hướng dẫn sử dụng:**
- Email: hcns@trasas.com
- Ext: xxx

---

**Phiên bản:** 1.0  
**Cập nhật:** 05/02/2026  
**Module:** trasas_dispatch_management v19.0.1.0.0
