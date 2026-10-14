"""
Images to PDF - Ghép toàn bộ ảnh trong folder thành 1 file PDF
Sắp xếp ảnh theo tên file (số thứ tự tự nhiên: 1, 2, 10 thay vì 1, 10, 2)
"""

import re
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("[LỖI] Thiếu thư viện Pillow. Cài bằng lệnh: pip install Pillow")
    sys.exit(1)


# Định dạng ảnh được hỗ trợ
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".tif", ".webp"}


def natural_sort_key(path: Path):
    """Sắp xếp tự nhiên: 1, 2, 3, ..., 10, 11 (thay vì 1, 10, 11, 2, ...)"""
    parts = re.split(r"(\d+)", path.stem.lower())
    return [int(p) if p.isdigit() else p for p in parts]


def images_to_pdf(folder: str, output_name: str = None):
    """
    Ghép tất cả ảnh trong folder thành 1 file PDF.

    Args:
        folder      : Đường dẫn folder chứa ảnh
        output_name : Tên file PDF đầu ra (không cần .pdf, None = dùng tên folder)
    """
    folder_path = Path(folder).resolve()

    if not folder_path.exists():
        print(f"[LỖI] Folder không tồn tại: {folder_path}")
        sys.exit(1)

    if not folder_path.is_dir():
        print(f"[LỖI] Đường dẫn không phải folder: {folder_path}")
        sys.exit(1)

    # Tìm tất cả ảnh trong folder (không đệ quy)
    image_files = sorted(
        [f for f in folder_path.iterdir() if f.suffix.lower() in IMAGE_EXTENSIONS],
        key=natural_sort_key,
    )

    if not image_files:
        print(f"[LỖI] Không tìm thấy ảnh nào trong: {folder_path}")
        print(f"      Hỗ trợ: {', '.join(sorted(IMAGE_EXTENSIONS))}")
        sys.exit(1)

    # Xác định tên file PDF đầu ra
    if output_name:
        pdf_name = output_name if output_name.lower().endswith(".pdf") else output_name + ".pdf"
    else:
        pdf_name = folder_path.name + ".pdf"

    # PDF lưu cùng cấp với folder
    pdf_path = folder_path.parent / pdf_name

    print(f"\n{'='*55}")
    print(f"  Folder    : {folder_path}")
    print(f"  Số ảnh    : {len(image_files)}")
    print(f"  PDF xuất  : {pdf_path}")
    print(f"{'='*55}\n")

    # Load ảnh
    images_rgb = []
    for i, img_file in enumerate(image_files, 1):
        try:
            img = Image.open(img_file)

            # Chuyển sang RGB (PDF không hỗ trợ RGBA, P, LA, ...)
            if img.mode in ("RGBA", "LA", "P"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")

            images_rgb.append(img)
            print(f"  [{i:>4}/{len(image_files)}] {img_file.name}  ({img.width}x{img.height})")

        except Exception as e:
            print(f"  [WARN] Bỏ qua {img_file.name}: {e}")

    if not images_rgb:
        print("\n[LỖI] Không load được ảnh nào.")
        sys.exit(1)

    # Ghép thành PDF
    print(f"\n  Đang tạo PDF...")
    first_img = images_rgb[0]
    rest_imgs = images_rgb[1:]

    first_img.save(
        pdf_path,
        format="PDF",
        save_all=True,
        append_images=rest_imgs,
        resolution=150,
    )

    pdf_size_mb = pdf_path.stat().st_size / (1024 * 1024)
    print(f"\n{'='*55}")
    print(f"  Hoan thanh! Da ghep {len(images_rgb)} anh -> PDF")
    print(f"  File: {pdf_path}")
    print(f"  Kich thuoc: {pdf_size_mb:.2f} MB")
    print(f"{'='*55}\n")


# ─────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) >= 2:
        # Chạy từ dòng lệnh: python images_to_pdf.py <folder> [output_name]
        in_folder   = sys.argv[1]
        out_name    = sys.argv[2] if len(sys.argv) > 2 else None
    else:
        # Chạy thủ công: nhập từ bàn phím
        print("=== Ghep anh thanh PDF ===")
        in_folder = input("Nhap duong dan folder chua anh: ").strip().strip('"')
        out_name  = input("Ten file PDF [Enter de dung ten folder]: ").strip() or None

    images_to_pdf(in_folder, output_name=out_name)
