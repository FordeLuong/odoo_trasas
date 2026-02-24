# TRASAS Contract Management Module

Module quản lý hợp đồng TRASAS cho Odoo 19.

## Tính năng

### Quản lý vòng đời hợp đồng
- ✅ Draft → Waiting → Approved → Signing → Signed
- ✅ Tự động chuyển sang Expired khi hết hạn
- ✅ Có thể Cancel ở bất kỳ giai đoạn nào (trừ Signed/Expired)

### Quy trình phê duyệt
- ✅ Nhân viên tạo và gửi duyệt
- ✅ Giám đốc phê duyệt/từ chối
- ✅ Tracking đầy đủ lịch sử thay đổi

### Luồng ký linh hoạt
- ✅ TRASAS ký trước
- ✅ Đối tác ký trước

### Thông báo tự động
- ✅ Email khi gửi duyệt
- ✅ Email khi phê duyệt/từ chối
- ✅ Email nhắc hạn ký (7 ngày trước)
- ✅ Email nhắc hợp đồng sắp hết hạn (30 ngày trước)
- ✅ Email yêu cầu đóng dấu

### Quản lý file
- ✅ Đính kèm PDF qua Chatter
- ✅ Upload bản scan cuối cùng (chỉ HCNS)

### Phân quyền
- ✅ Contract User: Tạo, sửa, gửi duyệt
- ✅ Contract Approver: Phê duyệt/từ chối
- ✅ Contract Manager: Toàn quyền

### Báo cáo & Tra cứu
- ✅ List view với màu sắc phân biệt
- ✅ Kanban view theo trạng thái
- ✅ Filters: Của tôi, Chờ duyệt, Sắp hết hạn
- ✅ Group by: Trạng thái, Loại, Đối tác, Người tạo

## Cài đặt

1. Copy module vào `custom_addons_project2/`
2. Restart Odoo
3. Update Apps List
4. Install "TRASAS Contract Management"

## Sử dụng

### Tạo loại hợp đồng (Master Data)
1. Vào **Hợp đồng TRASAS > Cấu hình > Loại hợp đồng**
2. Tạo các loại: HDMB, HDDV, HDT...
3. Cấu hình pattern đặt tên: `{code}/{year}/{sequence:04d}`

### Tạo hợp đồng mới
1. Vào **Hợp đồng TRASAS > Hợp đồng > Tất cả hợp đồng**
2. Click **Create**
3. Điền thông tin và đính kèm PDF
4. Click **Gửi duyệt**

### Phê duyệt
1. Giám đốc vào **Chờ phê duyệt**
2. Xem chi tiết và click **Phê duyệt** hoặc **Từ chối**

### Ký kết
1. Sau khi phê duyệt, click **Bắt đầu ký**
2. Tiến hành ký theo luồng đã chọn
3. Click **Xác nhận đã ký**

### Đóng dấu
1. HCNS nhận email yêu cầu đóng dấu
2. Sau khi đóng dấu, upload bản scan vào trường **Bản scan cuối cùng**

## Cron Jobs

- **Kiểm tra hợp đồng sắp hết hạn**: Chạy mỗi ngày lúc 1:00 AM
- **Kiểm tra hạn ký**: Chạy mỗi ngày lúc 2:00 AM

## Cấu trúc

```
trasas_contract_management/
├── models/
│   ├── contract_type.py    # Master data
│   └── contract.py         # Model chính
├── views/
│   ├── contract_type_views.xml
│   ├── contract_views.xml
│   └── menu_views.xml
├── security/
│   ├── security.xml        # Groups & Rules
│   └── ir.model.access.csv
├── data/
│   ├── mail_template_data.xml
│   └── ir_cron_data.xml
└── __manifest__.py
```

## Lưu ý

- Module kế thừa `mail` để có Chatter
- Sử dụng `tracking=True` để ghi log lịch sử
- Record rules đảm bảo User chỉ thấy hợp đồng của mình
- Approver và Manager thấy tất cả

## Tác giả

TRASAS - 2026
