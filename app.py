"""
Image Down - GUI App
Requires: pip install customtkinter requests Pillow
"""

import re
import sys
import logging
import threading
import webbrowser
import requests
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

import customtkinter as ctk
from tkinter import filedialog, messagebox

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# ───────────────────────────── Theme ──────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

CLR_BG        = "#0f1117"
CLR_PANEL     = "#1a1d27"
CLR_CARD      = "#21253a"
CLR_ACCENT    = "#00c8ff"
CLR_ACCENT2   = "#7b61ff"
CLR_SUCCESS   = "#00e676"
CLR_WARN      = "#ffd740"
CLR_ERROR     = "#ff5252"
CLR_TEXT      = "#e0e6f0"
CLR_SUBTEXT   = "#7a8299"
FONT_BODY     = ("Segoe UI", 13)
FONT_LABEL    = ("Segoe UI", 11)
FONT_TITLE    = ("Segoe UI", 22, "bold")
FONT_MONO     = ("Consolas", 11)
FONT_SMALL    = ("Segoe UI", 10)


# ───────────────────────────── Core logic ─────────────────────────────
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".tif", ".webp"}


def natural_sort_key(path: Path):
    """Sort files by embedded numbers naturally (1, 2, 10 not 1, 10, 2)."""
    parts = re.split(r"(\d+)", path.stem.lower())
    return [int(p) if p.isdigit() else p for p in parts]


def parse_url_pattern(url: str):
    """Extract base URL, prefix, start number, zero-padding and extension from a URL."""
    parsed = urlparse(url)
    path = parsed.path
    filename = Path(path).name
    stem = Path(path).stem
    suffix = Path(path).suffix
    match = re.fullmatch(r"(\D*)(\d+)", stem)
    if not match:
        raise ValueError(f"No number found in filename '{filename}'.")
    prefix_part = match.group(1)
    number_part = match.group(2)
    zero_pad = len(number_part) if number_part.startswith("0") else 0
    base_url = url[: url.rfind(filename)]
    return base_url, prefix_part, int(number_part), zero_pad, suffix


def build_url(base_url, prefix, num, pad, ext):
    """Construct the full URL for a given image number."""
    num_str = str(num).zfill(pad) if pad else str(num)
    return f"{base_url}{prefix}{num_str}{ext}"


