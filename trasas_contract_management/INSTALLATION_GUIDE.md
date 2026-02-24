# Hướng dẫn cài đặt và sử dụng Module TRASAS Contract Management

## 📋 Tổng quan

Module quản lý hợp đồng TRASAS cung cấp giải pháp toàn diện để quản lý vòng đời hợp đồng từ soạn thảo đến ký kết và theo dõi.

## 🚀 Cài đặt

### Bước 1: Restart Odoo
```bash
docker-compose down
docker-compose up -d
```

### Bước 2: Update Apps List
1. Đăng nhập Odoo
2. Vào **Apps**
3. Click **Update Apps List**
4. Tìm "TRASAS Contract Management"
5. Click **Install**

## 👥 Phân quyền

Sau khi cài đặt, cần gán quyền cho người dùng:

### Contract User (Nhân viên)
- Tạo hợp đồng
- Sửa hợp đồng của mình
- Gửi duyệt
- Bắt đầu ký và xác nhận ký

**Cách gán:**
1. Vào **Settings > Users & Companies > Users**
2. Chọn user
3. Tab **Access Rights**
4. Tìm **Contract User** và check

### Contract Approver (Giám đốc)
- Tất cả quyền của User
- Xem tất cả hợp đồng
- Phê duyệt/Từ chối

**Cách gán:**
1. Tương tự như trên
2. Check **Contract Approver**

### Contract Manager (HCNS/Admin)
- Toàn quyền
- Đóng dấu
- Upload bản scan
- Cấu hình hệ thống

**Cách gán:**
1. Tương tự như trên
2. Check **Contract Manager**

## 📝 Hướng dẫn sử dụng

### 1. Tạo Loại hợp đồng (Lần đầu)

Trước khi tạo hợp đồng, cần tạo các loại hợp đồng:

1. Vào **Hợp đồng TRASAS > Cấu hình > Loại hợp đồng**
2. Click **Create**
3. Điền thông tin:
   - **Tên**: Hợp đồng mua bán
   - **Mã**: HDMB
   - **Quy tắc đặt tên**: `{code}/{year}/{sequence:04d}`
   - **Thời hạn mặc định**: 365 (ngày)
4. Click **Save**

Ví dụ các loại hợp đồng:
- HDMB - Hợp đồng mua bán
- HDDV - Hợp đồng dịch vụ
- HDT - Hợp đồng thuê
- HDLD - Hợp đồng lao động

### 2. Tạo hợp đồng mới

**Nhân viên thực hiện:**

1. Vào **Hợp đồng TRASAS > Hợp đồng > Tất cả hợp đồng**
2. Click **Create**
3. Điền thông tin:
   - **Loại hợp đồng**: Chọn từ danh sách
   - **Tiêu đề**: Nhập tiêu đề ngắn gọn
   - **Đối tác**: Chọn đối tác
   - **Luồng ký**: TRASAS ký trước / Đối tác ký trước
   - **Ngày bắt đầu/kết thúc**: Chọn thời hạn
   - **Hạn ký**: (Optional) Ngày deadline để hoàn tất ký
4. **Đính kèm file PDF**:
   - Click biểu tượng 📎 ở góc trên
   - Hoặc kéo thả file vào khung Chat
5. Điền **Mô tả** và **Ghi chú nội bộ** nếu cần
6. Click **Save**
7. Click **Gửi duyệt**

→ Hệ thống sẽ gửi email cho Giám đốc

### 3. Phê duyệt hợp đồng

**Giám đốc thực hiện:**

1. Nhận email thông báo
2. Vào **Hợp đồng TRASAS > Hợp đồng > Chờ phê duyệt**
3. Click vào hợp đồng cần duyệt
4. Xem chi tiết và file đính kèm
5. Chọn:
   - **Phê duyệt**: Nếu đồng ý
   - **Từ chối**: Nếu cần chỉnh sửa (nhập lý do)

→ Hệ thống gửi email thông báo cho người tạo

### 4. Ký kết hợp đồng

**Nhân viên thực hiện:**

