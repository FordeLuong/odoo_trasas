# HƯỚNG DẪN SỬ DỤNG HỆ THỐNG QUẢN LÝ HỢP ĐỒNG TRASAS

Tài liệu này hướng dẫn chi tiết quy trình quản lý hợp đồng trên Odoo, được ánh xạ theo **Quy trình Quản lý Hợp đồng (01_TRASAS_QUANLYHOPDONG.pdf)** với đầy đủ 22 bước (B1-B22).

**Ghi chú:** 
- 🎯 Mỗi bước được đánh dấu [BX] để dễ theo dõi
- 📋 Activity (Việc cần làm) sẽ được giao tự động
- ⏰ Deadline sẽ được hệ thống cộng ngày tự động

---

## 1. Phân quyền Người dùng (Roles)

| Vai trò | Nhóm quyền Odoo | Nhiệm vụ chính | Bước thực hiện |
| :--- | :--- | :--- | :--- |
| **Nhân viên** | Contract User | Soạn thảo, trình ký | B1, B3, B6, B12, B13/B14 |
| **Quản lý / Rà soát** | Contract User | Rà soát nội dung | B3 |
| **Giám đốc** | Contract Approver | Phê duyệt, ký | B4, B5, B11, B15 |
| **HCNS** | Contract Manager | Rà soát, đóng dấu, lưu | B3, B16-B19 |

---

## 2. Quy trình Chi tiết từng Bước

### 📝 [B1-B2] KHỞI TẠO HỢP ĐỒNG (Soạn thảo - Draft)

**Trạng thái:** Draft  
**Người thực hiện:** Nhân viên  
**Mục đích:** Tạo hồ sơ hợp đồng mới, điền thông tin đầy đủ

**Thao tác:**
1. Vào menu **Hợp đồng TRASAS > Hợp đồng > Hợp đồng của tôi**
2. Bấm nút **➕ Mới**
3. Điền thông tin bắt buộc:
   - **Loại hợp đồng** (HDMB, HDDV, HDT, v.v)
   - **Đối tác** (Đơn vị ký kết)
   - **Tiêu đề hợp đồng** (Tên ngắn gọn)
   - **Ngày bắt đầu** (Mặc định hôm nay)
   - **Ngày kết thúc** (Mặc định từ loại hợp đồng)
   - **Hạn ký** (Ngày phải hoàn tất ký kết)
   - **Luồng ký:** Chọn
     - ✅ **TRASAS ký trước** (Luồng A) - TRASAS ký trước, rồi gửi đối tác
     - ⭕ **Đối tác ký trước** (Luồng B) - Chờ đối tác ký, rồi TRASAS ký
   - **Người rà soát (Đề xuất)** (Tùy chọn - chỉ cần nếu có Rà soát)

4. Tab **"Thông tin chi tiết":** Điền mô tả hợp đồng (tùy chọn)
5. Bấm **💾 Lưu**

✅ **Hệ thống sẽ:**
- Tự động tạo số hợp đồng (VD: HDMB/2026/0001)
- Ghi lại người tạo (`user_id`)
- Chuyển sang trạng thái "Nháp" (Draft)

---

### 📋 [B3] GỬI RÀ SOÁT NỘI BỘ (Draft → In Review)

**Trạng thái:** Draft → In Review  
**Người thực hiện:** Nhân viên  
**Mục đích:** Lấy ý kiến nội bộ, chỉnh sửa & hoàn thiện nội dung

**Thao tác - NHÂN VIÊN:**
1. Mở hợp đồng ở trạng thái **Draft**
2. Bấm nút **📋 Gửi rà soát**
3. Hệ thống sẽ:
   - ✅ Chuyển trạng thái → **In Review** (Đang rà soát)
   - ✅ Tạo Activity (Việc cần làm) cho người rà soát
   - ✅ Ghi lại lịch sử trong Chatter: **"[B3] Gửi rà soát"**