# ───────────────────────────── Main App ───────────────────────────────
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Download & Merge Photos")
        self.geometry("780x620")
        self.minsize(700, 560)
        self.configure(fg_color=CLR_BG)

        # Ensure taskbar uses the correct icon
        try:
            import ctypes, sys, os
            myappid = 'glasspham.imagedownloader.1.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            
            # Load bundled icon
            icon_path = "app_icon.ico"
            if hasattr(sys, '_MEIPASS'):
                icon_path = os.path.join(sys._MEIPASS, "app_icon.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception:
            pass

        # Remove OS window border
        self.overrideredirect(True)

        # Round corners on Windows 11
        try:
            from ctypes import windll, c_int, byref, sizeof
            HWND = windll.user32.GetParent(self.winfo_id())
            windll.dwmapi.DwmSetWindowAttribute(HWND, 33, byref(c_int(2)), sizeof(c_int))
        except Exception:
            pass

        # Drag state
        self._drag_x = 0
        self._drag_y = 0

        # Thread state
        self._dl_thread: threading.Thread | None = None
        self._pdf_thread: threading.Thread | None = None
        self._stop_flag = threading.Event()
        self._current_theme = "dark"  # track active theme

        self._build_ui()
        
        # Force window back to taskbar after removing border
        self.after(100, self._restore_taskbar)

    def _restore_taskbar(self):
        """Bring the borderless window back to the Windows taskbar."""
        try:
            from ctypes import windll
            GWL_EXSTYLE = -20
            WS_EX_APPWINDOW = 0x00040000
            WS_EX_TOOLWINDOW = 0x00000080
            hwnd = windll.user32.GetParent(self.winfo_id())
            style = windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            style = style & ~WS_EX_TOOLWINDOW
            style = style | WS_EX_APPWINDOW
            windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
            
            # Trigger Windows to update the taskbar
            self.withdraw()
            self.deiconify()
        except Exception:
            pass

    # ─────────────────────── UI Builder ───────────────────────────────
    def _build_ui(self):
        # ── Custom title bar (draggable) ──────────────────────────────
        self.titlebar = ctk.CTkFrame(self, fg_color=CLR_PANEL, corner_radius=0, height=42)
        self.titlebar.pack(fill="x")
        self.titlebar.pack_propagate(False)
        titlebar = self.titlebar  # local alias

        # App icon + name
        ctk.CTkLabel(
            titlebar, text="Download & Merge Photos",
            font=("Segoe UI", 14, "bold"), text_color=CLR_ACCENT,
        ).pack(side="left", padx=16, pady=8)

        # Window control buttons (right side)
        btn_close = ctk.CTkButton(
            titlebar, text="✕", width=36, height=28,
            fg_color="transparent", hover_color=CLR_ERROR,
            text_color=CLR_SUBTEXT, font=("Segoe UI", 13, "bold"),
            corner_radius=6, command=self.destroy,
        )
        btn_close.pack(side="right", padx=(0, 6), pady=6)

        btn_min = ctk.CTkButton(
            titlebar, text="─", width=36, height=28,
            fg_color="transparent", hover_color=CLR_CARD,
            text_color=CLR_SUBTEXT, font=("Segoe UI", 13, "bold"),
            corner_radius=6, command=self._minimize,
        )
        btn_min.pack(side="right", padx=2, pady=6)

        # Separator
        ctk.CTkFrame(titlebar, fg_color="#2e3450", width=1, height=20).pack(
            side="right", padx=6, pady=10)

        # ── Theme toggle buttons ─────────────────────────────────
        self._theme_btns = {}
        themes = [
            ("dark",  "🌙", "#2a2e45", "#00c8ff"),   # Dark
            ("glass", "🔮", "#3a3060", "#b39ddb"),   # Glass / Transparent
        ]
        for key, icon, bg, fg in themes:
            btn = ctk.CTkButton(
                titlebar, text=icon, width=32, height=26,
                fg_color=bg if key == self._current_theme else "transparent",
                hover_color=bg,
                text_color=fg, font=("Segoe UI", 13),
                corner_radius=6,
                command=lambda k=key: self._set_theme(k),
            )
            btn.pack(side="right", padx=2, pady=7)
            self._theme_btns[key] = (btn, bg, fg)

        # Drag bindings on title bar
        titlebar.bind("<ButtonPress-1>",   self._drag_start)
        titlebar.bind("<B1-Motion>",        self._drag_move)
        for child in titlebar.winfo_children():
            child.bind("<ButtonPress-1>",  self._drag_start)
            child.bind("<B1-Motion>",       self._drag_move)
        # Override drag on buttons so clicking them doesn't trigger drag
        btn_close.bind("<ButtonPress-1>", lambda e: None)
        btn_min.bind("<ButtonPress-1>",   lambda e: None)

        # ── Footer (pinned bottom) ────────────────────────────────────
        self.footer_frame = ctk.CTkFrame(self, fg_color=CLR_PANEL, corner_radius=0, height=26)
        self.footer_frame.pack(fill="x", side="bottom")
        self.footer_frame.pack_propagate(False)
        footer = self.footer_frame  # local alias

        link = ctk.CTkLabel(
            footer, text="Glasspham",
            font=("Segoe UI", 10, "underline"),
            text_color=CLR_SUBTEXT, cursor="hand2",
        )
        link.pack(pady=4)  # centered horizontally
        link.bind("<Button-1>", lambda _: webbrowser.open("https://github.com/Glasspham"))
        link.bind("<Enter>",    lambda _: link.configure(text_color=CLR_ACCENT))
        link.bind("<Leave>",    lambda _: link.configure(text_color=CLR_SUBTEXT))

        # ── Tab view (fills remaining space between titlebar & footer) ─
        self.tabs = ctk.CTkTabview(
            self, fg_color=CLR_PANEL,
            segmented_button_fg_color=CLR_CARD,
            segmented_button_selected_color=CLR_ACCENT,
            segmented_button_selected_hover_color="#009ece",
            segmented_button_unselected_color=CLR_CARD,
            segmented_button_unselected_hover_color="#2a2e45",
            text_color=CLR_TEXT,
            corner_radius=12,
        )
        self.tabs.pack(fill="both", expand=True, padx=12, pady=(4, 4))
        self.tabs.add("⬇  Download")
        self.tabs.add("📄  Merge PDF")

        self._build_download_tab(self.tabs.tab("⬇  Download"))
        self._build_pdf_tab(self.tabs.tab("📄  Merge PDF"))

    # ─────────────────── Window drag support ──────────────────────────
    def _minimize(self):
        """Minimize borderless window using Windows API (iconify doesn't work with overrideredirect)."""
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            ctypes.windll.user32.ShowWindow(hwnd, 6)  # SW_MINIMIZE = 6
        except Exception:
            self.withdraw()  # fallback: just hide window

    def _set_theme(self, mode: str):
        """Switch between dark and glass (translucent) themes."""
        self._current_theme = mode

        # Highlight active button
        for key, (btn, bg, fg) in self._theme_btns.items():
            btn.configure(fg_color=bg if key == mode else "transparent")

        # ALWAYS clear transparentcolor to guarantee NO click-through
        self.wm_attributes("-transparentcolor", "")

        if mode == "dark":
            self.wm_attributes("-alpha", 1.0)
            self.titlebar.configure(fg_color=CLR_BG)
            self.footer_frame.configure(fg_color=CLR_BG)
            self.tabs.configure(fg_color=CLR_BG)
            self.configure(fg_color=CLR_BG)

        elif mode == "glass":
            # Pure alpha transparency - no transparentcolor (that causes click-through)
            GLASS_BG = "#080a10"
            self.titlebar.configure(fg_color=GLASS_BG)
            self.footer_frame.configure(fg_color=GLASS_BG)
            self.tabs.configure(fg_color=GLASS_BG)
            self.configure(fg_color=GLASS_BG)
            # Apply window-level transparency (drag/click still work normally)
            self.wm_attributes("-alpha", 0.5)

    def _drag_start(self, event):
        self._drag_x = event.x_root - self.winfo_x()
        self._drag_y = event.y_root - self.winfo_y()

    def _drag_move(self, event):
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.geometry(f"+{x}+{y}")

    # ─────────────────── Download Tab ─────────────────────────────────
    def _build_download_tab(self, parent):
        pad = {"padx": 20, "pady": 6}

        # URL input
        self._lbl(parent, "Sample URL  (e.g. https://example.com/img/1.jpg)").pack(anchor="w", **pad)
        self.url_entry = self._entry(parent)
        self.url_entry.pack(fill="x", **pad)

        # Output folder
        self._lbl(parent, "Save folder").pack(anchor="w", padx=20, pady=(10, 4))
        row_dir = ctk.CTkFrame(parent, fg_color="transparent")
        row_dir.pack(fill="x", padx=20, pady=2)
        self.dir_entry = self._entry(row_dir, placeholder="Choose or type a path...")
        self.dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            row_dir, text="📁", width=44, height=38,
            fg_color=CLR_CARD, hover_color=CLR_ACCENT2, text_color=CLR_TEXT,
            font=("Segoe UI", 16), corner_radius=8,
            command=self._browse_dl_dir,
        ).pack(side="left")

        # Config row
        row_cfg = ctk.CTkFrame(parent, fg_color="transparent")
        row_cfg.pack(fill="x", padx=20, pady=(10, 4))

        cfg_l = ctk.CTkFrame(row_cfg, fg_color="transparent")
        cfg_l.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self._lbl(cfg_l, "End page  (blank = auto-stop on errors)").pack(anchor="w")
        self.end_entry = self._entry(cfg_l, placeholder="e.g. 150")
        self.end_entry.pack(fill="x", pady=2)

        cfg_r = ctk.CTkFrame(row_cfg, fg_color="transparent")
        cfg_r.pack(side="left", fill="x", expand=True)
        self._lbl(cfg_r, "Max consecutive errors before stopping").pack(anchor="w")
        self.fail_entry = self._entry(cfg_r, placeholder="default: 3")
        self.fail_entry.pack(fill="x", pady=2)

        # Action buttons
        btn_row = ctk.CTkFrame(parent, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(14, 6))
        self.dl_btn = ctk.CTkButton(
            btn_row, text="⬇  Start Download", height=44,
            font=("Segoe UI", 14, "bold"),
            fg_color=CLR_ACCENT2, hover_color="#5a41cf", text_color=CLR_TEXT,
            corner_radius=10, command=self._start_download,
        )
        self.dl_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.dl_stop_btn = ctk.CTkButton(
            btn_row, text="⏹ Stop", height=44, width=100,
            font=FONT_BODY, fg_color="#3a2a2a", hover_color=CLR_ERROR,
            text_color=CLR_TEXT, corner_radius=10,
            command=self._stop_download, state="disabled",
        )
        self.dl_stop_btn.pack(side="left")

        # Log box
        self._lbl(parent, "Log").pack(anchor="w", padx=20, pady=(10, 2))
        self.dl_log = ctk.CTkTextbox(
            parent, font=FONT_MONO,
            fg_color="#0a0d14", text_color="#c0cfdf",
            corner_radius=8, wrap="none", state="disabled",
        )
        self.dl_log.pack(fill="both", expand=True, padx=20, pady=(0, 6))
        self.dl_log.tag_config("ok",    foreground=CLR_SUCCESS)
        self.dl_log.tag_config("warn",  foreground=CLR_WARN)
        self.dl_log.tag_config("error", foreground=CLR_ERROR)
        self.dl_log.tag_config("info",  foreground=CLR_ACCENT)

    # ─────────────────── PDF Tab ──────────────────────────────────────
    def _build_pdf_tab(self, parent):
        pad = {"padx": 20, "pady": 6}

        # Source folder
        self._lbl(parent, "Image folder").pack(anchor="w", **pad)
        row_src = ctk.CTkFrame(parent, fg_color="transparent")
        row_src.pack(fill="x", padx=20, pady=2)
        self.pdf_src_entry = self._entry(row_src, placeholder="Choose a folder...")
        self.pdf_src_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            row_src, text="📁", width=44, height=38,
            fg_color=CLR_CARD, hover_color=CLR_ACCENT2, text_color=CLR_TEXT,
            font=("Segoe UI", 16), corner_radius=8,
            command=self._browse_pdf_src,
        ).pack(side="left")

        # PDF output name
        self._lbl(parent, "Output PDF name  (blank = use folder name)").pack(anchor="w", padx=20, pady=(12, 4))
        self.pdf_name_entry = self._entry(parent, placeholder="e.g. my_book")
        self.pdf_name_entry.pack(fill="x", **pad)

        # Quick-fill from Download tab
        ctk.CTkButton(
            parent, text="← Use folder from Download tab",
            height=32, font=FONT_LABEL,
            fg_color=CLR_CARD, hover_color=CLR_ACCENT2, text_color=CLR_SUBTEXT,
            corner_radius=8, command=self._autofill_pdf_src,
        ).pack(anchor="w", padx=20, pady=(4, 0))

        # Merge button
        self.pdf_btn = ctk.CTkButton(
            parent, text="📄  Merge to PDF", height=44,
            font=("Segoe UI", 14, "bold"),
            fg_color=CLR_ACCENT2, hover_color="#5a41cf", text_color=CLR_TEXT,
            corner_radius=10, command=self._start_pdf,
        )
        self.pdf_btn.pack(fill="x", padx=20, pady=(14, 6))

        # Log box
        self._lbl(parent, "Log").pack(anchor="w", padx=20, pady=(10, 2))
        self.pdf_log = ctk.CTkTextbox(
            parent, font=FONT_MONO,
            fg_color="#0a0d14", text_color="#c0cfdf",
            corner_radius=8, state="disabled",
        )
        self.pdf_log.pack(fill="both", expand=True, padx=20, pady=(0, 6))
        self.pdf_log.tag_config("ok",    foreground=CLR_SUCCESS)
        self.pdf_log.tag_config("warn",  foreground=CLR_WARN)
        self.pdf_log.tag_config("error", foreground=CLR_ERROR)
        self.pdf_log.tag_config("info",  foreground=CLR_ACCENT)

    # ─────────────────── Shared Helpers ───────────────────────────────
    def _lbl(self, parent, text):
        return ctk.CTkLabel(parent, text=text, font=FONT_LABEL, text_color=CLR_SUBTEXT)

    def _entry(self, parent, placeholder=""):
        return ctk.CTkEntry(
            parent, height=38, font=FONT_BODY,
            fg_color=CLR_CARD, border_color="#2e3450",
            text_color=CLR_TEXT, placeholder_text=placeholder,
            placeholder_text_color=CLR_SUBTEXT,
            corner_radius=8,
        )

    def _browse_dl_dir(self):
        d = filedialog.askdirectory(title="Select save folder")
        if d:
            self.dir_entry.delete(0, "end")
            self.dir_entry.insert(0, d)

    def _browse_pdf_src(self):
        d = filedialog.askdirectory(title="Select image folder")
        if d:
            self.pdf_src_entry.delete(0, "end")
            self.pdf_src_entry.insert(0, d)

    def _autofill_pdf_src(self):
        val = self.dir_entry.get().strip()
        if val:
            self.pdf_src_entry.delete(0, "end")
            self.pdf_src_entry.insert(0, val)

    def _log(self, textbox: ctk.CTkTextbox, msg: str, tag: str = ""):
        ts = datetime.now().strftime("%H:%M:%S")
        textbox.configure(state="normal")
        textbox.insert("end", f"[{ts}] {msg}\n", tag)
        textbox.see("end")
        textbox.configure(state="disabled")

    def _clear_log(self, textbox: ctk.CTkTextbox):
        textbox.configure(state="normal")
        textbox.delete("1.0", "end")
        textbox.configure(state="disabled")

    # ─────────────────── Download Logic ───────────────────────────────
    def _start_download(self):
        url     = self.url_entry.get().strip()
        out_dir = self.dir_entry.get().strip()
        end_raw = self.end_entry.get().strip()
        fail_raw= self.fail_entry.get().strip()

        if not url:
            messagebox.showerror("Missing input", "Please enter a sample image URL!")
            return
        if not out_dir:
            messagebox.showerror("Missing input", "Please select a save folder!")
            return

        end_num  = int(end_raw)  if end_raw.isdigit()  else None
        max_fail = int(fail_raw) if fail_raw.isdigit() else 3

        self._stop_flag.clear()
        self._clear_log(self.dl_log)
        self.dl_btn.configure(state="disabled")
        self.dl_stop_btn.configure(state="normal")

        self._dl_thread = threading.Thread(
            target=self._download_worker,
            args=(url, out_dir, end_num, max_fail),
            daemon=True,
        )
        self._dl_thread.start()

    def _stop_download(self):
        self._stop_flag.set()
        self.dl_stop_btn.configure(state="disabled")

    def _download_worker(self, url, out_dir, end_num, max_fail):
        def log(msg, tag=""):
            self.after(0, lambda m=msg, t=tag: self._log(self.dl_log, m, t))

        # Parse URL pattern
        try:
            base_url, prefix, _, zero_pad, ext = parse_url_pattern(url)
        except ValueError as e:
            log(f"URL error: {e}", "error")
            self.after(0, self._dl_done)
            return

        save_dir = Path(out_dir)
        save_dir.mkdir(parents=True, exist_ok=True)

        # Set up file logger
        log_file = save_dir / f"{save_dir.name}.log"
        flogger = logging.getLogger(f"dl_{id(self)}")
        flogger.setLevel(logging.DEBUG)
        flogger.handlers.clear()
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(logging.Formatter(
            "%(asctime)s  %(levelname)-5s  %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        flogger.addHandler(fh)

        # HTTP session
        session = requests.Session()
        session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
            ),
            "Referer": base_url,
        })

        end_label = str(end_num) if end_num else f"auto (max_fail={max_fail})"
        log(f"URL     : {url}", "info")
        log(f"Save to : {save_dir.resolve()}", "info")
        log(f"End at  : {end_label}", "info")
        log("─" * 50)
        flogger.info(f"Start download: {url} | end={end_num} | max_fail={max_fail}")

        downloaded = 0
        fail_streak = 0
        num = 1

        while not self._stop_flag.is_set():
            # Stop if end page reached
            if end_num is not None and num > end_num:
                log(f"Reached end page ({end_num}).", "info")
                break

            img_url  = build_url(base_url, prefix, num, zero_pad, ext)
            filename = save_dir / f"{prefix}{num}{ext}"

            try:
                resp = session.get(img_url, timeout=15)
                if resp.status_code == 200 and "image" in resp.headers.get("Content-Type", ""):
                    filename.write_bytes(resp.content)
                    size_kb = len(resp.content) / 1024
                    log(f"[OK] {filename.name}  ({size_kb:.1f} KB)", "ok")
                    flogger.info(f"[OK] {img_url} ({size_kb:.1f} KB)")
                    downloaded += 1
                    fail_streak = 0
                elif resp.status_code == 404:
                    flogger.debug(f"[404] {img_url}")
                    fail_streak += 1
                else:
                    log(f"HTTP {resp.status_code}: {img_url}", "warn")
                    flogger.warning(f"HTTP {resp.status_code}: {img_url}")
                    fail_streak += 1
            except requests.exceptions.RequestException as e:
                log(f"Connection error: {e}", "error")
                flogger.warning(f"Connection error: {img_url} -> {e}")
                fail_streak += 1

            # Auto-stop when no end_num specified and too many failures
            if end_num is None and fail_streak >= max_fail:
                log(f"Stopped after {max_fail} consecutive errors.", "warn")
                flogger.info(f"Stopped: {max_fail} consecutive errors.")
                break

            num += 1

        if self._stop_flag.is_set():
            log("⏹ Stopped by user.", "warn")

        flogger.info(f"Done: {downloaded} images")
        log("─" * 50)
        log(f"✅ Done! Downloaded {downloaded} images.", "ok")
        log(f"📁 {save_dir.resolve()}", "info")
        log(f"📋 Log: {log_file}", "info")
        self.after(0, self._dl_done)

    def _dl_done(self):
        self.dl_btn.configure(state="normal")
        self.dl_stop_btn.configure(state="disabled")

    # ─────────────────── PDF Logic ────────────────────────────────────
    def _start_pdf(self):
        if not PIL_AVAILABLE:
            messagebox.showerror(
                "Missing library",
                "Please install Pillow first:\n\npip install Pillow",
            )
            return

        src  = self.pdf_src_entry.get().strip()
        name = self.pdf_name_entry.get().strip() or None

        if not src:
            messagebox.showerror("Missing input", "Please select an image folder!")
            return

        self._clear_log(self.pdf_log)
        self.pdf_btn.configure(state="disabled")

        self._pdf_thread = threading.Thread(
            target=self._pdf_worker, args=(src, name), daemon=True,
        )
        self._pdf_thread.start()

    def _pdf_worker(self, src, out_name):
        def log(msg, tag=""):
            self.after(0, lambda m=msg, t=tag: self._log(self.pdf_log, m, t))

        folder_path = Path(src).resolve()
        if not folder_path.is_dir():
            log(f"Folder not found: {folder_path}", "error")
            self.after(0, lambda: self.pdf_btn.configure(state="normal"))
            return

        # Collect and sort image files
        image_files = sorted(
            [f for f in folder_path.iterdir() if f.suffix.lower() in IMAGE_EXTENSIONS],
            key=natural_sort_key,
        )

        if not image_files:
            log("No images found in the selected folder!", "error")
            self.after(0, lambda: self.pdf_btn.configure(state="normal"))
            return

        pdf_name = out_name if out_name else folder_path.name
        if not pdf_name.lower().endswith(".pdf"):
            pdf_name += ".pdf"
        pdf_path = folder_path.parent / pdf_name

        log(f"Folder  : {folder_path}", "info")
        log(f"Images  : {len(image_files)}", "info")
        log(f"Output  : {pdf_path}", "info")
        log("─" * 50)

        # Load and convert images to RGB
        images_rgb = []
        for i, img_file in enumerate(image_files, 1):
            try:
                img = Image.open(img_file)
                if img.mode in ("RGBA", "LA", "P"):
                    bg = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    bg.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
                    img = bg
                elif img.mode != "RGB":
                    img = img.convert("RGB")
                images_rgb.append(img)
                log(f"  [{i:>4}/{len(image_files)}] {img_file.name}  ({img.width}×{img.height})", "ok")
            except Exception as e:
                log(f"  Skipped {img_file.name}: {e}", "warn")

        if not images_rgb:
            log("Could not load any images!", "error")
            self.after(0, lambda: self.pdf_btn.configure(state="normal"))
            return

        # Save PDF
        log("─" * 50)
        log("Merging PDF...", "info")
        try:
            images_rgb[0].save(
                pdf_path, format="PDF", save_all=True,
                append_images=images_rgb[1:], resolution=150,
            )
            size_mb = pdf_path.stat().st_size / (1024 * 1024)
            log(f"✅ Done! {len(images_rgb)} images → PDF", "ok")
            log(f"📄 {pdf_path}  ({size_mb:.2f} MB)", "ok")
        except Exception as e:
            log(f"PDF export error: {e}", "error")

        self.after(0, lambda: self.pdf_btn.configure(state="normal"))


# ───────────────────────────── Entry Point ────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
