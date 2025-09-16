# ui_app.py
# The main Tkinter application class, importing pure logic from other modules.

import os, re, math, platform, csv
from datetime import datetime
import statistics as stats

import cv2, numpy as np
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk

from config import OUTPUT_ROOT, LETTERS, CFG
from files_io import parse_answer_key, parse_class_section, ensure_outdir
from ui_widgets import ScrollableToolbar, ScrollableFrame
from omr import warp_page, find_markers, detect_answers, detect_student_id, annotate, grade

class OMRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OMR Scanner — 50 items + Student ID (touch-friendly)")

        # Maximize or near-fullscreen
        try:
            if platform.system() == 'Windows':
                self.root.state('zoomed')
            else:
                self.root.attributes('-zoomed', True)
        except Exception:
            sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
            self.root.geometry(f"{int(sw*0.98)}x{int(sh*0.95)}+0+0")

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.configure(bg='#f8f9fa')

        # Initialize scaling
        self.ui_scale = 1.0

        # Session state
        self.session_date = datetime.now().strftime("%Y-%m-%d")
        self.exam_name = None
        self.key_path = None
        self.key = {}
        self.section_name = None
        self.id_to_name = {}
        ensure_outdir(OUTPUT_ROOT)
        self.session_dir = None
        self._refresh_session_dir()

        # Variables
        self.max_items_var = tk.StringVar(value="50")  # 1..50
        self.detect_every_n = 5  # frames
        self.detect_var = tk.IntVar(value=self.detect_every_n)

        # State
        self.cap = None
        self.preview_running = False
        self.last_frame_bgr = None
        self.last_corners = None
        self.preview_frame_count = 0

        self.pending = None
        self.results = []

        # Build UI
        self._build_appbar()      # top app bar (scrollable)
        self._build_main()        # notebook with panes
        self._build_statusbar()   # bottom sticky bar

        # Apply initial responsive styling + debounced resize
        self._resize_after_id = None
        self._apply_responsive_scaling()
        self.root.bind('<Configure>', self._on_root_configure)

        self.log("💡 Tip: Load an answer key and a class section, pick item count, then scan.")

    # ---------- Responsive scaling ----------
    def _base_size(self):
        return 1500, 950

    def _compute_scale(self):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        bw, bh = self._base_size()
        scale = min(max(sw / bw, 0.7), max(sh / bh, 0.7))
        return max(0.7, min(scale, 1.25))

    def _apply_responsive_scaling(self):
        self.ui_scale = self._compute_scale()
        try:
            self.root.tk.call('tk', 'scaling', self.ui_scale)
        except Exception:
            pass
        self._set_fonts_from_scale(self.ui_scale)
        if hasattr(self, 'appbar'):
            self.appbar.update_idletasks()
        self._redraw_trend_only()

    def _fz(self, base):
        return max(8, int(round(base * self.ui_scale)))

    def _pad(self, *vals):
        return tuple(int(round(v * self.ui_scale)) for v in vals)

    def _set_fonts_from_scale(self, scale):
        style = ttk.Style()

        style.configure('Modern.TFrame', background='#f8f9fa')
        style.configure('Modern.TLabelframe', background='#ffffff', borderwidth=2, relief='solid')
        style.configure('Modern.TLabelframe.Label',
                        font=('Segoe UI', self._fz(12), 'bold'), foreground='#2c3e50')

        # Buttons
        style.configure('Primary.TButton',
                        font=('Segoe UI', self._fz(15), 'bold'),
                        padding=self._pad(18, 12),
                        background='#0d6efd', foreground='black', borderwidth=0, relief='flat')
        style.map('Primary.TButton', background=[('active', '#0b5ed7'), ('pressed', '#0a58ca')])

        style.configure('Success.TButton',
                        font=('Segoe UI', self._fz(15), 'bold'),
                        padding=self._pad(18, 12),
                        background='#28a745', foreground='black', borderwidth=0, relief='flat')
        style.map('Success.TButton', background=[('active', '#1e7e34'), ('pressed', '#155724')])

        style.configure('Warning.TButton',
                        font=('Segoe UI', self._fz(15), 'bold'),
                        padding=self._pad(18, 12),
                        background='#ffc107', foreground='black', borderwidth=0, relief='flat')
        style.map('Warning.TButton', background=[('active', '#e0a800'), ('pressed', '#c69500')])

        style.configure('Danger.TButton',
                        font=('Segoe UI', self._fz(15), 'bold'),
                        padding=self._pad(18, 12),
                        background='#dc3545', foreground='black', borderwidth=0, relief='flat')
        style.map('Danger.TButton', background=[('active', '#bb2d3b'), ('pressed', '#b02a37')])

        # Notebook
        style.configure('Modern.TNotebook', background='#f8f9fa', borderwidth=0)
        style.configure('Modern.TNotebook.Tab',
                        font=('Segoe UI', self._fz(15), 'bold'),
                        padding=self._pad(24, 14),
                        background='#e9ecef', foreground='#495057',
                        borderwidth=0, relief='flat')
        style.map('Modern.TNotebook.Tab', background=[('selected', '#ffffff'), ('active', '#dee2e6')])

        # Treeview
        style.configure('Modern.Treeview',
                        font=('Segoe UI', self._fz(13)),
                        rowheight=max(24, int(34 * self.ui_scale)),
                        background='#ffffff', fieldbackground='#ffffff', foreground='#212529')
        style.configure('Modern.Treeview.Heading',
                        font=('Segoe UI', self._fz(13), 'bold'),
                        background='#e9ecef', foreground='#495057')

        style.configure('Title.TLabel',
                        font=('Segoe UI', self._fz(18), 'bold'),
                        foreground='#2c3e50', background='#f8f9fa')
        style.configure('Status.TLabel',
                        font=('Segoe UI', self._fz(13)),
                        foreground='#6c757d', background='#f8f9fa')

        if hasattr(self, 'combo_max'):
            self.combo_max.configure(font=('Segoe UI', self._fz(15), 'bold'))
            self.combo_max['height'] = max(6, int(10 * self.ui_scale))
        if hasattr(self, 'cam_combo'):
            self.cam_combo.configure(font=('Segoe UI', self._fz(14), 'bold'))
            self.cam_combo['height'] = max(6, int(8 * self.ui_scale))

    def _on_root_configure(self, event):
        try:
            if self._resize_after_id:
                self.root.after_cancel(self._resize_after_id)
        except Exception:
            pass
        self._resize_after_id = self.root.after(120, self._apply_responsive_scaling)

    # ---------- Helpers ----------
    def get_active_items(self):
        try:
            n = int(self.max_items_var.get())
        except Exception:
            n = 50
        return min(50, max(1, n))

    def _make_safe(self, s: str) -> str:
        s = (s or "").strip()
        s = s.replace(os.sep, " ")
        for ch in r'<>:"/\\|?*':
            s = s.replace(ch, " ")
        return re.sub(r"\s+", " ", s).strip() or "Untitled"

    def _unique_dir(self, base_path: str) -> str:
        path = base_path
        i = 2
        while os.path.exists(path):
            path = f"{base_path} ({i})"
            i += 1
        return path

    def _refresh_session_dir(self):
        exam = self._make_safe(self.exam_name or "Exam")
        section = self._make_safe(self.section_name or "Section")
        folder_name = f"{exam} - {section} - {self.session_date}"
        base = os.path.join(OUTPUT_ROOT, folder_name)
        if self.session_dir:
            current_leaf = os.path.basename(self.session_dir)
            if current_leaf.startswith(folder_name):
                ensure_outdir(self.session_dir)
                return
        session_path = self._unique_dir(base)
        ensure_outdir(session_path)
        self.session_dir = session_path
        try:
            readme = os.path.join(self.session_dir, "_session_info.txt")
            with open(readme, "w", encoding="utf-8") as f:
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"Session created: {ts}\nExam: {exam}\nSection: {section}\nDate tag: {self.session_date}\n")
        except Exception:
            pass