**Thao tác - NGƯỜI RÀ SOÁT:**
1. Nhận Activity (Việc cần làm) từ hệ thống
2. Vào xem chi tiết hợp đồng
3. Nếu cần sửa:
   - Chat/Ghi chú trong phần **Chatter** (bên phải)
   - Để nhân viên biết phần cần sửa
4. Nếu nội dung OK:
   - Bấm nút **✅ Xác nhận rà soát**
   - Hệ thống sẽ:
     - ✅ Chuyển trạng thái → **Waiting** (Chờ duyệt)
     - ✅ Ghi lại `reviewer_id` (Người rà soát) & `review_date` (Ngày rà soát)
     - ✅ Tạo Activity cho Giám đốc (Deadline: +1 ngày)
     - ✅ Ghi lại lịch sử: **"[B3] Hoàn tất rà soát"**

---

### ⏳ [B4-B5] PHÊ DUYỆT / TỪ CHỐI (Waiting → Approved / Draft)

**Trạng thái:** Waiting → Approved hoặc Draft  
**Người thực hiện:** Giám đốc (Contract Approver)  
**Mục đích:** Ban Giám đốc phê duyệt hoặc từ chối hợp đồng

#### **[B4-B5A] PHÂN DUYỆT**

**Thao tác:**
1. Nhận Activity (Việc cần làm) từ hệ thống
2. Vào xem chi tiết hợp đồng ở trạng thái **Chờ duyệt**
3. Kiểm tra nội dung
4. **Đồng ý phê duyệt:**
   - Bấm nút **✅ Phê duyệt**
   - Hệ thống sẽ:
     - ✅ Chuyển trạng thái → **Approved** (Đã duyệt)
     - ✅ Ghi lại `approver_id` (Người phê duyệt) & `approved_date` (Ngày phê duyệt)
     - ✅ Gửi email thông báo cho nhân viên
     - ✅ Tạo Activity cho nhân viên để bắt đầu ký (Deadline: +2 ngày)
     - ✅ Ghi lại lịch sử: **"[B5] Phê duyệt"**

#### **[B5B] TỪ CHỐI**

**Thao tác:**
1. **Không đồng ý:** Bấm nút **❌ Từ chối**
2. Nhập **lý do từ chối** trong hộp thoại
3. Bấm **Xác nhận**
4. Hệ thống sẽ:
   - ✅ Chuyển trạng thái → **Draft** (Nháp - quay lại)
   - ✅ Ghi lại `rejection_reason` (Lý do từ chối)
   - ✅ Gửi email thông báo cho nhân viên
   - ✅ Tạo Activity cho nhân viên: "⚠️ Bị từ chối. Vui lòng kiểm tra và sửa lại"
   - ✅ Ghi lại lịch sử: **"[B5] Từ chối - Lý do: ..."**

**Nhân viên sẽ:**
- Nhận Activity và thông báo từ chối
- Sửa lại nội dung hợp đồng
- Gửi rà soát lại hoặc gửi duyệt lại (quay lại B3 hoặc B4)

---

### 🖊️ [B6-B9] BẮT ĐẦU KÝ & PHÂN LOẠI LUỒNG KÝ (Approved → Signing)

**Trạng thái:** Approved → Signing  
**Người thực hiện:** Nhân viên  
**Mục đích:** Khởi tạo quá trình ký kết & phân loại theo luồng

**Thao tác:**
1. Nhận Activity (Việc cần làm): "Bắt đầu ký kết"
2. Vào xem hợp đồng ở trạng thái **Đã duyệt**
3. Bấm nút **🖊️ Bắt đầu ký**
4. Hệ thống sẽ:
   - ✅ Chuyển trạng thái → **Signing** (Đang ký)
   - ✅ **Phân loại luồng ký [B9]:**
     - **Nếu chọn "TRASAS ký trước" (Luồng A):**
       - Tạo Activity cho Giám đốc: "Ký hợp đồng TRASAS trước" (Deadline: +3 ngày)
     - **Nếu chọn "Đối tác ký trước" (Luồng B):**
       - Tạo Activity cho nhân viên: "Chờ đối tác ký hợp đồng" (Deadline: +5 ngày)
   - ✅ Ghi lại lịch sử: **"[B6-B9] Bắt đầu ký - Luồng ký: [TRASAS trước/Đối tác trước]"**

