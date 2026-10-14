# 📥 Down & Merge Photos

> Công cụ desktop nhẹ để **tải ảnh hàng loạt** từ các URL có đánh số thứ tự và **ghép tất cả thành một file PDF** — đơn giản, nhanh chóng.

Được xây dựng bằng Python + CustomTkinter. Có thể đóng gói thành file `.exe` portable, người dùng không cần cài Python.

---

## ✨ Tính năng

| Tính năng | Mô tả |
|---|---|
| 🌐 **Tải ảnh hàng loạt** | Tự động nhận diện mẫu URL, tải từ trang `1` đến hết |
| 📄 **Ghép ảnh thành PDF** | Gộp tất cả ảnh trong một thư mục thành một file PDF có thứ tự |
| 🎨 **Giao diện hiện đại** | Cửa sổ không viền, kéo thả được, có nút chuyển theme Dark / Glass |
| 💾 **Đường dẫn tùy chỉnh** | Chọn thư mục lưu ảnh và PDF tùy ý |
| 🛑 **Dừng bất cứ lúc nào** | Có thể dừng tải hoặc ghép PDF giữa chừng |
| 📝 **Ghi log ra file** | Log chi tiết được lưu vào `<tên-thư-mục>.log` trong thư mục output |
| 🖥️ **Hiển thị đúng Taskbar** | App xuất hiện trên thanh taskbar với icon riêng |
| 📦 **File EXE portable** | Đóng gói bằng PyInstaller — người dùng không cần cài Python |

---

## 📁 Cấu trúc thư mục

```
Scrap-Book/
├── app.py                  # Ứng dụng GUI chính
├── build.bat               # Script build thành .exe một lần click
├── app_icon.ico            # Icon ứng dụng
├── version_info.txt        # Thông tin metadata EXE (tên cty, phiên bản...)
├── Terminal/
│   ├── download_images.py  # Script CLI tải ảnh (chạy trên terminal)
│   └── images_to_pdf.py    # Script CLI ghép ảnh thành PDF
└── dist/
    └── Down and Merge Photos.exe   # File EXE đã build (sau khi chạy build.bat)
```

---

## 🚀 Hướng dẫn sử dụng

### Cách A — Dùng file EXE có sẵn *(Khuyến nghị cho người dùng thường)*

1. Tải file `Down and Merge Photos.exe` từ trang [Releases](../../releases).
2. Double-click để chạy — không cần cài đặt thêm gì.

---

### Cách B — Chạy từ mã nguồn *(Dành cho lập trình viên)*

**Yêu cầu:** Python 3.10 trở lên

```bash
# 1. Clone repository về máy
git clone https://github.com/Glasspham/Scrap-Book.git
cd Scrap-Book

# 2. Cài thư viện cần thiết
pip install customtkinter requests Pillow fpdf2

# 3. Chạy ứng dụng
python app.py
```

---

## 🖼️ Hướng dẫn dùng giao diện GUI

### ⬇ Tab Download (Tải ảnh)

1. Dán **bất kỳ URL ảnh nào** trong chuỗi vào ô URL (ví dụ: `https://example.com/img/5.jpg`).
   > Công cụ sẽ tự động reset về trang **1** và tải lần lượt đến hết.
2. Chọn **thư mục lưu** ảnh tải về.
3. *(Tùy chọn)* Nhập **trang kết thúc** nếu muốn dừng ở trang cụ thể.
4. *(Tùy chọn)* Nhập **số lỗi liên tiếp tối đa** trước khi dừng tự động (mặc định: 3).
5. Nhấn **⬇ Start Download**.

### 📄 Tab Merge PDF (Ghép PDF)

1. Nhập **đường dẫn thư mục** chứa các ảnh cần ghép.
2. *(Tùy chọn)* Nhập **tên file PDF** đầu ra (mặc định lấy tên thư mục).
3. Nhấn **📄 Merge to PDF**.

---

## 💻 Script CLI (Thư mục Terminal)

### `download_images.py`

```bash
python Terminal/download_images.py
```

Nhập các thông tin khi được hỏi:
- URL ảnh bất kỳ trong chuỗi
- Tên thư mục lưu output
- Trang kết thúc (tùy chọn)
- Số lỗi liên tiếp tối đa (tùy chọn)

Log được lưu vào file `<tên_thư_mục>.log` trong thư mục output.

---

### `images_to_pdf.py`

```bash
python Terminal/images_to_pdf.py
```

Nhập các thông tin khi được hỏi:
- Đường dẫn thư mục chứa ảnh
- Tên file PDF đầu ra (tùy chọn, mặc định lấy tên thư mục)

---

## 📦 Build file EXE

```bash
.\build.bat
```

Script sẽ tự động:
1. Cài các thư viện cần thiết qua `pip`
2. Chạy PyInstaller để đóng gói tất cả thành một file `.exe`
3. Xuất ra tại `dist\Down and Merge Photos.exe`

File EXE được nhúng thông tin bản quyền (Công ty: Glass Pham, Phiên bản: 1.0.0) và icon tùy chỉnh.

---

## 🛠️ Công nghệ sử dụng

| Thư viện | Mục đích |
|---|---|
| `customtkinter` | Framework GUI hiện đại (dựa trên Tkinter) |
| `requests` | Tải ảnh qua HTTP |
| `Pillow` | Xử lý ảnh & xuất PDF |
| `fpdf2` | Tạo file PDF |
| `PyInstaller` | Đóng gói thành file `.exe` standalone |
| `ctypes` | Windows API cho cửa sổ không viền, icon taskbar, hiệu ứng trong suốt |

---

## 👤 Tác giả

**Glass Pham** — [github.com/Glasspham](https://github.com/Glasspham)

---

## 📄 Giấy phép

Dự án này dùng cho mục đích cá nhân. Thoải mái fork và tùy chỉnh theo nhu cầu.