1. Sau khi được phê duyệt, vào hợp đồng
2. Click **Bắt đầu ký**
3. Tiến hành ký kết theo luồng đã chọn:
   - Nếu TRASAS ký trước: TRASAS ký → Gửi cho đối tác → Đối tác ký
   - Nếu Đối tác ký trước: Đối tác ký → Gửi về TRASAS → TRASAS ký
4. Sau khi cả 2 bên đã ký, click **Xác nhận đã ký**

→ Hệ thống gửi email cho HCNS để đóng dấu

### 5. Đóng dấu và hoàn tất

**HCNS thực hiện:**

1. Nhận email yêu cầu đóng dấu
2. Đóng dấu vào hợp đồng giấy
3. Scan hợp đồng đã đóng dấu
4. Vào hợp đồng trong hệ thống
5. Tab **File đính kèm**
6. Upload file scan vào trường **Bản scan cuối cùng**
7. Click **Save**

→ Hoàn tất! Hợp đồng đã có bản scan chính thức

## 🔔 Thông báo tự động

Hệ thống sẽ tự động gửi email trong các trường hợp:

1. **Gửi duyệt**: Email cho Giám đốc
2. **Phê duyệt**: Email cho người tạo
3. **Từ chối**: Email cho người tạo (kèm lý do)
4. **Hoàn tất ký**: Email cho HCNS
5. **Sắp hết hạn**: Email nhắc nhở (30 ngày trước)
6. **Sắp đến hạn ký**: Email nhắc nhở (7 ngày trước)

## 📊 Tra cứu và báo cáo

### Filters có sẵn:
- **Hợp đồng của tôi**: Chỉ hợp đồng do mình tạo
- **Chờ duyệt**: Hợp đồng đang chờ phê duyệt
- **Sắp hết hạn**: Hợp đồng sẽ hết hạn trong 30 ngày
- **Hết hạn**: Hợp đồng đã hết hạn

### Group By:
- Trạng thái
- Loại hợp đồng
- Đối tác
- Người tạo
- Tháng bắt đầu/kết thúc

### Màu sắc:
- 🔴 **Đỏ**: Hết hạn hoặc còn < 30 ngày
- 🟡 **Vàng**: Còn < 60 ngày
- 🔵 **Xanh**: Chờ duyệt
- 🟢 **Xanh lá**: Đã ký
- ⚫ **Xám**: Đã hủy

## 🔧 Cấu hình nâng cao

### Tùy chỉnh email
1. Vào **Settings > Technical > Email > Templates**
2. Tìm "TRASAS:"
3. Chỉnh sửa nội dung email theo ý muốn

### Tùy chỉnh Cron Job
1. Vào **Settings > Technical > Automation > Scheduled Actions**
2. Tìm "TRASAS:"
3. Thay đổi thời gian chạy nếu cần

### Tùy chỉnh số ngày cảnh báo
Hiện tại:
- Hạn ký: 7 ngày trước
- Hết hạn: 30 ngày trước

Để thay đổi, cần sửa code trong `models/contract.py`

## ❓ FAQ

**Q: Tôi không thấy menu "Hợp đồng TRASAS"?**
A: Kiểm tra xem bạn đã được gán quyền Contract User chưa.

**Q: Tôi không thấy nút "Phê duyệt"?**
A: Chỉ Giám đốc (Contract Approver) mới thấy nút này.

**Q: File PDF đính kèm ở đâu?**
A: Sử dụng biểu tượng 📎 hoặc kéo thả vào khung Chat (Chatter).

**Q: Làm sao để upload bản scan cuối cùng?**
A: Chỉ HCNS (Contract Manager) mới có quyền upload vào trường này.

**Q: Email không được gửi?**
A: Kiểm tra cấu hình email server trong Odoo Settings.

**Q: Hợp đồng tự động hết hạn khi nào?**
A: Cron job chạy mỗi đêm lúc 1:00 AM sẽ tự động chuyển hợp đồng sang trạng thái Expired.

## 📞 Hỗ trợ

Nếu gặp vấn đề, vui lòng liên hệ IT Support hoặc tham khảo file README.md trong module.

---

**Chúc bạn sử dụng module hiệu quả! 🎉**