---

## 3️⃣ TRACKING 3 MỐC THỜI GIAN (B10-B15) - ⭐ TRỌNG TÂM

Hệ thống tự động ghi lại 3 mốc thời gian quan trọng để tracking quá trình ký kết:

### **Luồng A: TRASAS ký trước** 
```
[B11] TRASAS ký → [B12] Gửi ĐT → [B13] Nhận lại
```

#### **[B11] Xác nhận TRASAS đã ký (Luồng A)**
**Status:** Signing  
**Người:** Giám đốc (hoặc người có thẩm quyền)  
**Mốc 1:** `internal_sign_date` (Ngày nội bộ ký)

**Thao tác:**
1. Nhận Activity: "Ký hợp đồng TRASAS trước"
2. In bản giấy hợp đồng
3. **Ký hợp đồng** theo thẩm quyền
4. Vào Odoo, mở hợp đồng
5. Tab **"Phê duyệt"** → Nhìn mục **"Theo dõi ký kết"**
6. Bấm nút **📝 Xác nhận TRASAS đã ký**
7. Hệ thống sẽ:
   - ✅ Ghi lại **Ngày nội bộ ký** (internal_sign_date) = Hôm nay
   - ✅ Tạo Activity cho nhân viên: "Gửi hợp đồng cho đối tác" (Deadline: +1 ngày)
   - ✅ Ghi lại lịch sử: **"[B11] TRASAS đã ký hợp đồng (Luồng A)"**

#### **[B12] Xác nhận Đã gửi Đối tác (Luồng A)**
**Status:** Signing  
**Người:** Nhân viên  
**Mốc 2:** `sent_to_partner_date` (Ngày gửi đối tác)

**Thao tác:**
1. Nhận Activity: "Gửi hợp đồng cho đối tác"
2. Chuẩn bị bản giấy (đã ký TRASAS)
3. **Gửi cho đối tác/khách hàng** để ký
4. Vào Odoo, mở hợp đồng
5. Tab **"Phê duyệt"** → Nhìn mục **"Theo dõi ký kết"**
6. Bấm nút **📤 Xác nhận Đã gửi Đối tác**
7. Hệ thống sẽ:
   - ✅ Ghi lại **Ngày gửi đối tác** (sent_to_partner_date) = Hôm nay
   - ✅ Tạo Activity cho nhân viên: "Chờ đối tác ký và gửi lại" (Deadline: +7 ngày)
   - ✅ Ghi lại lịch sử: **"[B12] Đã gửi hợp đồng cho đối tác (Luồng A)"**

#### **[B13] Xác nhận Hoàn tất Ký (Luồng A)**
**Status:** Signing → Signed  
**Người:** Nhân viên  
**Mốc 3:** `partner_sign_date` (Ngày đối tác ký)

**Thao tác:**
1. Nhận Activity: "Chờ đối tác ký và gửi lại"
2. **Nhận lại bản giấy** từ đối tác (đã ký cả TRASAS & Đối tác)
3. Vào Odoo, mở hợp đồng
4. Tab **"Phê duyệt"** → Nhìn mục **"Theo dõi ký kết"**
5. Bấm nút **📝 Xác nhận Đối tác đã ký**
6. Hệ thống sẽ ghi lại **Ngày đối tác ký** (partner_sign_date) = Hôm nay
7. Bấm nút **✅ Xác nhận Hoàn tất**
8. Hệ thống sẽ:
   - ✅ Chuyển trạng thái → **Signed** (Đã ký)
   - ✅ Ghi lại `signed_date` (Ngày hoàn tất ký)
   - ✅ Tạo Activity cho HCNS: "Đóng dấu & Lưu kho" (Deadline: +1 ngày)
   - ✅ Ghi lại lịch sử: **"[B13] Hoàn tất ký - Hợp đồng đã được ký đầy đủ"**

