# HƯỚNG DẪN SỬ DỤNG PHÂN HỆ QUẢN LÝ TÀI SẢN 

Dưới đây là chi tiết cách thức hoạt động và trải nghiệm của 10 tính năng cốt lõi trong phân hệ Quản lý tài sản (App: Quản lý Tài sản).

---

### 1. Phân loại tài sản (Sử dụng nội bộ / Cho thuê / Thuê ngoài)
*   **Vị trí**: Tab *Thông tin định danh* trên Form tạo mới/chỉnh sửa Tài sản.
*   **Cách thức hoạt động**: 
    *   Trường "Phân loại" chỉ tự động hiện ra khi người dùng chọn Nhóm tài sản là **Nhà cửa/Công trình** hoặc **Máy móc thiết bị Sản xuất**.
    *   Người dùng bung dropdown để chọn 1 trong 3 trạng thái: *Sử dụng nội bộ, Cho thuê, Thuê ngoài*.
    *   Dựa vào phân loại này, hệ thống sẽ giới hạn các nút chức năng. (Ví dụ: "Thuê ngoài" sẽ có nút *Đưa vào sử dụng (Thuê ngoài)*, "Cho thuê" sẽ có nút *Cho thuê trực tiếp*).

### 2. Tự động chuyển State (Trạng thái) & Ẩn đi các thao tác tay dư thừa
*   **Vị trí**: Toàn bộ hệ thống (Chạy ngầm).
*   **Cách thức hoạt động**:
    *   Hệ thống có bộ quét tự động (Cron Job) hoạt động vào mỗi đêm.
    *   Khi Hồ sơ pháp lý (hợp đồng, giấy tờ) sắp hết hạn (trước <X> ngày), hệ thống tự động nhận diện và gửi **Thông báo nhắc việc (Activity)**.
    *   Khi Hợp đồng kết thúc, tài sản tự động nhảy từ *Đang cho thuê* về trạng thái *Kết thúc HĐ*.
    *   **Lợi ích**: Người Quản lý tài sản không cần tự mình đi tìm và bấm nút "Sắp hết hạn" nữa, hệ thống lo hoàn toàn logic chuyển trạng thái trên Statusbar.

### 3. Cơ chế tái ký hợp đồng (Gia hạn HĐ)
*   **Vị trí**: Nút **"Tái ký / Gia hạn"** màu xanh (Chỉ hiện khi tài sản đang ở trạng thái *Sắp hết hạn*).
*   **Cách thức hoạt động**:
    *   Nhấn nút "Tái ký", một cửa sổ Popup hiển thị.
    *   Nhập thông tin hợp đồng mới (Ngày ký, Hiệu lực, Đính kèm file).
    *   Khi nhấn Xác nhận:
        1. Tài sản được chuyển trạng thái ngược trở lại thành **Đang cho thuê / Đang sử dụng**.
        2. Hợp đồng vừa nhập được tự động thêm vào tab **Lịch sử hợp đồng**.
        3. Hệ thống sinh tự động một **Email** báo cáo về việc tài sản vừa được gia hạn thành công (gửi về bộ phận liên quan quản lý).

### 4. Cơ chế "Tái sử dụng" tài sản (Reset bản ghi cho chu kỳ mới)
*   **Vị trí**: Nút **"Tái sử dụng"** (Chỉ hiện khi tài sản ở trạng thái *Hoàn thành* - Kết thúc vòng đời cũ).
*   **Cách thức hoạt động**:
    *   Nhấn nút "Tái sử dụng", popup hiện lên yêu cầu thiết lập Hợp đồng/Phiên sử dụng mới.
    *   Người dùng chọn Đối tác/Khách hàng mới, và thời hạn mới.
    *   **Kết quả**: 
        *   Tài sản giữ nguyên vẹn 100% Mã tài sản, Hồ sơ chứng từ pháp lý, Thông số kích thước/giá trị.
        *   Tài sản đổi Nhà cung cấp/Bộ phận thành thông tin mới anh vừa nhập.
        *   Tài sản reset trạng thái về lại mức **Mới (Draft)** để bắt đầu một quy trình duyệt/sử dụng tiếp theo. 
        *   Hợp đồng mới được lưu vào *Lịch sử hợp đồng*.

### 5. Theo dõi Chi phí Cải tạo tài sản
*   **Vị trí**: Tab **"Chi phí cải tạo"** (Chỉ hiện đối với tài sản nhóm *Nhà cửa/Công trình*).
*   **Cách thức hoạt động**:
    *   Khi tài sản đang trong quá trình "Đang cải tạo", người dùng vào Tab này và nhấn **Thêm dòng**.
    *   Điền đủ 4 thông tin: *Ngày phát sinh, Tên chi phí (VD: Nâng nền kho), Thành tiền, Ghi chú*.
    *   Bên dưới Grid sẽ có dòng Tổng cộng tiền tự động cộng dồn tất cả các khoản chi phí cải tạo lịch sử của mảnh đất/nhà xưởng này.