####################
    # ---------- Top App Bar ----------
    def _build_appbar(self):
        self.appbar = ScrollableToolbar(self.root)
        self.appbar.pack(side=tk.TOP, fill=tk.X)
        bar = self.appbar.inner

        # FILES GROUP
        files_grp = ttk.Frame(bar, style='Modern.TFrame')
        files_grp.pack(side=tk.LEFT, padx=12, pady=8)

        ttk.Label(files_grp, text="📂 Files", style='Title.TLabel').pack(side=tk.TOP, anchor='w')
        row1 = ttk.Frame(files_grp, style='Modern.TFrame'); row1.pack(side=tk.TOP)
        ttk.Button(row1, text="📄 Answer Key", style='Primary.TButton', command=self.on_load_key)\
            .pack(side=tk.LEFT, padx=(0,8))
        ttk.Button(row1, text="👥 Class Section", style='Primary.TButton', command=self.on_load_section)\
            .pack(side=tk.LEFT)

        info = ttk.Frame(files_grp, style='Modern.TFrame'); info.pack(side=tk.TOP, anchor='w', pady=(6,0))
        self.lbl_exam = ttk.Label(info, text="Exam: —", style='Status.TLabel'); self.lbl_exam.pack(side=tk.LEFT, padx=(0,12))
        self.lbl_section = ttk.Label(info, text="Section: —", style='Status.TLabel'); self.lbl_section.pack(side=tk.LEFT)

        # ITEMS GROUP
        items_grp = ttk.Frame(bar, style='Modern.TFrame'); items_grp.pack(side=tk.LEFT, padx=16, pady=8)
        ttk.Label(items_grp, text="📝 Items", style='Title.TLabel').pack(side=tk.TOP, anchor='w')
        row_items = ttk.Frame(items_grp, style='Modern.TFrame'); row_items.pack(side=tk.TOP)
        self.combo_max = ttk.Combobox(
            row_items, values=[str(i) for i in range(1, 51)],
            textvariable=self.max_items_var, state="readonly", justify="center", width=6
        )
        self.combo_max.pack(side=tk.LEFT)
        ttk.Label(row_items, text=" (1–50)", style='Status.TLabel').pack(side=tk.LEFT, padx=(6,0))

        # CAMERA GROUP
        cam_grp = ttk.Frame(bar, style='Modern.TFrame'); cam_grp.pack(side=tk.LEFT, padx=16, pady=8)
        ttk.Label(cam_grp, text="📹 Camera", style='Title.TLabel').pack(side=tk.TOP, anchor='w')
        cam_row = ttk.Frame(cam_grp, style='Modern.TFrame'); cam_row.pack(side=tk.TOP)
        self.cam_index = tk.StringVar(value="0")
        self.cam_combo = ttk.Combobox(cam_row, width=6, textvariable=self.cam_index,
                                      values=self._probe_cams(), state="readonly", justify='center')
        self.cam_combo.pack(side=tk.LEFT, padx=(0,8))
        self.btn_open = ttk.Button(cam_row, text="▶ Open", style='Primary.TButton', command=self.open_cam)
        self.btn_open.pack(side=tk.LEFT, padx=(0,8))
        self.btn_close = ttk.Button(cam_row, text="⏹ Close", style='Primary.TButton',
                                    command=self.close_cam, state=tk.DISABLED)
        self.btn_close.pack(side=tk.LEFT)

        # SCAN GROUP
        scan_grp = ttk.Frame(bar, style='Modern.TFrame'); scan_grp.pack(side=tk.LEFT, padx=16, pady=8)
        ttk.Label(scan_grp, text="🔍 Scan", style='Title.TLabel').pack(side=tk.TOP, anchor='w')
        scan_row = ttk.Frame(scan_grp, style='Modern.TFrame'); scan_row.pack(side=tk.TOP)
        self.btn_scan = ttk.Button(scan_row, text="📸 Scan", style='Primary.TButton',
                                   command=self.scan_current, state=tk.DISABLED)
        self.btn_scan.pack(side=tk.LEFT, padx=(0,8))
        self.btn_retry = ttk.Button(scan_row, text="↺ Retry", style='Primary.TButton',
                                    command=self.on_retry, state=tk.DISABLED)
        self.btn_retry.pack(side=tk.LEFT, padx=(0,8))
        self.btn_confirm = ttk.Button(scan_row, text="✅ Confirm", style='Primary.TButton',
                                      command=self.on_confirm, state=tk.DISABLED)
        self.btn_confirm.pack(side=tk.LEFT)

        # PERF GROUP (corner detect frequency)
        perf_grp = ttk.Frame(bar, style='Modern.TFrame'); perf_grp.pack(side=tk.LEFT, padx=16, pady=8)
        ttk.Label(perf_grp, text="⚙️ Performance", style='Title.TLabel').pack(side=tk.TOP, anchor='w')
        perf_row = ttk.Frame(perf_grp, style='Modern.TFrame'); perf_row.pack(side=tk.TOP)
        ttk.Label(perf_row, text="Detect every", style='Status.TLabel').pack(side=tk.LEFT, padx=(0,6))
        self.spin_detect = ttk.Spinbox(perf_row, from_=1, to=20, width=4,
                                       textvariable=self.detect_var, wrap=True, justify='center', state='readonly',
                                       command=self._on_detect_change)
        self.spin_detect.pack(side=tk.LEFT)
        ttk.Label(perf_row, text="frames", style='Status.TLabel').pack(side=tk.LEFT, padx=(6,0))

        # EXPORT GROUP
        exp_grp = ttk.Frame(bar, style='Modern.TFrame'); exp_grp.pack(side=tk.LEFT, padx=16, pady=8)
        ttk.Label(exp_grp, text="📤 Export", style='Title.TLabel').pack(side=tk.TOP, anchor='w')
        ttk.Button(exp_grp, text="📊 Results", style='Primary.TButton', command=self.on_export)\
            .pack(side=tk.LEFT, padx=(0,8))
        ttk.Button(exp_grp, text="📈 Statistics", style='Primary.TButton', command=self.on_export_stats)\
            .pack(side=tk.LEFT)

        # LIVE STATUS (compact)
        live_grp = ttk.Frame(bar, style='Modern.TFrame'); live_grp.pack(side=tk.LEFT, padx=24, pady=8)
        score_container = ttk.Frame(live_grp, style='Modern.TFrame'); score_container.pack(side=tk.LEFT, padx=(0,16))
        ttk.Label(score_container, text="SCORE", style='Status.TLabel').pack(side=tk.TOP, anchor='w')
        self.score_var = tk.StringVar(value="—")
        ttk.Label(score_container, textvariable=self.score_var, style='Title.TLabel').pack(side=tk.TOP, anchor='w')

        id_container = ttk.Frame(live_grp, style='Modern.TFrame'); id_container.pack(side=tk.LEFT)
        ttk.Label(id_container, text="STUDENT ID", style='Status.TLabel').pack(side=tk.TOP, anchor='w')
        self.id_var = tk.StringVar(value="-----")
        ttk.Label(id_container, textvariable=self.id_var, style='Title.TLabel').pack(side=tk.TOP, anchor='w')

        ttk.Separator(self.root, orient='horizontal').pack(side=tk.TOP, fill=tk.X)