---

### **Luồng B: Đối tác ký trước**
```
[B14] Đối tác ký → [B15] TRASAS ký → [B13] Hoàn tất
```

#### **[B14] Xác nhận Đối tác đã ký (Luồng B)**
**Status:** Signing  
**Người:** Nhân viên  
**Mốc 1:** `partner_sign_date` (Ngày đối tác ký)

**Thao tác:**
1. Nhận Activity: "Chờ đối tác ký hợp đồng"
2. **Nhận bản giấy từ đối tác** (đã ký bên đối tác)
3. Vào Odoo, mở hợp đồng
4. Tab **"Phê duyệt"** → Nhìn mục **"Theo dõi ký kết"**
5. Bấm nút **✅ Xác nhận Đối tác đã ký**
6. Hệ thống sẽ:
   - ✅ Ghi lại **Ngày đối tác ký** (partner_sign_date) = Hôm nay
   - ✅ Tạo Activity cho Giám đốc: "Ký hợp đồng TRASAS" (Deadline: +2 ngày)
   - ✅ Ghi lại lịch sử: **"[B14] Nhận hợp đồng đã ký từ đối tác (Luồng B)"**

#### **[B15] Xác nhận TRASAS đã ký (Luồng B)**
**Status:** Signing  
**Người:** Giám đốc  
**Mốc 2:** `internal_sign_date` (Ngày nội bộ ký)

**Thao tác:**
1. Nhận Activity: "Ký hợp đồng TRASAS"
2. **Ký bản giấy** (đã ký bên đối tác rồi)
3. Vào Odoo, mở hợp đồng
4. Tab **"Phê duyệt"** → Nhìn mục **"Theo dõi ký kết"**
5. Bấm nút **📝 Xác nhận TRASAS đã ký**
6. Hệ thống sẽ:
   - ✅ Ghi lại **Ngày nội bộ ký** (internal_sign_date) = Hôm nay
   - ✅ Tạo Activity cho nhân viên: "Hoàn tất ký" (Deadline: +1 ngày)
   - ✅ Ghi lại lịch sử: **"[B15] TRASAS đã ký hợp đồng (Luồng B)"**

#### **[B13] Xác nhận Hoàn tất Ký (Luồng B)**
**Status:** Signing → Signed  
**Người:** Nhân viên  
**Mốc 3:** Hoàn tất (cả 2 đã ký)

**Thao tác:**
1. Nhận Activity: "Hoàn tất ký"
2. Vào Odoo, mở hợp đồng
3. Tab **"Phê duyệt"** → Nhìn mục **"Theo dõi ký kết"**
4. Bấm nút **✅ Xác nhận Hoàn tất**
5. Hệ thống sẽ:
   - ✅ Chuyển trạng thái → **Signed** (Đã ký)
   - ✅ Ghi lại `signed_date` (Ngày hoàn tất ký)
   - ✅ Tạo Activity cho HCNS: "Đóng dấu & Lưu kho" (Deadline: +1 ngày)
   - ✅ Ghi lại lịch sử: **"[B13] Hoàn tất ký"**

---

### 🔐 [B16-B19] ĐÓNG DẤU & LƯU KHO (Signed)

**Status:** Signed  
**Người thực hiện:** HCNS (Contract Manager)  
**Mục đích:** Đóng dấu & lưu trữ bản gốc, upload bản scan

**Thao tác:**

#### **[B16-B17] Đóng dấu**
1. Nhận Activity: "Đóng dấu & Lưu kho"
2. Nhận hợp đồng đã ký hoàn tất (2 bên)
3. **Thực hiện đóng dấu** theo quy định công ty
4. Ghi lại ngày đóng dấu (tự động = ngày hoàn tát ký)

#### **[B18] Lưu kho**
1. Lưu trữ **bản gốc** ở kho hồ sơ