### 6. Lịch sử Upload File (Ngày Cập Nhật)
*   **Vị trí**: Tab **"Hồ sơ chứng từ"**.
*   **Cách thức hoạt động**:
    *   Trong danh sách các chứng từ đính kèm của 1 tài sản, có thêm cột **"Ngày cập nhật"**.
    *   Mỗi khi có ai đó tải lên file đính kèm/hợp đồng mới vào dòng chứng từ này, hệ thống tự bắt mốc thời gian thực (Real-time update) để Quản lý biết file này mới nộp lên hôm qua hay đã nộp từ năm ngoái.

### 7. Thời gian bảo trì tự động (Tự chuyển State & Cảnh báo)
*   **Vị trí**: Tab **"Quản lý sử dụng"** (Chỉ hiển thị với nhóm *Máy móc thiết bị* và *Thiết bị văn phòng*).
*   **Cách thức hoạt động**:
    *   **Khai báo**: Chọn *Chu kỳ bảo trì* (3, 6, 12 tháng) và chọn *Ngày bảo trì tiếp theo*.
    *   **Tự động hoá**:
        *   Trước ngày bảo trì 7 ngày: Hệ thống đổ 1 cảnh báo (Odoo Activity todo) về cho người phụ trách, nhắc chuẩn bị tài chính/kỹ thuật bảo trì máy.
        *   Đến đúng ngày: Hệ thống tự tước quyền "Đang sử dụng" của tài sản và nhảy nó sang trạng thái màu cam **"Bảo trì định kỳ"**.
    *   **Vòng lặp**: Khi bảo trì xong, nhấn nút *Đưa lại vào sử dụng*, hệ thống tự động cộng dồn +3 (hoặc 6/12) tháng vào trường Ngày bảo trì tiếp theo để lo cho chu kỳ tới.

### 8. Cảnh báo & Highlight trên danh sách Chứng từ
*   **Vị trí**: Giao diện Menu **Hồ sơ Pháp lý**.
*   **Cách thức hoạt động**:
    *   Mở danh sách Chứng từ ra, ngay lập tức nhìn thấy các dòng giấy tờ sắp hoặc đã hết hiệu lực.
    *   Cột **Ngày hết hiệu lực** và **Số ngày còn lại** của chứng từ đó sẽ được làm **in đậm (bold)** và tô màu **ĐỎ** (Quá hạn) hoặc màu **VÀNG CAM** (Sắp tới hạn báo trước 30 ngày).
    *   Bên cạnh dòng cũng có nút Badge màu đỏ/vàng tương ứng. Đồng thời Activity ngầm và Thư điện tử (Email) cũng đã được hệ thống gửi nhắc hạn từ trước.

### 9. View Kanban tài sản theo Tình Trạng
*   **Vị trí**: Màn hình trang chủ của Menu Tab **Tài sản**. Biểu tượng Kanban góc trên bên phải.
*   **Cách thức hoạt động**:
    *   Toàn bộ hàng ngàn Tài sản được rải đều trên một Bảng (Board) có các cột kéo thả là 12 trạng thái (Mới, Đang sử dụng, Sửa chữa, Đang thuê, Hết hạn...).
    *   **Giao diện Thẻ Kanban**: Trên mỗi thẻ vuông của 1 tài sản, ngoài tên và hình ảnh, sẽ có thêm tag màu thể hiện Tình trạng và hiển thị Thời gian mua/ghi nhận tài sản ngay trên mặt thẻ để sếp dễ quan sát tuổi thọ thiết bị.

### 10. Chuyên mục Báo cáo (Group by & Export)
*   **Vị trí**: Menu **Báo cáo**.
*   **Cách thức hoạt động**:
    *   Bao gồm 2 báo cáo chính: *Danh sách tài sản* và *Danh sách chứng từ*.
    *   Để đáp ứng tiêu chuẩn báo cáo trích xuất, giao diện "Danh sách chứng từ" đã được lập trình ép bắt buộc gom nhóm (Group By) theo cấu trúc 3 tầng chuẩn:
        1. Nhóm tài sản lớn 
        2. Tên từng tài sản 
        3. Tình trạng hiệu lực pháp lý (Active / Expired). 
    *   Giao diện hiển thị nhãn chữ rõ ràng (Ví dụ: "Nhà cửa công trình xây dựng" thay vì mã code `nxct`).
    *   **Xuất Excel**: Bấm biểu tượng ⚙️ (Bánh răng) > **Xuất** (Export) > tick chọn các cột cần thiết (hoặc Download tất cả) -> sẽ tải ngay một file Excel hạch toán đúng cấp bậc Parent-Child kể trên dùng báo cáo cho BGĐ.
