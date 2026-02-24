# Custom Addons - Project 2

Folder này chứa các custom addons cho dự án khác.

## Hướng dẫn sử dụng

1. Đặt các module custom của bạn vào folder này
2. Mỗi module phải có cấu trúc chuẩn Odoo:
   ```
   module_name/
   ├── __init__.py
   ├── __manifest__.py
   ├── models/
   ├── views/
   ├── security/
   └── ...
   ```

3. Sau khi thêm module mới, restart Odoo và update Apps list để thấy module mới

## Cấu hình

Folder này đã được thêm vào `addons_path` trong file `odoo.conf`