#### **[B19] Upload bản scan**
1. Vào Odoo, mở hợp đồng (Status: Signed)
2. Tab **"File đính kèm"**
3. Kéo-thả hoặc bấm để upload **bản scan cuối cùng** (PDF đã đóng dấu)
4. Hệ thống sẽ tự động lưu

#### **[B18B] Ghi vị trí lưu kho**
1. Tab **"Phê duyệt"**
2. Điền vào trường **"Vị trí lưu kho"** (VD: "Tủ A, Kệ 2")
3. Hệ thống sẽ lưu tự động
4. Ghi lại lịch sử: **"[B16-B19] Đóng dấu & Lưu kho hoàn tất"**

---

### ⏰ [B7-B8] CẢNH BÁO HẠN KÝ (Tự động)

**Cron job:** Chạy mỗi ngày lúc 2:00 AM  
**Mục đích:** Nhắc nhở khi gần đến hạn ký (7 ngày)

**Cách hoạt động:**
- Hệ thống tự động quét hợp đồng có hạn ký trong 7 ngày tới
- Gửi email nhắc nhở đến người phụ trách
- **Người nhận:** Người tạo hợp đồng & Giám đốc
- **Nội dung:** "[B7-B8] Cảnh báo hạn ký - Hợp đồng ... sắp hết hạn ký"

---

### 📊 [B20] CẢNH BÁO HỢP ĐỒNG HẾT HẠN (Tự động)

**Cron job:** Chạy mỗi ngày lúc 1:00 AM  
**Mục đích:** Cảnh báo hợp đồng sắp hết hạn & tự động chuyển Expired

**Cách hoạt động:**

#### **[B20A] Cảnh báo 30 ngày trước hết hạn**
- Hệ thống tự động quét hợp đồng "Đã ký" còn 30 ngày hết hạn
- Gửi email cảnh báo đến người tạo & Giám đốc
- **Nội dung:** "[B20] Cảnh báo - Hợp đồng ... sắp hết hạn (còn X ngày)"

#### **[B20B] Tự động chuyển Expired**
- Khi hợp đồng quá ngày kết thúc (`date_end < Hôm nay`)
- Hệ thống tự động chuyển trạng thái → **Expired** (Hết hạn)
- Ghi lại lịch sử: **"[B20] Hợp đồng đã hết hạn"**
- List view sẽ **hiển thị màu đỏ** để dễ phát hiện

---

### 📋 [B21] TRA CỨU & FILTER (List View)

**Vị trí:** Menu **Hợp đồng TRASAS > Hợp đồng > Tất cả hợp đồng**

**Cách sử dụng:**

#### **1. Danh sách hiển thị (List View)**
- **Màu sắc thông minh:**
  - 🔴 **Đỏ:** Hết hạn hoặc sắp hết hạn (< 30 ngày)
  - 🟡 **Vàng:** Còn 60 ngày
  - 🟢 **Xanh:** Đã ký
  - 🔵 **Xanh đậm:** Chờ duyệt
  - ⚫ **Xám:** Hủy

#### **2. Kanban View (Theo trạng thái)**
- Bấm icon **Kanban** để xem dạng bảng theo trạng thái
- Kéo-thả hợp đồng giữa các cột
- Dễ dàng quản lý workflow

#### **3. Filters (Lọc)**
- **"Của tôi":** Chỉ hợp đồng do bạn tạo
- **"Chờ duyệt":** Hợp đồng cần phê duyệt
- **"Sắp hết hạn":** Còn 30 ngày hoặc ít hơn
- **"Đã ký":** Hoàn tất ký kết

#### **4. Group By (Nhóm)**
- **Theo trạng thái:** Nhóm theo Draft, In Review, Waiting, v.v
- **Theo loại hợp đồng:** HDMB, HDDV, HDT, v.v
- **Theo đối tác:** Hiển thị hợp đồng của từng đối tác
- **Theo người tạo:** Hợp đồng của mỗi nhân viên

#### **5. Search (Tìm kiếm)**
- Tìm theo: Số hợp đồng, Tiêu đề, Đối tác, v.v

---

