# Hướng dẫn nhanh - TRASAS Demo Users

## 🎯 Mục đích

Module này tạo sẵn **3 users và 3 employees** để test phân quyền của module TRASAS Contract Management.

## 👥 Thông tin đăng nhập

| Tên | Email | Password | Phòng ban | Quyền |
|-----|-------|----------|-----------|-------|
| Nguyễn Văn A | `vanhanh@trasas.com` | `trasas2026` | Vận hành | Contract User |
| Trần Thị B | `giamdoc@trasas.com` | `trasas2026` | Giám đốc | Contract Approver |
| Lê Văn C | `hcns@trasas.com` | `trasas2026` | HCNS | Contract Manager |

## 🚀 Cài đặt

1. **Install TRASAS Contract Management** trước (nếu chưa)
2. **Update Apps List** trong Odoo
3. Tìm **"TRASAS Demo Users"** và click **Install**
4. **Đăng xuất** và đăng nhập lại với một trong 3 tài khoản trên

## 🧪 Test nhanh

### Kịch bản 1: Quy trình phê duyệt

1. **Login**: `vanhanh@trasas.com` / `trasas2026`
   - Tạo hợp đồng mới
   - Click "Gửi duyệt"

2. **Login**: `giamdoc@trasas.com` / `trasas2026`
   - Vào menu "Chờ phê duyệt"
   - Click "Phê duyệt"

3. **Login**: `vanhanh@trasas.com` / `trasas2026`
   - Click "Bắt đầu ký"
   - Click "Xác nhận đã ký"

4. **Login**: `hcns@trasas.com` / `trasas2026`
   - Upload bản scan cuối cùng

### Kịch bản 2: Kiểm tra phân quyền

**Nhân viên Vận hành** (`vanhanh@trasas.com`):
- ✅ Tạo hợp đồng
- ✅ Chỉ thấy hợp đồng của mình
- ❌ Không có nút "Phê duyệt"

**Giám đốc** (`giamdoc@trasas.com`):
- ✅ Xem tất cả hợp đồng
- ✅ Phê duyệt/Từ chối
- ❌ Không upload bản scan

**HCNS** (`hcns@trasas.com`):
- ✅ Toàn quyền
- ✅ Upload bản scan
- ✅ Cấu hình hệ thống

## 📋 Checklist phân quyền

| Chức năng | Vận hành | Giám đốc | HCNS |
|-----------|----------|----------|------|
| Tạo hợp đồng | ✅ | ✅ | ✅ |
| Xem hợp đồng của mình | ✅ | ✅ | ✅ |
| Xem tất cả hợp đồng | ❌ | ✅ | ✅ |
| Gửi duyệt | ✅ | ✅ | ✅ |
| Phê duyệt/Từ chối | ❌ | ✅ | ✅ |
| Bắt đầu ký | ✅ | ✅ | ✅ |
| Upload bản scan | ❌ | ❌ | ✅ |
| Cấu hình loại HD | ❌ | ❌ | ✅ |
| Hủy bất kỳ HD | ❌ | ❌ | ✅ |

## ⚠️ Lưu ý

- Module này chỉ dùng để **DEMO/TEST**
- Không dùng trong **production**
- Password đơn giản: `trasas2026`
- Sau khi test xong, có thể uninstall module này

## 📞 Hỗ trợ

Xem thêm chi tiết trong file [README.md](README.md)

---

**Happy Testing! 🎉**
