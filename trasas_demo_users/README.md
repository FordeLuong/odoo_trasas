# TRASAS Demo Users Module

Module tạo sẵn 3 nhân viên và 3 user để test phân quyền Contract Management.

## 👥 Danh sách Users

### 1. Nguyễn Văn A - Phòng Vận hành
- **Email**: `vanhanh@trasas.com`
- **Password**: `trasas2026`
- **Quyền**: Contract User
- **Chức năng**:
  - Tạo hợp đồng
  - Sửa hợp đồng của mình
  - Gửi duyệt
  - Bắt đầu ký và xác nhận ký
  - Chỉ thấy hợp đồng do mình tạo

### 2. Trần Thị B - Giám đốc
- **Email**: `giamdoc@trasas.com`
- **Password**: `trasas2026`
- **Quyền**: Contract Approver
- **Chức năng**:
  - Tất cả quyền của User
  - Xem tất cả hợp đồng
  - Phê duyệt hợp đồng
  - Từ chối hợp đồng (với lý do)

### 3. Lê Văn C - Phòng HCNS
- **Email**: `hcns@trasas.com`
- **Password**: `trasas2026`
- **Quyền**: Contract Manager + System Admin
- **Chức năng**:
  - Toàn quyền quản lý hợp đồng
  - Đóng dấu và upload bản scan
  - Cấu hình hệ thống
  - Quản lý loại hợp đồng

## 🚀 Cài đặt

### Bước 1: Install module TRASAS Contract Management trước
```bash
# Vào Odoo > Apps > Tìm "TRASAS Contract Management" > Install
```

### Bước 2: Install module này
```bash
# Vào Odoo > Apps > Update Apps List
# Tìm "TRASAS Demo Users" > Install
```

### Bước 3: Đăng xuất và đăng nhập lại
Sử dụng một trong 3 tài khoản trên để test.

## 🧪 Kịch bản test

### Test 1: Quy trình tạo và phê duyệt hợp đồng

1. **Đăng nhập với `vanhanh@trasas.com`**
   - Tạo hợp đồng mới
   - Đính kèm file PDF
   - Click "Gửi duyệt"
   - Kiểm tra: Chỉ thấy hợp đồng của mình

2. **Đăng nhập với `giamdoc@trasas.com`**
   - Vào menu "Chờ phê duyệt"
   - Thấy hợp đồng vừa tạo
   - Click "Phê duyệt"
   - Kiểm tra: Thấy tất cả hợp đồng

3. **Đăng nhập lại với `vanhanh@trasas.com`**
   - Thấy hợp đồng đã được phê duyệt
   - Click "Bắt đầu ký"
   - Click "Xác nhận đã ký"

4. **Đăng nhập với `hcns@trasas.com`**
   - Thấy hợp đồng đã ký
   - Upload bản scan vào trường "Bản scan cuối cùng"
   - Kiểm tra: Có quyền cấu hình loại hợp đồng

### Test 2: Kiểm tra phân quyền

1. **User Vận hành** (vanhanh@trasas.com):
   - ✅ Tạo hợp đồng
   - ✅ Sửa hợp đồng của mình
   - ❌ Không thấy hợp đồng của người khác
   - ❌ Không có nút "Phê duyệt"
   - ❌ Không vào được menu "Cấu hình"

2. **Giám đốc** (giamdoc@trasas.com):
   - ✅ Xem tất cả hợp đồng
   - ✅ Phê duyệt/Từ chối
   - ❌ Không sửa được hợp đồng của người khác
   - ❌ Không upload được bản scan cuối cùng

3. **HCNS** (hcns@trasas.com):
   - ✅ Toàn quyền
   - ✅ Upload bản scan
   - ✅ Cấu hình loại hợp đồng
   - ✅ Hủy hợp đồng bất kỳ

### Test 3: Email notifications

1. Tạo hợp đồng và gửi duyệt → Kiểm tra email của Giám đốc
2. Phê duyệt → Kiểm tra email của người tạo
3. Từ chối → Kiểm tra email của người tạo (có lý do)

## 📝 Lưu ý

- **Password mặc định**: `trasas2026` cho tất cả users
- **noupdate="1"**: Dữ liệu chỉ tạo lần đầu, không update khi upgrade module
- **Employee - User linking**: Mỗi user được link với 1 employee tương ứng

## 🔧 Tùy chỉnh

Nếu muốn thay đổi password hoặc thông tin:

1. Vào **Settings > Users & Companies > Users**
2. Chọn user cần sửa
3. Thay đổi thông tin
4. Click **Save**

Hoặc sửa trực tiếp trong file `data/res_users_data.xml` và upgrade module.

## ⚠️ Quan trọng

Module này chỉ dùng để **DEMO và TEST**. Không nên sử dụng trong môi trường production vì:
- Password đơn giản
- Dữ liệu công khai
- Không có bảo mật cao

Trong production, nên:
- Tạo users thủ công
- Sử dụng password mạnh
- Cấu hình email thật
- Xóa module demo này

## 🎯 Mục đích

Module này giúp bạn:
- ✅ Test nhanh quy trình phê duyệt
- ✅ Hiểu rõ phân quyền 3 cấp
- ✅ Demo cho khách hàng
- ✅ Training cho nhân viên mới

---

**Happy Testing! 🚀**
