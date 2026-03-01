QUY TRÌNH

Tạo hợp đồng trên Odoo → xuất và lưu PDF bản gốc (Unsigned).

Nhấn Gửi Giám đốc ký (VNPT SmartCA) → app SmartCA hiện yêu cầu → Giám đốc xác nhận trên app.

Odoo lấy chữ ký (CMS) từ SmartCA và tạo PDF đã ký bởi công ty (Director-Signed).

Odoo gửi email cho khách kèm link Portal.

Khách vào Portal tải Director-Signed, ký bằng nhà cung cấp chữ ký số của họ, rồi upload lại PDF đã ký đầy đủ.

Odoo lưu Fully-Signed và chuyển hợp đồng sang Completed.


# Hướng dẫn sử dụng Hợp đồng ký số VNPT SmartCA

> Module: `vnpt_smartca_contract_sign` | Odoo 19.0

---

## 1. Tổng quan

Module Chữ ký số cho phép **gửi hợp đồng để ký số điện tử** thông qua nhà cung cấp bên ngoài (Demo, DocuSign, FPT.eSign, VNPT-CA...).

### Luồng hoạt động tổng quát

```mermaid
sequenceDiagram
    participant NV as Nhân viên
    participant HT as Hệ thống Odoo
    participant VNPT as VNPT SmartCA (Giám đốc)
    participant GD as Giám đốc
    participant KH as Khách hàng
    participant CA as Nhà cung cấp ký số khác (của KH)
    participant PT as Portal Odoo

    NV->>HT: 1. Tạo hợp đồng + xuất PDF (Unsigned)
    NV->>HT: 2. Bấm "Gửi Giám đốc ký (VNPT)"
    HT->>VNPT: 3. Tạo giao dịch ký (hash) + doc_id/desc
    VNPT-->>GD: 4. Push yêu cầu ký lên app SmartCA
    GD->>VNPT: 5. Mở app → xem thông tin → xác nhận ký
    VNPT-->>HT: 6. Trả về CMS/PKCS#7 (signature_value) qua status
    HT->>HT: 7. Nhúng CMS vào PDF → tạo "Director-Signed"
    HT->>KH: 8. Gửi email mời ký (kèm link Portal + token)
    KH->>PT: 9. Mở link Portal → tải "Director-Signed"
    KH->>CA: 10. Ký số bằng nhà cung cấp của KH (PAdES)
    KH->>PT: 11. Upload "Fully-Signed" lên Portal
    PT-->>HT: 12. Lưu file + cập nhật trạng thái Completed
    HT-->>NV: 13. Thông báo hoàn tất + lưu bản cuối
```
