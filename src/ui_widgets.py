# ui_widgets.py
# Reusable Tkinter widgets (e.g., scrollable toolbar, scrollable frame).

import tkinter as tk
from tkinter import ttk

class ScrollableToolbar(ttk.Frame):
    """
    Horizontally scrollable toolbar using a Canvas + interior Frame.
    Ensures controls never get cropped on small screens.
    """
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0, bg='#f8f9fa')
        self.hbar = ttk.Scrollbar(self, orient='horizontal', command=self.canvas.xview)
        self.inner = ttk.Frame(self, style='Modern.TFrame')

        self.canvas.configure(xscrollcommand=self.hbar.set)
        self.canvas.pack(side=tk.TOP, fill=tk.X, expand=True)
        self.hbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.window_id = self.canvas.create_window(0, 0, window=self.inner, anchor='nw')

        self.inner.bind('<Configure>', self._on_inner_configure)
        self.canvas.bind('<Configure>', self._on_canvas_configure)

        # start scrolled fully left
        self.after(50, lambda: self.canvas.xview_moveto(0.0))
        # Shift + mouse wheel for horizontal scrolling
        self.canvas.bind_all('<Shift-MouseWheel>', self._on_shift_wheel)

    def _on_inner_configure(self, event):
        bbox = self.canvas.bbox('all')
        if bbox:
            self.canvas.configure(scrollregion=bbox)
        # Make canvas tall enough for content
        req_h = self.inner.winfo_reqheight()
        if req_h > 0:
            self.canvas.configure(height=req_h)
            self.canvas.itemconfig(self.window_id, height=req_h)

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.window_id, height=event.height)

    def _on_shift_wheel(self, event):
        direction = -1 if event.delta > 0 else 1
        self.canvas.xview_scroll(direction, 'units')


class ScrollableFrame(ttk.Frame):
    """
    Generic vertically scrollable container:
      - self.body is the interior frame where you pack your content
      - gains a right-side vertical scrollbar and mousewheel scrolling
      - supports dynamic resizing
    """
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0, bg='#f8f9fa')
        self.vbar = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.body = ttk.Frame(self.canvas, style='Modern.TFrame')

        self.canvas.configure(yscrollcommand=self.vbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.vbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._win = self.canvas.create_window((0, 0), window=self.body, anchor='nw')

        # track size changes to update scrollregion
        self.body.bind('<Configure>', self._on_body_configure)
        self.canvas.bind('<Configure>', self._on_canvas_configure)

        # Mouse wheel support (Windows/Mac/Linux)
        self.body.bind_all("<MouseWheel>", self._on_mousewheel)      # Windows/macOS
        self.body.bind_all("<Button-4>", self._on_mousewheel_linux)  # Linux up
        self.body.bind_all("<Button-5>", self._on_mousewheel_linux)  # Linux down

    def _on_body_configure(self, event):
        # Update scrollregion to match body size
        bbox = self.canvas.bbox('all')
        if bbox:
            self.canvas.configure(scrollregion=bbox)

    def _on_canvas_configure(self, event):
        # Keep body width in sync with canvas width
        self.canvas.itemconfig(self._win, width=event.width)

    def _on_mousewheel(self, event):
        # event.delta: positive when scrolling up (on Windows typically +120/-120)
        delta = int(-1*(event.delta/120))
        self.canvas.yview_scroll(delta, "units")

    def _on_mousewheel_linux(self, event):
        # For X11 systems using Button-4/5
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