### 📈 [B22] XUẤT BÁO CÁO (Report & Export)

**Mục đích:** Xuất dữ liệu phục vụ báo cáo Audit, ISO, v.v

**Cách sử dụng:**

#### **1. Export từ List View**
1. Vào **Hợp đồng TRASAS > Tất cả hợp đồng**
2. Bấm icon **⋮ (Menu)** → **Export**
3. Chọn fields cần export (Số, Loại, Đối tác, Trạng thái, Hạn, v.v)
4. Format: **CSV, Excel, PDF**
5. Bấm **Export**

#### **2. Dữ liệu sẵn sàng**
- ✅ Số hợp đồng
- ✅ Loại hợp đồng
- ✅ Đối tác
- ✅ Trạng thái hiện tại
- ✅ Ngày tạo
- ✅ Ngày bắt đầu / Kết thúc
- ✅ Người tạo / Phê duyệt / Ký
- ✅ Ngày phê duyệt / Ký
- ✅ Vị trí lưu kho
- ✅ Ghi chú nội bộ

---

## 4. CHEAT SHEET - Tóm tắt Nhanh

| Bước | Trạng thái | Nút bấm | Người | Deadline |
|:---:|---|---|---|---|
| B1-B2 | Draft | - | NVCN | - |
| B3 | Draft→In Review | 📋 Gửi rà soát | NVCN | - |
| B3 | In Review→Waiting | ✅ Xác nhận rà soát | Reviewer | +1d |
| B4-B5 | Waiting→Approved | ✅ Phê duyệt | GĐ | +2d |
| B5 | Waiting→Draft | ❌ Từ chối | GĐ | Hôm nay |
| B6-B9 | Approved→Signing | 🖊️ Bắt đầu ký | NVCN | +3/+5d |
| B11 | Signing | 📝 TRASAS ký | GĐ | +1d |
| B12 | Signing | 📤 Gửi ĐT | NVCN | +7d |
| B14 | Signing | ✅ ĐT ký | NVCN | +2d |
| B15 | Signing | 📝 TRASAS ký | GĐ | +1d |
| B13 | Signing→Signed | ✅ Hoàn tất | NVCN | +1d |
| B16-19 | Signed | - | HCNS | - |
| B20 | Signed→Expired | 🔐 Tự động | Cron | Mỗi ngày |

---

## 5. Thường Gặp - Q&A

### **Q: Tôi muốn bỏ qua bước rà soát (B3)?**
**A:** Bấm nút **"Gửi duyệt"** thay vì "Gửi rà soát". Hợp đồng sẽ chuyển từ Draft → Waiting trực tiếp.

### **Q: Tôi muốn chọn người rà soát khác?**
**A:** Ở bước B1-B2, chọn **"Người rà soát (Đề xuất)"** trong form. Hệ thống sẽ giao cho người đó.

### **Q: Giám đốc ký mất môi, tôi có thể ký thay được không?**
**A:** Không. Hệ thống sẽ ghi lại `approver_id` là người ký. Cần Giám đốc ký để có tính pháp lý.

### **Q: Làm sao biết đối tác đã ký chưa?**
**A:** Kiểm tra tab **"Phê duyệt"** mục **"Theo dõi ký kết"** - xem `partner_sign_date` đã được điền chưa.

### **Q: Hợp đồng hết hạn, tôi có thể làm gì?**
**A:** Hệ thống sẽ tự động chuyển sang **Expired**. Bạn có thể tạo hợp đồng mới hoặc gia hạn nếu cần.

### **Q: Bản scan nào được lưu?**
**A:** **Bản scan cuối cùng** - là file PDF đã đóng dấu. Upload vào Tab **"File đính kèm"** ở trạng thái Signed.

### **Q: Audit muốn xem lịch sử, tôi upload file đâu?**
**A:** Tất cả lịch sử được ghi trong **Chatter** (chat bên phải form). Bấm **"Export conversation"** để lưu.

---

**📞 Hỗ trợ:** Liên hệ Team IT hoặc HCNS nếu có vấn đề!