#############
    def _on_detect_change(self):
        try:
            v = int(self.detect_var.get())
            self.detect_every_n = max(1, min(20, v))
        except Exception:
            pass

    # ---------- Main (Notebook + Panes) ----------
    def _build_main(self):
        self.nb = ttk.Notebook(self.root, style='Modern.TNotebook')
        self.nb.pack(fill=tk.BOTH, expand=True, padx=12, pady=(8, 12))

        # --- Tab: Scan ---
        tab_scan = ttk.Frame(self.nb, style='Modern.TFrame'); self.nb.add(tab_scan, text="📷 Scan")

        # status line inside Scan
        status = ttk.Frame(tab_scan, style='Modern.TFrame', padding=(12, 10)); status.pack(side=tk.TOP, fill=tk.X)
        self.corner_status = tk.StringVar(value="🔴 Corners: Not detected")
        ttk.Label(status, textvariable=self.corner_status, style='Status.TLabel').pack(side=tk.LEFT)

        # PanedWindow: left preview | right annotated (user-resizable)
        paned = ttk.Panedwindow(tab_scan, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        left = ttk.Labelframe(paned, text="📹 Camera Preview", style='Modern.TLabelframe', padding=10)
        right = ttk.Labelframe(paned, text="🔍 Annotated View", style='Modern.TLabelframe', padding=10)

        self.preview_label = tk.Label(left, bg="#1e1e1e", fg="#ffffff", relief='solid', bd=1,
                                      text="📹 Preview")
        self.preview_label.pack(fill=tk.BOTH, expand=True)

        self.annot_label = tk.Label(right, bg="#1e1e1e", fg="#ffffff", relief='solid', bd=1,
                                    text="🔍 Annotated")
        self.annot_label.pack(fill=tk.BOTH, expand=True)

        paned.add(left, weight=1)
        paned.add(right, weight=1)

        # Red target overlay rectangles — half-size squares
        m = 0.06
        s = 0.06  # half of original 0.12
        self.target_rects_rel = [
            (m,         m,         m+s,     m+s),     # top-left
            (1-m-s,     m,         1-m,     m+s),     # top-right
            (1-m-s,     1-m-s,     1-m,     1-m),     # bottom-right
            (m,         1-m-s,     m+s,     1-m),     # bottom-left
        ]

        
        # --- Tab: Scores ---
        tab_scores = ttk.Frame(self.nb, style='Modern.TFrame'); self.nb.add(tab_scores, text="📊 Scores")
        scores_sf = ScrollableFrame(tab_scores)
        scores_sf.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        scores_root = scores_sf.body  # put all Scores widgets into this frame

        top = ttk.Frame(scores_root, style='Modern.TFrame', padding=(12, 10)); top.pack(side=tk.TOP, fill=tk.X)
        ttk.Button(top, text="🔄 Refresh", style='Primary.TButton', command=self.refresh_scores).pack(side=tk.LEFT)
        hist = ttk.Frame(top, style='Modern.TFrame'); hist.pack(side=tk.LEFT, padx=16)
        ttk.Label(hist, text="SCANNED", style='Status.TLabel').pack(anchor='w')
        self.lbl_count = ttk.Label(hist, text="0", style='Title.TLabel'); self.lbl_count.pack(anchor='w')
        low = ttk.Frame(top, style='Modern.TFrame'); low.pack(side=tk.LEFT, padx=16)
        ttk.Label(low, text="LOWEST", style='Status.TLabel').pack(anchor='w')
        self.lbl_lowest = ttk.Label(low, text="—", style='Title.TLabel'); self.lbl_lowest.pack(anchor='w')
        self.lbl_lowest_names = ttk.Label(low, text="", style='Status.TLabel'); self.lbl_lowest_names.pack(anchor='w')
        high = ttk.Frame(top, style='Modern.TFrame'); high.pack(side=tk.LEFT, padx=16)
        ttk.Label(high, text="HIGHEST", style='Status.TLabel').pack(anchor='w')
        self.lbl_highest = ttk.Label(high, text="—", style='Title.TLabel'); self.lbl_highest.pack(anchor='w')
        self.lbl_highest_names = ttk.Label(high, text="", style='Status.TLabel'); self.lbl_highest_names.pack(anchor='w')

        cols = ("#", "Student Name", "Student ID", "Score", "Max")
        self.tree_scores = ttk.Treeview(scores_root, columns=cols, show="headings", height=14, style='Modern.Treeview')
        for c, w in zip(cols, (60, 360, 180, 140, 100)):
            self.tree_scores.heading(c, text=c)
            self.tree_scores.column(c, width=w, anchor=tk.CENTER if c in ("#","Student ID","Score","Max") else tk.W)
        self.tree_scores.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        
        # --- Tab: Statistics ---
        tab_stats = ttk.Frame(self.nb, style='Modern.TFrame'); self.nb.add(tab_stats, text="📈 Statistics")
        stats_sf = ScrollableFrame(tab_stats)
        stats_sf.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        stats_root = stats_sf.body  # place all Stats widgets here

        box_top = ttk.Frame(stats_root, style='Modern.TFrame', padding=(12, 10)); box_top.pack(side=tk.TOP, fill=tk.X)
        ttk.Button(box_top, text="🔄 Recompute", style='Primary.TButton', command=self.refresh_stats).pack(side=tk.LEFT)
        ttk.Button(box_top, text="💾 Export Statistics", style='Primary.TButton', command=self.on_export_stats).pack(side=tk.LEFT, padx=(10, 0))

        stats_frame = ttk.Labelframe(stats_root, text="📊 Summary Statistics", style='Modern.TLabelframe', padding=12)
        stats_frame.pack(side=tk.TOP, fill=tk.X, padx=12, pady=(8, 6))
        mean_frame = ttk.Frame(stats_frame, style='Modern.TFrame'); mean_frame.pack(side=tk.LEFT, padx=(0, 24))
        ttk.Label(mean_frame, text="MEAN", style='Status.TLabel').pack(anchor='w')
        self.stat_mean = tk.StringVar(value="—"); ttk.Label(mean_frame, textvariable=self.stat_mean, style='Title.TLabel').pack(anchor='w')
        median_frame = ttk.Frame(stats_frame, style='Modern.TFrame'); median_frame.pack(side=tk.LEFT, padx=(0, 24))
        ttk.Label(median_frame, text="MEDIAN", style='Status.TLabel').pack(anchor='w')
        self.stat_median = tk.StringVar(value="—"); ttk.Label(median_frame, textvariable=self.stat_median, style='Title.TLabel').pack(anchor='w')
        mode_frame = ttk.Frame(stats_frame, style='Modern.TFrame'); mode_frame.pack(side=tk.LEFT)
        ttk.Label(mode_frame, text="MODE", style='Status.TLabel').pack(anchor='w')
        self.stat_mode = tk.StringVar(value="—"); ttk.Label(mode_frame, textvariable=self.stat_mode, style='Title.TLabel').pack(anchor='w')

        trend_frame = ttk.Labelframe(stats_root, text="📈 Score Trend (Scan Order)", style='Modern.TLabelframe', padding=12)
        trend_frame.pack(side=tk.TOP, fill=tk.X, padx=12, pady=6)
        ########
        self.trend_canvas = tk.Canvas(trend_frame, height=260, bg="#0F0E47", highlightthickness=0, relief='flat')
        #########
        self.trend_canvas.pack(fill=tk.X, padx=6, pady=6)
        self.trend_canvas.bind("<Configure>", lambda e: self._redraw_trend_only())

        item_frame = ttk.Labelframe(stats_root, text="🔍 Item Analysis (% Correct)", style='Modern.TLabelframe', padding=12)
        item_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=12, pady=(6, 12))
        self.tree_items = ttk.Treeview(item_frame, columns=("Item", "% Correct", "Correct (n)"),
                                       show="headings", height=12, style='Modern.Treeview')
        for col, w, anchor in (("Item", 120, tk.CENTER), ("% Correct", 180, tk.CENTER), ("Correct (n)", 180, tk.CENTER)):
            self.tree_items.heading(col, text=col)
            self.tree_items.column(col, width=w, anchor=anchor)
        self.tree_items.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # ---------- Bottom Status Bar ----------

    def _build_statusbar(self):
        bar = ttk.Frame(self.root, style='Modern.TFrame')
        bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.log_var = tk.StringVar(value="")
        ttk.Label(bar, textvariable=self.log_var, style='Status.TLabel').pack(side=tk.LEFT, padx=12, pady=6)

    # ---------- Camera ----------
    def _probe_cams(self):
        found = []
        for i in range(6):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW) if os.name=='nt' else cv2.VideoCapture(i)
            ok = cap.isOpened()
            if ok:
                found.append(str(i))
            cap.release()
        return found if found else ["0"]

    def open_cam(self):
        idx = int(self.cam_index.get() or "0")
        self.cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW) if os.name=='nt' else cv2.VideoCapture(idx)
        if not self.cap or not self.cap.isOpened():
            messagebox.showerror("Camera", f"Cannot open camera index {idx}")
            self.cap = None; return
        self.preview_running = True
        self.btn_open.config(state=tk.DISABLED)
        self.btn_close.config(state=tk.NORMAL)
        self.btn_scan.config(state=tk.NORMAL)
        self.log(f"Camera opened. Saving to: {self.session_dir}")
        self._loop_preview()

    def close_cam(self):
        self.preview_running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        self.btn_open.config(state=tk.NORMAL)
        self.btn_close.config(state=tk.DISABLED)
        self.btn_scan.config(state=tk.DISABLED)
        self.preview_label.config(image="", text="📹 Preview")
        self.corner_status.set("🔴 Corners: Not detected")
        self.last_corners = None
        self.log("Camera closed.")

    def _loop_preview(self):
        if not self.preview_running or not self.cap:
            return
        ok, frame = self.cap.read()
        if ok:
            self.last_frame_bgr = frame
            self.preview_frame_count += 1
            # Adjustable detection frequency
            if self.preview_frame_count % max(1, int(self.detect_every_n)) == 0:
                try:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    corners = find_markers(gray)
                    self.last_corners = corners
                    self.corner_status.set("🟢 Corners: Detected ✓")
                except Exception:
                    self.last_corners = None
                    self.corner_status.set("🔴 Corners: Not detected")
            disp = self._draw_corner_overlay(frame.copy(), self.last_corners)
            self._show_bgr_on_label(disp, self.preview_label)
        self.root.after(20, self._loop_preview)

    def _draw_corner_overlay(self, bgr, corners_np):
        h, w = bgr.shape[:2]
        have_corners = corners_np is not None and len(corners_np)==4
        box_color = (0,255,0) if have_corners else (0,0,255)
        dot_color = (0,255,0)
        for (x0r,y0r,x1r,y1r) in self.target_rects_rel:
            x0, y0 = int(x0r*w), int(y0r*h)
            x1, y1 = int(x1r*w), int(y1r*h)
            cv2.rectangle(bgr, (x0,y0), (x1,y1), box_color, 2)
            overlay = bgr.copy()
            cv2.rectangle(overlay, (x0,y0), (x1,y1), box_color, -1)
            bgr = cv2.addWeighted(overlay, 0.08, bgr, 0.92, 0)
        if have_corners:
            for (x,y) in corners_np.astype(int):
                cv2.circle(bgr, (int(x),int(y)), 8, dot_color, -1)
            tl,tr,br,bl = corners_np.astype(int)
            cv2.polylines(bgr, [np.array([tl,tr,br,bl,tl])], False, (0,255,0), 2)
        return bgr

    def _show_bgr_on_label(self, bgr, widget):
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        w = max(widget.winfo_width(), 480)
        h = max(widget.winfo_height(), 360)
        ih, iw = rgb.shape[:2]
        scale = min(w/iw, h/ih)
        new_w, new_h = max(1,int(iw*scale)), max(1,int(ih*scale))
        resized = cv2.resize(rgb, (new_w, new_h), interpolation=cv2.INTER_AREA)
        im = Image.fromarray(resized)
        imgtk = ImageTk.PhotoImage(image=im)
        widget.imgtk = imgtk
        widget.configure(image=imgtk)

    # ---------- File loaders ----------
    def on_load_key(self):
        path = filedialog.askopenfilename(title="Select answer key",
                                          filetypes=[("Text files","*.txt"),("All files","*.*")],
                                          initialdir=self.session_dir)
        if not path:
            return
        exam, key = parse_answer_key(path)
        if not exam or not key:
            messagebox.showwarning("Answer Key", "File parsed, but exam name or items look empty.")
        self.exam_name = exam or "(Unnamed Exam)"
        self.key_path = path
        self.key = key
        self.lbl_exam.config(text=f"Exam: {self.exam_name}")
        if key:
            try:
                self.max_items_var.set(str(min(50, max(key.keys()))))
                if hasattr(self, "combo_max"):
                    self.combo_max.set(self.max_items_var.get())
            except ValueError:
                pass
        self._refresh_session_dir()
        self.log(f"Loaded answer key: {os.path.basename(path)} ({len(key)} items)\nSession: {self.session_dir}")

    def on_load_section(self):
        path = filedialog.askopenfilename(title="Select class section",
                                          filetypes=[("Text files","*.txt"),("All files","*.*")],
                                          initialdir=self.session_dir)
        if not path:
            return
        section, id2name = parse_class_section(path)
        if not section:
            messagebox.showwarning("Class Section", "Section name missing (first non-empty line).")
        self.section_name = section or "(Unnamed Section)"
        self.id_to_name = id2name
        self.lbl_section.config(text=f"Section: {self.section_name}")
        self._refresh_session_dir()
        self.log(f"Loaded section: {self.section_name} ({len(id2name)} students)\nSession: {self.session_dir}")

    # ---------- Scan flow ----------
    def scan_current(self):
        if not (self.exam_name and self.key):
            messagebox.showerror("Setup Required",
                                 "Please load the Answer Key (quiz name) before scanning.\n\nApp Bar → 📄 Answer Key")
            return
        if not (self.section_name and self.id_to_name):
            messagebox.showerror("Setup Required",
                                 "Please load the Class Section before scanning.\n\nApp Bar → 👥 Class Section")
            return
        if self.last_frame_bgr is None:
            messagebox.showwarning("Scan", "No frame available. Open camera first.")
            return

        N = self.get_active_items()

        frame = self.last_frame_bgr.copy()
        try:
            warped = warp_page(frame)
        except Exception as e:
            messagebox.showerror(
                "Warp/Markers",
                "Failed to detect page corners. Align the 4 black squares with the green targets.\n\n"
                f"Details: {e}"
            )
            return

        gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
        answers, centers, r = detect_answers(gray, CFG)
        student_id, id_cols, r_id = detect_student_id(gray, CFG)

        annotated = annotate(
            warped, centers, r, answers, key=self.key,
            mark_blanks=bool(CFG.get("mark_blanks", True)),
            id_cols=id_cols, r_id=r_id, limit_items=N
        )

        score = grade(answers, self.key, limit_items=N)

        self._show_bgr_on_label(annotated, self.annot_label)
        self.id_var.set(f"{student_id if student_id else '-----'}")
        self.score_var.set(f"{score}/{N}")

        self.pending = {
            'warped': warped,
            'annotated': annotated,
            'answers': answers[:N],
            'student_id': student_id,
            'score': score,
            'total_items': N,
        }
        self.btn_retry.config(state=tk.NORMAL)
        self.btn_confirm.config(state=tk.NORMAL)
        self.log("Review the annotated view, then Confirm to save.")

    def on_retry(self):
        self.pending = None
        self._show_placeholder_annot()
        self.score_var.set("—")
        self.id_var.set("-----")
        self.btn_retry.config(state=tk.DISABLED)
        self.btn_confirm.config(state=tk.DISABLED)
        self.log("Retry: discard pending scan and rescan.")

    def on_confirm(self):
        if not self.pending:
            return
        data = self.pending

        # Duplicate Student ID protection
        student_id = data.get('student_id') or ""
        if student_id and any(r.get('student_id') == student_id for r in self.results):
            messagebox.showerror(
                "Duplicate Student ID",
                f"Student ID {student_id} has already been scanned in this session."
            )
            return

        self.pending = None

        # Save annotated image & CSV row into session directory
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = f"scan_{ts}"
        ensure_outdir(self.session_dir)
        out_img = os.path.join(self.session_dir, f"{base}.png")
        cv2.imwrite(out_img, data['annotated'])
        csv_path = os.path.join(self.session_dir, "results.csv")

        answers = data['answers']
        score = data['score']
        total_items = data['total_items']  # N at scan time
        student_name = self.id_to_name.get(student_id, "(Unknown)") if student_id else "(Unknown)"

        header = ["timestamp","filename","exam","section","student_name","student_id","score","max"] + [f"Q{i:02d}" for i in range(1,total_items+1)]
        row = [ts, base, self.exam_name or "", self.section_name or "", student_name, student_id, score, total_items]
        letters = [LETTERS[a] if isinstance(a,int) and a>=0 else "-" for a in answers]
        row.extend(letters[:total_items])
        new_file = not os.path.exists(csv_path)
        with open(csv_path, "a", newline="", encoding='utf-8') as f:
            w = csv.writer(f)
            if new_file:
                w.writerow(header)
            w.writerow(row)

        self.results.append({
            'timestamp': ts,
            'filename': base,
            'exam': self.exam_name or "",
            'section': self.section_name or "",
            'student_name': student_name,
            'student_id': student_id,
            'score': score,
            'max': total_items,
            'answers': answers[:total_items],
        })

        self.refresh_scores()
        self.refresh_stats()
        self.btn_retry.config(state=tk.DISABLED)
        self.btn_confirm.config(state=tk.DISABLED)
        self.log(f"Saved image: {out_img} • Logged to results.csv")

    def _show_placeholder_annot(self):
        ph = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(ph, "Annotated view", (20,240), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (200,200,200), 2, cv2.LINE_AA)
        self._show_bgr_on_label(ph, self.annot_label)

    # ---------- Scores tab ----------
    def refresh_scores(self):
        for it in self.tree_scores.get_children():
            self.tree_scores.delete(it)
        for i, r in enumerate(self.results, start=1):
            self.tree_scores.insert('', 'end', values=(i, r['student_name'], r['student_id'], r['score'], r['max']))
        self.lbl_count.config(text=f"{len(self.results)}")

        # Lowest / Highest with names
        if not self.results:
            self.lbl_lowest.config(text="—"); self.lbl_highest.config(text="—")
            self.lbl_lowest_names.config(text=""); self.lbl_highest_names.config(text="")
            return
        scores = [r['score'] for r in self.results if isinstance(r['score'], (int, float))]
        if not scores:
            self.lbl_lowest.config(text="—"); self.lbl_highest.config(text="—")
            self.lbl_lowest_names.config(text=""); self.lbl_highest_names.config(text=""); return
        mn, mx = min(scores), max(scores)
        min_names = [r['student_name'] for r in self.results if r.get('score') == mn]
        max_names = [r['student_name'] for r in self.results if r.get('score') == mx]
        self.lbl_lowest.config(text=str(mn)); self.lbl_highest.config(text=str(mx))
        def _fmt(names, limit=3):
            return ", ".join(names) if len(names)<=limit else ", ".join(names[:limit]) + f" (+{len(names)-limit} more)"
        self.lbl_lowest_names.config(text=_fmt(min_names))
        self.lbl_highest_names.config(text=_fmt(max_names))

    # ---------- Statistics tab ----------
    def _redraw_trend_only(self):
        scores = [r['score'] for r in self.results if isinstance(r['score'], (int, float))]
        maxv = self.get_active_items() if self.results else 50
        self.draw_trend(scores, maxv)

    def refresh_stats(self):
        scores = [r['score'] for r in self.results if isinstance(r['score'], (int,float))]
        maxv = self.get_active_items() if self.results else 50
        if scores:
            try:
                mean = sum(scores)/len(scores)
                median = stats.median(scores)
                mode = stats.mode(scores)
            except stats.StatisticsError:
                mode = "—"; median = stats.median(scores); mean = sum(scores)/len(scores)
            self.stat_mean.set(f"{mean:.2f}")
            self.stat_median.set(f"{median}")
            self.stat_mode.set(f"{mode}")
        else:
            self.stat_mean.set("—"); self.stat_median.set("—"); self.stat_mode.set("—")

        if (self.trend_canvas.winfo_width() or 0) <= 1:
            self.root.after(50, self._redraw_trend_only)
        else:
            self.draw_trend(scores, maxv)

        self.fill_item_analysis(self.get_active_items())

    def draw_trend(self, scores, maxv):
        c = self.trend_canvas
        c.delete('all')
        w = max(c.winfo_width(), c.winfo_reqwidth(), 480)
        h = max(c.winfo_height(), c.winfo_reqheight(), 220)
        PAD_L, PAD_R, PAD_T, PAD_B = 68, 26, 24, 44
        plot_w = max(1, w - PAD_L - PAD_R)
        plot_h = max(1, h - PAD_T - PAD_B)
        c.create_rectangle(0, 0, w, h, fill="#f8f9fa", outline="")
        c.create_line(PAD_L, h - PAD_B, w - PAD_R, h - PAD_B, fill="#8686AC", width=2)
        c.create_line(PAD_L, h - PAD_B, PAD_L, PAD_T, fill="#8686AC", width=2)
        if not scores:
            c.create_text(w//2, h//2, text="📊 No data yet", fill="#6c757d", font=('Segoe UI', 16)); return
        n = len(scores)
        y_min, y_max = 0, max(1, maxv if maxv else max(scores))
        def _nice_ticks(vmax, lines=5):
            if vmax <= 0: return [0, 1]
            raw = vmax / lines
            mag = 10 ** int(math.floor(math.log10(raw)))
            nice_mul = [1, 2, 2.5, 5, 10]
            step = min(nice_mul, key=lambda m: abs(raw - m*mag)) * mag
            k = int(math.ceil(vmax / step))
            return [i*step for i in range(k+1)]
        yticks = _nice_ticks(y_max, lines=5)
        def mapx(i):
            if n == 1: return PAD_L + plot_w / 2
            return PAD_L + (i / (n - 1)) * plot_w
        def mapy(s):
            rng = max(1e-6, y_max - y_min)
            return h - PAD_B - ((s - y_min) / rng) * plot_h
        for val in yticks:
            y = mapy(val)
            c.create_line(PAD_L, y, w - PAD_R, y, fill="#505081", width=1)
            c.create_text(PAD_L - 10, y, text=f"{int(val)}", anchor="e", fill="#8686AC", font=('Segoe UI', 12))
        xtick_count = min(10, n)
        if xtick_count > 1:
            step = (n - 1) / (xtick_count - 1)
            for j in range(xtick_count):
                i = int(round(j * step))
                x = mapx(i)
                c.create_line(x, h - PAD_B, x, h - PAD_B + 4, fill="#6c757d", width=1)
                c.create_text(x, h - PAD_B + 16, text=str(i + 1), anchor="n", fill="#6c757d", font=('Segoe UI', 12))
        max_segments = max(10, int(plot_w))
        idxs = list(range(n))
        if n > max_segments:
            stride = int(math.ceil(n / max_segments))
            idxs = list(range(0, n, stride))
            if idxs[-1] != n - 1:
                idxs.append(n - 1)
        density = len(idxs)
        line_w = 4 if density < 200 else 3
        r_outer = 6 if density < 200 else 3
        r_inner = 3 if density < 200 else 2
        pts = [(mapx(i), mapy(scores[i])) for i in idxs]
        for i in range(1, len(pts)):
            x0, y0 = pts[i - 1]; x1, y1 = pts[i]
            c.create_line(x0, y0, x1, y1, fill="#8686AC", width=line_w, capstyle=tk.ROUND)
        if density <= 600:
            for (x, y) in pts:
                c.create_oval(x - r_outer, y - r_outer, x + r_outer, y + r_outer,
                                outline="#505081", fill="#0F0E47", width=2)
                c.create_oval(x - r_inner, y - r_inner, x + r_inner, y + r_inner,
                                outline="", fill="#8686AC")
        latest = scores[-1]; best = max(scores)
        x_latest, y_latest = mapx(n - 1), mapy(latest)
        x_best, y_best = mapx(scores.index(best)), mapy(best)
        
        def tag(x, y, text, fill="#272757"):
            padding = 6
            txt = c.create_text(x, y, text=text, anchor="sw", font=('Segoe UI', 12, 'bold'), fill="#8686AC")
            bx, by, bx2, by2 = c.bbox(txt); c.delete(txt)
            c.create_rectangle(bx - padding, by - padding, bx2 + padding, by2 + padding, fill=fill, outline=fill)
            c.create_text(x, y, text=text, anchor="sw", font=('Segoe UI', 12, 'bold'), fill="#8686AC")
        tag(x_latest, y_latest - 10, f" Latest: {latest}", fill="#22c55e")
        if best == latest: tag(x_best, y_best - 30, " Best ✓", fill="#16a34a")
        else:              tag(x_best, y_best - 10, f" Best: {best}", fill="#16a34a")

    def fill_item_analysis(self, total_items):
        for it in self.tree_items.get_children():
            self.tree_items.delete(it)
        if not self.results or not self.key:
            return
        count = [0]*total_items
        n = len(self.results)
        for r in self.results:
            ans = r['answers']
            for i in range(total_items):
                a = ans[i] if i < len(ans) else -1
                k = self.key.get(i+1, None)
                if k is not None and a == k:
                    count[i] += 1
        for i in range(total_items):
            pc = (100.0 * count[i] / n) if n>0 else 0.0
            self.tree_items.insert('', 'end', values=(i+1, f"{pc:.1f}%", count[i]))

    # ---------- Export (results & statistics) ----------
    def on_export(self):
        if not self.results:
            messagebox.showinfo("Export", "No results to export yet.")
            return
        session_items = max((r['max'] for r in self.results), default=self.get_active_items())
        qcols = [f"Q{i:02d}" for i in range(1, session_items+1)]
        safe_section = (self.section_name or "Section").strip().replace(os.sep, ' ').replace(':','-')
        safe_exam = (self.exam_name or "Exam").strip().replace(os.sep, ' ').replace(':','-')
        base = f"{safe_section} - {safe_exam}"
        try:
            import pandas as pd
            rows = []
            for r in self.results:
                rec = {
                    'timestamp': r['timestamp'], 'exam': r['exam'], 'section': r['section'],
                    'student_name': r['student_name'], 'student_id': r['student_id'],
                    'score': r['score'], 'max': r['max'],
                }
                for i in range(session_items):
                    a = r['answers'][i] if i < len(r['answers']) else -1
                    rec[qcols[i]] = LETTERS[a] if isinstance(a,int) and a>=0 else '-'
                rows.append(rec)
            df = pd.DataFrame(rows)
            out_path = filedialog.asksaveasfilename(title="Export to Excel",
                                                    defaultextension=".xlsx",
                                                    initialfile=f"{base}.xlsx",
                                                    initialdir=self.session_dir,
                                                    filetypes=[("Excel","*.xlsx"),("All","*.*")])
            if not out_path: return
            df.to_excel(out_path, index=False)
            messagebox.showinfo("Export", f"Exported to Excel:\n{out_path}")
            return
        except Exception:
            pass
        out_path = filedialog.asksaveasfilename(title="Export to CSV (fallback)",
                                                defaultextension=".csv",
                                                initialfile=f"{base}.csv",
                                                initialdir=self.session_dir,
                                                filetypes=[("CSV","*.csv"),("All","*.*")])
        if not out_path: return
        with open(out_path, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            header = ['timestamp','exam','section','student_name','student_id','score','max'] + qcols
            w.writerow(header)
            for r in self.results:
                row = [r['timestamp'], r['exam'], r['section'], r['student_name'], r['student_id'], r['score'], r['max']]
                for i in range(session_items):
                    a = r['answers'][i] if i < len(r['answers']) else -1
                    row.append(LETTERS[a] if isinstance(a,int) and a>=0 else '-')
                w.writerow(row)
        messagebox.showinfo("Export", f"Exported to CSV:\n{out_path}")

    def on_export_stats(self):
        if not self.results:
            messagebox.showinfo("Export Statistics", "No results to export yet.")
            return

        total_items = self.get_active_items()
        scores = [r['score'] for r in self.results if isinstance(r['score'], (int, float))]
        safe_section = (self.section_name or "Section").strip().replace(os.sep, ' ').replace(':', '-')
        safe_exam = (self.exam_name or "Exam").strip().replace(os.sep, ' ').replace(':', '-')
        base = f"{safe_section} - {safe_exam} - statistics"

        if scores:
            try:
                mean = sum(scores) / len(scores)
                median = stats.median(scores)
                mode = stats.mode(scores)
            except stats.StatisticsError:
                median = stats.median(scores); mean = sum(scores)/len(scores); mode = "—"
            mn = min(scores); mx = max(scores)
            min_names = [r['student_name'] for r in self.results if r.get('score') == mn]
            max_names = [r['student_name'] for r in self.results if r.get('score') == mx]
        else:
            mean = median = mode = "—"; mn = mx = "—"; min_names = max_names = []

        count = [0] * total_items
        n = len(self.results)
        for r in self.results:
            ans = r['answers']
            for i in range(total_items):
                a = ans[i] if i < len(ans) else -1
                k = self.key.get(i+1, None)
                if k is not None and a == k:
                    count[i] += 1
        pct = [(100.0 * c / n) if n > 0 else 0.0 for c in count]

        try:
            import pandas as pd
            df_summary = pd.DataFrame([{
                'Exam': self.exam_name or "",
                'Section': self.section_name or "",
                'N Students': len(self.results),
                'Mean': mean if isinstance(mean, (int, float)) else "",
                'Median': median if isinstance(median, (int, float)) else "",
                'Mode': mode if isinstance(mode, (int, float)) else str(mode),
                'Lowest Score': mn if isinstance(mn, (int, float)) else "",
                'Lowest Names': ", ".join(min_names),
                'Highest Score': mx if isinstance(mx, (int, float)) else "",
                'Highest Names': ", ".join(max_names),
                'Max Items (active)': total_items,
            }])
            df_items = pd.DataFrame({
                'Item': list(range(1, total_items+1)),
                'Correct (n)': count,
                '% Correct': [f"{p:.1f}%" for p in pct],
            })
            out_path = filedialog.asksaveasfilename(title="Export Statistics (Excel)",
                                                    defaultextension=".xlsx",
                                                    initialfile=f"{base}.xlsx",
                                                    initialdir=self.session_dir,
                                                    filetypes=[("Excel","*.xlsx"),("All","*.*")])
            if not out_path: return
            with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
                df_summary.to_excel(writer, sheet_name="Summary", index=False)
                df_items.to_excel(writer, sheet_name="Item Analysis", index=False)
            messagebox.showinfo("Export Statistics", f"Exported to Excel:\n{out_path}")
            return
        except Exception:
            out_summary = filedialog.asksaveasfilename(title="Export Summary (CSV)",
                                                       defaultextension=".csv",
                                                       initialfile=f"{base} - summary.csv",
                                                       initialdir=self.session_dir,
                                                       filetypes=[("CSV","*.csv"),("All","*.*")])
            if not out_summary: return
            with open(out_summary, 'w', newline='', encoding='utf-8') as f:
                w = csv.writer(f)
                w.writerow(['Exam','Section','N Students','Mean','Median','Mode',
                            'Lowest Score','Lowest Names','Highest Score','Highest Names','Max Items (active)'])
                w.writerow([self.exam_name or "", self.section_name or "", len(self.results),
                            mean if isinstance(mean, (int, float)) else "",
                            median if isinstance(median, (int, float)) else "",
                            mode if isinstance(mode, (int, float)) else str(mode),
                            mn if isinstance(mn, (int, float)) else "",
                            "; ".join(min_names),
                            mx if isinstance(mx, (int, float)) else "",
                            "; ".join(max_names),
                            total_items])
            out_items = out_summary.replace("summary.csv", "item-analysis.csv")
            with open(out_items, 'w', newline='', encoding='utf-8') as f:
                w = csv.writer(f)
                w.writerow(['Item','Correct (n)','% Correct'])
                for i in range(total_items):
                    w.writerow([i+1, count[i], f"{pct[i]:.1f}%"])
            messagebox.showinfo("Export Statistics", f"Exported CSV files:\n{out_summary}\n{out_items}")

    # ---------- Utils ----------
    def log(self, msg):
        self.log_var.set(msg)

    def on_close(self):
        self.preview_running = False
        if self.cap:
            self.cap.release()
        self.root.destroy()
