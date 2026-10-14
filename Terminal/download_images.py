"""
Image Downloader - Tải ảnh theo dãy số từ URL mẫu
Ví dụ URL: https://example.com/img/1.jpg  ->  tải 1.jpg, 2.jpg, 3.jpg, ...
"""

import re
import sys
import logging
import requests
from pathlib import Path
from urllib.parse import urlparse


def parse_url_pattern(url: str):
    """
    Phân tích URL để tìm phần số ở cuối (trước phần mở rộng file).
    Trả về: (base_url, prefix_part, start_number, zero_pad, extension)
    Ví dụ: "https://example.com/img/1.jpg" -> ("https://example.com/img/", "", 1, 0, ".jpg")
    """
    parsed = urlparse(url)
    path = parsed.path  # e.g. /opac/ebooks/.../img/1.jpg

    filename = Path(path).name          # "1.jpg"
    stem = Path(path).stem              # "1"
    suffix = Path(path).suffix          # ".jpg"

    # Tìm số cuối cùng trong stem (có thể có prefix chữ trước số)
    match = re.fullmatch(r"(\D*)(\d+)", stem)
    if not match:
        raise ValueError(
            f"Không tìm thấy số cuối trong tên file '{filename}'.\n"
            "URL phải có dạng: .../prefix123.jpg hoặc .../1.jpg"
        )

    prefix_part = match.group(1)   # phần chữ trước số (có thể rỗng)
    number_part = match.group(2)   # phần số, e.g. "1" hoặc "001"
    zero_pad = len(number_part) if number_part.startswith("0") else 0

    base_url = url[: url.rfind(filename)]

    return base_url, prefix_part, int(number_part), zero_pad, suffix


def build_url(base_url: str, prefix: str, num: int, pad: int, ext: str) -> str:
    num_str = str(num).zfill(pad) if pad else str(num)
    return f"{base_url}{prefix}{num_str}{ext}"


def download_images(url: str, output_dir: str = "downloaded_images",
                    end_num: int = None, max_fail: int = 5):
    """
    Tải tất cả ảnh từ URL mẫu.

    Args:
        url        : URL mẫu chứa số ở cuối, e.g. https://example.com/img/1.jpg
        output_dir : Thư mục lưu ảnh (mặc định: ./downloaded_images)
        end_num    : Số kết thúc (None = tự động dừng khi lỗi liên tiếp)
        max_fail   : Số lần thất bại liên tiếp trước khi dừng (mặc định: 5)
    """
    try:
        base_url, prefix, start_num, zero_pad, ext = parse_url_pattern(url)
    except ValueError as e:
        print(f"[LỖI] {e}")
        sys.exit(1)

    save_dir = Path(output_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    # ── Thiết lập logging ──────────────────────────────────────
    log_file = save_dir / f"{save_dir.name}.log"

    logger = logging.getLogger("downloader")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()  # tránh duplicate nếu gọi lại nhiều lần

    # Handler ghi file: toàn bộ chi tiết
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(asctime)s  %(levelname)-5s  %(message)s",
                                       datefmt="%Y-%m-%d %H:%M:%S"))
    logger.addHandler(fh)

    # Handler terminal: chỉ WARNING trở lên (lỗi quan trọng)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.WARNING)
    ch.setFormatter(logging.Formatter("  [!] %(message)s"))
    logger.addHandler(ch)
    # ──────────────────────────────────────────────────────────

    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": base_url,
    })

    end_label = str(end_num) if end_num is not None else f"tự động (dừng sau {max_fail} lỗi)"
    print(f"\n{'='*55}")
    print(f"  URL mẫu   : {url}")
    print(f"  Base URL  : {base_url}")
    print(f"  Bắt đầu từ: {prefix}1{ext}")
    print(f"  Kết thúc  : {prefix}{end_label}{ext}")
    print(f"  Lưu vào   : {save_dir.resolve()}")
    print(f"  Log file  : {log_file}")
    print(f"{'='*55}\n")

    logger.info("=" * 50)
    logger.info(f"URL mẫu   : {url}")
    logger.info(f"Bắt đầu từ: {prefix}1{ext}")
    logger.info(f"Kết thúc  : {prefix}{end_label}{ext}")
    logger.info(f"Lưu vào   : {save_dir.resolve()}")
    logger.info("=" * 50)

    downloaded = 0
    fail_streak = 0
    num = 1  # Luôn bắt đầu từ 1 dù URL mẫu được nhập ở trang nào

    while True:
        # Dừng nếu đã vượt quá số kết thúc
        if end_num is not None and num > end_num:
            print(f"\n  Đã đến số kết thúc ({end_num}).")
            break

        img_url = build_url(base_url, prefix, num, zero_pad, ext)
        filename = save_dir / f"{prefix}{num}{ext}"

        try:
            resp = session.get(img_url, timeout=15)

            if resp.status_code == 200 and "image" in resp.headers.get("Content-Type", ""):
                filename.write_bytes(resp.content)
                size_kb = len(resp.content) / 1024
                logger.info(f"[OK] {img_url}  ({size_kb:.1f} KB)  -> {filename.name}")
                downloaded += 1
                fail_streak = 0
            elif resp.status_code == 404:
                logger.debug(f"[404] {img_url}")
                fail_streak += 1
            else:
                logger.warning(f"HTTP {resp.status_code}: {img_url}")
                fail_streak += 1

        except requests.exceptions.RequestException as e:
            logger.warning(f"Lỗi kết nối: {img_url} -> {e}")
            fail_streak += 1

        # Chỉ kiểm tra lỗi liên tiếp khi không có số kết thúc cố định
        if end_num is None and fail_streak >= max_fail:
            logger.info(f"Dừng: {max_fail} lần lỗi liên tiếp.")
            break

        num += 1

    # Dừng vì đến số kết thúc
    if end_num is not None and num > end_num:
        logger.info(f"Đã đến số kết thúc ({end_num}).")

    logger.info(f"Hoàn thành! Đã tải: {downloaded} ảnh")
    print(f"\n{'='*55}")
    print(f"  Hoàn thành! Đã tải: {downloaded} ảnh")
    print(f"  Lưu tại : {save_dir.resolve()}")
    print(f"  Log file : {log_file}")
    print(f"{'='*55}\n")


# ─────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) >= 2:
        # Chạy từ dòng lệnh: python download_images.py <url> [output_dir] [end_num] [max_fail]
        input_url = sys.argv[1]
        out_dir   = sys.argv[2] if len(sys.argv) > 2 else "downloaded_images"
        end_n     = int(sys.argv[3]) if len(sys.argv) > 3 else None
        max_f     = int(sys.argv[4]) if len(sys.argv) > 4 else 3
    else:
        # Chạy thủ công: nhập URL từ bàn phím
        print("=== Trinh tai anh theo day so ===")
        input_url = input("Nhap URL mau (e.g. https://example.com/img/1.jpg): ").strip()
        out_dir   = input("Thu muc luu anh [downloaded_images]: ").strip() or "downloaded_images"
        en_input  = input("So ket thuc (Enter de tu dong dung khi loi): ").strip()
        end_n     = int(en_input) if en_input.isdigit() else None
        if end_n is None:
            mf_input = input("So lan loi lien tiep truoc khi dung (def: 3): ").strip()
            max_f    = int(mf_input) if mf_input.isdigit() else 3
        else:
            max_f = 3

    download_images(input_url, output_dir=out_dir, end_num=end_n, max_fail=max_f)
