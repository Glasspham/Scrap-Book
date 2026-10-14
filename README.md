# 📥 Down & Merge Photos

> A lightweight desktop tool to **batch-download images** from sequential URLs and **merge them into a single PDF** — no fuss, just get the job done.

Built with Python + CustomTkinter. Packages into a portable `.exe` with no installation required for end users.

---

## ✨ Features

| Feature | Details |
|---|---|
| 🌐 **Batch Image Downloader** | Auto-detects image numbering from any URL pattern and downloads all pages from `1` to the end |
| 📄 **Merge to PDF** | Combines all images in a folder into a single, ordered PDF file |
| 🎨 **Modern GUI** | Borderless, draggable window with Dark / Glass theme switcher |
| 💾 **Custom Save Path** | Choose any output folder for downloaded images or generated PDF |
| 🛑 **Stop Anytime** | Interrupt a running download or merge at any time |
| 📝 **File Logging** | Detailed logs saved to `<archive-name>.log` inside the output folder |
| 🖥️ **Taskbar Integration** | Shows up correctly in the Windows taskbar with a custom icon |
| 📦 **Portable EXE** | Packaged with PyInstaller — no Python installation needed |

---

## 📁 Project Structure

```
Scrap-Book/
├── app.py                  # Main GUI application
├── build.bat               # One-click build script (produces .exe)
├── app_icon.ico            # Application icon
├── version_info.txt        # Windows EXE version metadata (company, version, etc.)
├── Terminal/
│   ├── download_images.py  # Standalone CLI script for downloading images
│   └── images_to_pdf.py    # Standalone CLI script for merging images to PDF
└── dist/
    └── Down and Merge Photos.exe   # Built executable (after running build.bat)
```

---

## 🚀 Getting Started

### Option A — Use the Prebuilt EXE *(Recommended for regular users)*

1. Download `Down and Merge Photos.exe` from the [Releases](../../releases) page.
2. Double-click to run — no installation required.

---

### Option B — Run from Source *(For developers)*

**Requirements:** Python 3.10+

```bash
# 1. Clone the repository
git clone https://github.com/Glasspham/Scrap-Book.git
cd Scrap-Book

# 2. Install dependencies
pip install customtkinter requests Pillow fpdf2

# 3. Launch the app
python app.py
```

---

## 🖼️ How to Use the GUI

### ⬇ Download Tab

1. Paste **any image URL** from the series (e.g. `https://example.com/img/5.jpg`).
   > The tool automatically resets to page **1** and downloads all pages until errors occur.
2. Set the **Save folder** where images will be stored.
3. (Optional) Set **End page** to stop at a specific page number.
4. (Optional) Set **Max consecutive errors** before auto-stop (default: 3).
5. Click **⬇ Start Download**.

### 📄 Merge PDF Tab

1. Set the **Image folder** path containing the downloaded images.
2. (Optional) Enter a **PDF file name** (defaults to the folder name).
3. Click **📄 Merge to PDF**.

---

## 💻 CLI Scripts (Terminal Folder)

### `download_images.py`

```bash
python Terminal/download_images.py
```

Prompts you for:
- Image URL (any page in the series)
- Output folder name
- End page number (optional)
- Max consecutive failures (optional)

Logs are saved as `<folder_name>.log` inside the output folder.

---

### `images_to_pdf.py`

```bash
python Terminal/images_to_pdf.py
```

Prompts you for:
- Input folder path (containing images)
- Output PDF file name (optional, defaults to folder name)

---

## 📦 Build EXE

```bash
.\build.bat
```

This will:
1. Install all required dependencies via `pip`
2. Run PyInstaller to bundle everything into a single `.exe`
3. Output to `dist\Down and Merge Photos.exe`

The resulting EXE contains embedded version info (Company: Glass Pham, Version: 1.0.0) and the custom icon.

---

## 🛠️ Tech Stack

| Library | Purpose |
|---|---|
| `customtkinter` | Modern GUI framework (built on top of Tkinter) |
| `requests` | HTTP image downloading |
| `Pillow` | Image processing & PDF export |
| `fpdf2` | PDF generation |
| `PyInstaller` | Packaging into standalone `.exe` |
| `ctypes` | Windows API for borderless window, taskbar icon, transparency |

---

## 👤 Author

**Glass Pham** — [github.com/Glasspham](https://github.com/Glasspham)

---

## 📄 License

This project is for personal use. Feel free to fork and customize.
