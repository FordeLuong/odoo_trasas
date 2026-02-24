# 📋 HƯỚNG DẪN SỬ DỤNG — Module Quản lý Tài sản TRASAS

> **Module:** `trasas_asset_management`  
> **Phiên bản:** 19.0.2.0.0  
> **Đối tượng sử dụng:** Phòng HCNS (toàn quyền) & Ban Giám đốc (tra cứu)

---

## Mục lục

1. [Tổng quan quy trình 11 bước](#1-tổng-quan-quy-trình-11-bước)
2. [Phân quyền người dùng](#2-phân-quyền-người-dùng)
3. [Hướng dẫn chi tiết theo từng bước](#3-hướng-dẫn-chi-tiết-theo-từng-bước)
4. [Trường thông tin theo nhóm tài sản](#4-trường-thông-tin-theo-nhóm-tài-sản)
5. [Quản lý trạng thái tài sản](#5-quản-lý-trạng-thái-tài-sản)
6. [Tự động hóa & Thông báo](#6-tự-động-hóa--thông-báo)
7. [Cấu trúc menu](#7-cấu-trúc-menu)

---

## 1. Tổng quan quy trình 11 bước

```
HÀNH CHÍNH NHÂN SỰ (HCNS)
├── B1: Tạo hồ sơ tài sản
├── B2: Nhập thông tin tài sản
├── B3: Cập nhật pháp lý / sở hữu
└── B4: Scan & upload hồ sơ pháp lý

ODOO SYSTEM (Tự động)
├── B5: Cấp mã tài sản tự động
├── B6: Cập nhật trạng thái tài sản
├── B7: Liên kết hồ sơ ↔ tài sản
├── B8: Tracking lịch sử
└── B9: Xuất báo cáo tài sản / khấu hao

BAN GIÁM ĐỐC (BGĐ)
├── B10: Tra cứu toàn bộ thông tin tài sản
└── B11: Xem hồ sơ pháp lý theo loại tài sản
```

---

## 2. Phân quyền người dùng

| Nhóm quyền | Vai trò | Quyền |
|-------------|---------|-------|
| **Asset Manager (HCNS)** | Phòng Hành chính Nhân sự | Tạo, sửa, xoá, upload toàn bộ tài sản & hồ sơ |
| **Asset Director (BGĐ)** | Ban Giám đốc | Chỉ xem — tra cứu tài sản & hồ sơ pháp lý |

> **Lưu ý:** Admin hệ thống tự động có quyền Asset Manager.

### Cách gán quyền cho user:
1. Vào **Thiết lập → Người dùng & Công ty → Người dùng**
2. Chọn user cần gán quyền
3. Tại mục **Quản lý Tài sản**, chọn:
   - `Asset Manager (HCNS)` — cho nhân viên HCNS
   - `Asset Director (Ban Giám đốc)` — cho Ban Giám đốc

---

## 3. Hướng dẫn chi tiết theo từng bước

### Bước 1: Tạo hồ sơ tài sản 📝

**Thao tác:**
1. Mở menu **Quản lý Tài sản → Tài sản**
2. Click nút **"Mới"** (hoặc **"Create"**)
3. Form tài sản mới mở ra ở trạng thái **Nháp**

**Kết quả:**
- Hệ thống tạo Activity nhắc HCNS upload hồ sơ (deadline 7 ngày)
- Email thông báo gửi tự động đến người phụ trách
- Ghi log trong Chatter: "Tài sản đã được tạo với mã: ..."

---

### Bước 2: Nhập thông tin tài sản 📋

Điền đầy đủ các nhóm thông tin trên form:

#### Nhóm 1 — Thông tin định danh
| Trường | Bắt buộc | Mô tả |
|--------|----------|-------|
| Tên tài sản | ✅ | Tên đầy đủ của tài sản |
| Nhóm tài sản | ✅ | Chọn: NXCT / MMTB / TBVP / TSVH |
| Loại tài sản | | TSCĐ / CCDC / Tài sản vô hình |
| Mã tài sản | Tự động | Sinh tự động khi lưu (B5) |

#### Nhóm 2 — Thông tin mua sắm
| Trường | Mô tả |
|--------|-------|
| Nhà cung cấp | Chọn từ danh sách Đối tác |
| Ngày mua / ghi nhận | Ngày mua hoặc nhận tài sản |
| Số HĐ / PO / Hóa đơn | Số hợp đồng, PO hoặc hóa đơn |
| Nguyên giá | Giá mua + chi phí liên quan |
| Giá trị còn lại | Giá trị hiện tại sau khấu hao |

#### Nhóm 3 — Quản lý sử dụng
| Trường | Mô tả |
|--------|-------|
| Bộ phận sử dụng | Phòng ban đang sử dụng |
| Vị trí tài sản | Chi nhánh, kho, tầng, phòng... |
| Người phụ trách | Mặc định là người tạo |

---

### Bước 3: Cập nhật pháp lý / sở hữu 📄

**Thao tác:**
1. Trong form tài sản, chuyển sang tab **"Hồ sơ chứng từ"**
2. Click **"Thêm dòng"** để thêm mới giấy tờ
3. Điền thông tin cho từng dòng:

| Cột | Mô tả |
|-----|-------|
| STT | Kéo thả để sắp xếp |
| Tên giấy tờ | VD: Giấy CN QSDĐ, Hợp đồng mua bán... |
| Ngày cấp | Ngày phát hành giấy tờ |
| Cơ quan cấp | Cơ quan ra quyết định |
| Số GCN | Số giấy chứng nhận / hiệu văn bản |
| Hiệu lực | Ngày hết hiệu lực (để trống nếu vô hạn) |
| Trạng thái | Hiệu lực / Sắp hết hạn / Hết hiệu lực / Đã thu hồi |
| Ghi chú | Thông tin bổ sung |

> **Tab riêng theo nhóm:** Khi chọn nhóm tài sản, tab tương ứng tự động hiện ra:
> - **NXCT** → Tab "Nhà cửa / Công trình" (địa chỉ, diện tích, hoàn công...)
> - **MMTB** → Tab "Máy móc thiết bị" (serial, thông số KT, kiểm định...)
> - **TBVP** → Tab "Thiết bị văn phòng" (serial, bảo hành, IT config...)
> - **TSVH** → Tab "Tài sản vô hình" (license, bản quyền, gia hạn...)

---

### Bước 4: Scan & upload hồ sơ pháp lý 📎

**Thao tác:**
1. Tại tab **"Hồ sơ chứng từ"**, cột **File đính kèm**
2. Click biểu tượng 📎 trên dòng chứng từ cần upload
3. Chọn file scan (PDF, ảnh...)
4. Mỗi dòng chứng từ có thể upload **nhiều file**

**Phân quyền upload:**
- Chỉ user có quyền **Asset Manager** mới upload/sửa/xoá được
- BGĐ chỉ xem file đã upload

---

### Bước 5: Cấp mã tài sản tự động 🔢

**Hoàn toàn tự động** — Hệ thống sinh mã ngay khi lưu (Save).

**Format mã:** `STT.YY/TS-NHÓM-TRS`

| Ví dụ | Giải thích |
|-------|-----------|
| `01.26/TS-NXCT-TRS` | Tài sản thứ 1, năm 2026, nhóm Nhà cửa/CT |
| `03.26/TS-MMTB-TRS` | Tài sản thứ 3, năm 2026, nhóm Máy móc |
| `01.27/TS-TBVP-TRS` | Tài sản thứ 1, năm 2027, nhóm TB Văn phòng |
| `02.26/TS-TSVH-TRS` | Tài sản thứ 2, năm 2026, nhóm Tài sản vô hình |

> **Lưu ý:** Mỗi nhóm tài sản có STT riêng, reset theo năm.

---

### Bước 6: Cập nhật trạng thái tài sản 🔄

Sử dụng các nút trên **Header** của form tài sản:

```
                    ┌──── Bảo trì ←──── Hoàn tất bảo trì ────┐
                    │                                          │
    Nháp ──→ Đang sử dụng ──→ Hư hỏng ──→ Thanh lý
                    │                         ↑
                    └─────────────────────────┘
```

| Nút bấm | Từ trạng thái | Sang trạng thái |
|----------|---------------|-----------------|
| **Đưa vào sử dụng** | Nháp | Đang sử dụng |
| **Bảo trì** | Đang sử dụng | Bảo trì |
| **Hoàn tất bảo trì** | Bảo trì | Đang sử dụng |
| **Hư hỏng** | Đang sử dụng / Bảo trì | Hư hỏng |
| **Thanh lý** | Đang sử dụng / Hư hỏng | Thanh lý |
| **Đặt về nháp** | Bất kỳ | Nháp |

> Mỗi thay đổi trạng thái tự động:
> - Ghi log trong Chatter
> - Gửi email thông báo cho người phụ trách

---

### Bước 7: Liên kết hồ sơ ↔ tài sản 🔗

Đã tự động thông qua:
- Tab **"Hồ sơ chứng từ"** trên form tài sản (One2many)
- **Smart button "Hồ sơ"** hiển thị số lượng hồ sơ, click để xem danh sách

---

### Bước 8: Tracking lịch sử 📊

Tất cả thay đổi được ghi lại trong **Chatter** (cuối form):

Các trường có tracking:
- Tên tài sản, Mã tài sản
- Nhóm tài sản, Loại tài sản
- Nhà cung cấp, Ngày mua, Số HĐ
- Nguyên giá, Giá trị còn lại
- Bộ phận, Vị trí, Người phụ trách
- Tình trạng tài sản
- Toàn bộ trường kế toán / khấu hao

---

### Bước 9: Xuất báo cáo 📈

**Hiện có:**
- **List view** với bộ lọc và nhóm → Export Excel/CSV từ nút ☰
- Các filter nhanh: Nháp, Đang SD, Bảo trì, Hư hỏng, Thanh lý
- Lọc theo loại: TSCĐ, CCDC, Tài sản vô hình

**Cách xuất:**
1. Mở danh sách tài sản
2. Áp dụng filter/nhóm mong muốn
3. Tick chọn bản ghi (hoặc Chọn tất cả)
4. Click **☰ → Xuất** (Export)
5. Chọn format: Excel (.xlsx) hoặc CSV

---

### Bước 10: BGĐ tra cứu thông tin 🔍

**Dành cho users có quyền "Asset Director":**

1. Mở menu **Quản lý Tài sản → Tài sản**
2. Mặc định hiển thị tài sản "Đang sử dụng"
3. Sử dụng thanh tìm kiếm để lọc:
   - Theo tên, mã tài sản
   - Theo nhóm tài sản
   - Theo vị trí, người phụ trách
   - Theo bộ phận sử dụng
   - Theo nhà cung cấp
4. Click vào tài sản để xem chi tiết (chế độ chỉ đọc)

---

### Bước 11: BGĐ xem hồ sơ pháp lý 📂

**Cách 1 — Từ tài sản:**
1. Mở form tài sản bất kỳ
2. Click **smart button "Hồ sơ"** → Xem danh sách chứng từ của tài sản đó

**Cách 2 — Xem tổng hợp:**
1. Mở menu **Quản lý Tài sản → Hồ sơ Pháp lý**
2. Hiển thị toàn bộ chứng từ pháp lý trên hệ thống
3. Có thể lọc theo tài sản, trạng thái, ngày hết hạn

---

## 4. Trường thông tin theo nhóm tài sản

Khi chọn **Nhóm tài sản**, tab riêng tự động hiện ra:

### a. Nhà cửa / Công trình XD (NXCT)
| Trường | Mô tả |
|--------|-------|
| Địa chỉ công trình | Vị trí cụ thể |
| Diện tích (m²) | Diện tích sử dụng |
| Quy mô | Mô tả quy mô |
| Hạng mục | Kho / Văn phòng / Bãi / Nhà xưởng / Khác |
| Ngày xây dựng | Ngày khởi công |
| Ngày hoàn công | Ngày nghiệm thu |
| Thông tin sở hữu | QSDĐ, chủ sở hữu... |

### b. Máy móc thiết bị SX (MMTB)
| Trường | Mô tả |
|--------|-------|
| Model | Tên model thiết bị |
| Serial Number | Số seri |
| Thông số kỹ thuật | Công suất, tải trọng... |
| Năm sản xuất | |
| Nhà sản xuất | |
| Xuất xứ | Quốc gia sản xuất |
| Hạn kiểm định an toàn | Ngày hết hạn kiểm định |
| Lịch bảo trì | Ghi chú lịch bảo dưỡng |

### c. Thiết bị văn phòng (TBVP)
| Trường | Mô tả |
|--------|-------|
| Serial / Asset Tag | Mã quản lý thiết bị |
| Cấu hình kỹ thuật | Đối với thiết bị IT |
| Hạn bảo hành | Ngày hết bảo hành |
| Vị trí lắp đặt | Tầng, phòng, khu vực |

### d. Tài sản vô hình (TSVH)
| Trường | Mô tả |
|--------|-------|
| Mã bản quyền / License key | |
| Nhà cung cấp bản quyền | |
| Ngày hiệu lực | Bắt đầu sử dụng |
| Ngày hết hạn | |
| Số lượng user/license | |
| Điều kiện gia hạn | |
| HĐ dịch vụ đi kèm | Số hợp đồng dịch vụ |

---

## 5. Quản lý trạng thái tài sản

### Sơ đồ chuyển trạng thái

```
    ┌──────────────────────────────────────────────────────┐
    │                                                      │
    │  ┌───────┐     ┌─────────────┐     ┌──────────┐     │
    │  │ Nháp  │────▶│ Đang sử dụng│────▶│ Bảo trì  │     │
    │  └───────┘     └──────┬──────┘     └────┬─────┘     │
    │       ▲               │       ▲         │           │
    │       │               │       └─────────┘           │
    │       │               │     Hoàn tất BT             │
    │  Đặt về nháp          │                             │
    │       │               ▼                             │
    │       │          ┌──────────┐                        │
    │       ├──────────│ Hư hỏng  │                        │
    │       │          └────┬─────┘                        │
    │       │               │                              │
    │       │               ▼                              │
    │       │          ┌──────────┐                        │
    │       └──────────│ Thanh lý │                        │
    │                  └──────────┘                        │
    └──────────────────────────────────────────────────────┘
```

### Ý nghĩa trạng thái
| Trạng thái | Ý nghĩa | Màu hiển thị |
|-----------|---------|--------------|
| **Nháp** | Mới tạo, chưa đưa vào sử dụng | 🔵 Xanh dương |
| **Đang sử dụng** | Đang được quản lý & sử dụng | 🟢 Xanh lá |
| **Bảo trì** | Đang sửa chữa / bảo dưỡng | 🟡 Vàng |
| **Hư hỏng** | Không thể sử dụng | 🔴 Đỏ |
| **Thanh lý** | Đã thanh lý / loại bỏ | 🔴 Đỏ mờ |

---

## 6. Tự động hóa & Thông báo

### Activity (Nhắc việc)
| Sự kiện | Activity cho | Deadline |
|---------|-------------|----------|
| Tạo tài sản mới (B1) | Người phụ trách | 7 ngày — Upload hồ sơ |
| Hồ sơ sẵn sàng | Asset Manager | 3 ngày — Xác nhận kích hoạt |

### Email tự động
| Sự kiện | Gửi đến | Nội dung |
|---------|---------|---------|
| Tạo tài sản mới | Người phụ trách | Thông báo tạo + link xem |
| Thay đổi trạng thái | Người phụ trách | Trạng thái mới + link |
| Giấy tờ sắp hết hạn (≤30 ngày) | Người phụ trách | Cảnh báo + deadline |
| Giấy tờ đã hết hạn | Người phụ trách | Yêu cầu xử lý |

### Cron job (Chạy hàng ngày)
- Tự động kiểm tra giấy tờ sắp hết hạn (≤30 ngày) → đổi trạng thái + gửi email + tạo Activity
- Tự động đánh dấu giấy tờ đã hết hạn → gửi email cảnh báo

---

## 7. Cấu trúc menu

```
📁 Quản lý Tài sản
├── 📋 Tài sản                    ← Danh sách tất cả tài sản
├── 📄 Hồ sơ Pháp lý              ← Tổng hợp chứng từ pháp lý
└── ⚙️ Cấu hình (chỉ HCNS)
    └── 📂 Loại tài sản           ← Quản lý nhóm + sequence
```

---

## Tab Kế toán – Khấu hao

| Trường | Mô tả |
|--------|-------|
| Ngày bắt đầu khấu hao | Ngày bắt đầu tính khấu hao |
| Thời gian khấu hao (tháng) | Tổng số tháng khấu hao |
| Phương pháp khấu hao | Đường thẳng / Số dư giảm dần |
| Tỷ lệ khấu hao (%/năm) | Tự điền theo nhóm, sửa được |
| Fixed Asset Account | TK tài sản cố định |
| Depreciation Account | TK khấu hao |
| Expense Account | TK chi phí |
| Journal | Nhật ký kế toán |

---

> **Liên hệ hỗ trợ:** Phòng HCNS hoặc Admin hệ thống  
> **Phiên bản tài liệu:** v2.0 — Cập nhật 11/02/2026
