# KẾ HOẠCH TÍCH HỢP ODOO ACTIVITIES (VIỆC CẦN LÀM)

Để đảm bảo quy trình thông suốt, hệ thống sẽ tự động giao việc (Activity) cho người phụ trách bước tiếp theo mỗi khi trạng thái hợp đồng thay đổi.

## 1. Nguyên tắc hoạt động
*   **Tự động tạo:** Khi chuyển bước (VD: Gửi duyệt), hệ thống tạo 1 Activity "To Do" cho người duyệt.
*   **Tự động đóng:** Khi người đó hoàn thành (VD: Bấm nút Duyệt), Activity cũ sẽ được đánh dấu "Done" và tạo Activity mới cho bước sau.
*   **Hiển thị:** Activity hiện số đỏ trên thanh menu và trong khay hệ thống (Systray) như hình bạn gửi.

## 2. Bảng quy hoạch Activity

| Hành động | Chuyển trạng thái | Tạo Activity: **Nội dung** | Giao cho ai? (Assigned To) |
| :--- | :--- | :--- | :--- |
| **Gửi rà soát**<br>(Nhân viên) | `Draft` -> `In Review` | **Yêu cầu rà soát hợp đồng**<br>Deadline: Hôm nay | **Người rà soát**<br>(Cần chọn trươc trên Form hoặc lấy Trưởng bộ phận) |
| **Xác nhận rà soát**<br>(Quản lý) | `In Review` -> `Waiting` | **Yêu cầu phê duyệt**<br>Deadline: +1 ngày | **Giám đốc**<br>(Lấy user đầu tiên trong nhóm *Contract Approver*) |
| **Phê duyệt**<br>(Giám đốc) | `Waiting` -> `Approved` | **Hợp đồng đã duyệt. Tiến hành ký.**<br>Deadline: +2 ngày | **Người tạo** (`user_id`)<br>(Nhân viên phụ trách) |
| **Từ chối**<br>(Giám đốc) | `Waiting` -> `Draft` | **Hợp đồng bị từ chối. Vui lòng sửa.** | **Người tạo** (`user_id`) |
| **Hoàn tất ký**<br>(Nhân viên) | `Signed` -> `Signed` | **Đóng dấu & Lưu kho**<br>Deadline: +1 ngày | **HCNS**<br>(Lấy user đầu tiên trong nhóm *Contract Manager*) |

## 3. Cập nhật kỹ thuật (Technical Plan)

### A. Thêm trường chọn người
*   Cần thêm trường `suggested_reviewer_id` (Người rà soát) ở form (tab Khác hoặc ngay header) để Nhân viên chọn lúc gửi. Nếu không chọn sẽ mặc định lấy Trưởng phòng (dựa trên Employee).

### B. Logic Code (`contract.py`)
Sử dụng hàm `activity_schedule` và `activity_feedback`.

**Ví dụ Logic khi "Gửi rà soát":**
```python
def action_submit_for_review(self):
    # ... logic đổi state ...
    
    # 1. Đánh dấu 'Done' các activity cũ của mình (nếu có)
    self.activity_feedback(['mail.mail_activity_data_todo'])
    
    # 2. Tạo việc mới cho Reviewer
    self.activity_schedule(
        'mail.mail_activity_data_todo', 
        user_id=self.suggested_reviewer_id.id,
        summary='Vui lòng rà soát hợp đồng %s' % self.name,
        date_deadline=fields.Date.context_today(self)
    )
```

### C. Logic Tìm người (Get Users)
*   **Lấy Giám đốc:** `self.env.ref('trasas_contract_management.group_contract_approver').users[0]`
*   **Lấy HCNS:** `self.env.ref('trasas_contract_management.group_contract_manager').users[0]`

## 4. Câu hỏi xác nhận
Bạn có đồng ý với logic gán người như trên không? Đặc biệt là bước **Rà soát**, bạn muốn nhân viên tự chọn người rà soát hay hệ thống tự tìm Trưởng bộ phận?
