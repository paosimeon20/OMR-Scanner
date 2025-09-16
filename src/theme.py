# theme.py
# Professional ttk theme constrained to exactly these 4 colors:
#   #272757, #8686AC, #505081, #0F0E47
# Usage: from theme import apply_theme; apply_theme(root, scale=1.0)

from tkinter import ttk

PALETTE = {
    # fixed 4-color palette
    "C1": "#272757",  # mid-dark (tabs selected / surfaces)
    "C2": "#8686AC",  # text / accents
    "C3": "#505081",  # borders / controls
    "C4": "#0F0E47",  # darkest background
}

def _pad(scale, *vals):
    return tuple(int(round(v * scale)) for v in vals)

def _fz(scale, px):
    return max(8, int(round(px * scale)))

def apply_theme(root, *, scale: float = 1.0):
    s = ttk.Style(root)
    base_theme = "clam" if "clam" in s.theme_names() else s.theme_use()
    s.theme_use(base_theme)

    # Window background
    root.configure(bg=PALETTE["C4"])

    # Typography
    title_font     = ("Segoe UI", _fz(scale, 18), "bold")
    subtitle_font  = ("Segoe UI", _fz(scale, 14), "bold")
    text_font      = ("Segoe UI", _fz(scale, 12))
    button_font    = ("Segoe UI", _fz(scale, 13), "bold")
    tab_font       = ("Segoe UI", _fz(scale, 13), "bold")
    table_font     = ("Segoe UI", _fz(scale, 12))
    table_head     = ("Segoe UI", _fz(scale, 12), "bold")
    row_h = max(24, int(34 * scale))

    # ---------------------------
    # Frames / Panels
    # ---------------------------
    s.configure("Modern.TFrame", background=PALETTE["C4"])          # root-level bg
    s.configure("Modern.Surface.TFrame", background=PALETTE["C1"])  # tab pages, appbar
    s.configure("Modern.Panel.TFrame", background=PALETTE["C4"])    # inner panels

    s.configure("Modern.TLabelframe",
                background=PALETTE["C1"],
                borderwidth=1,
                relief="solid",
                bordercolor=PALETTE["C3"])
    s.configure("Modern.TLabelframe.Label",
                background=PALETTE["C1"],
                foreground=PALETTE["C2"],
                font=subtitle_font)

    # Labels
    s.configure("Title.TLabel",    background=PALETTE["C4"], foreground=PALETTE["C2"], font=title_font)
    s.configure("Subtitle.TLabel", background=PALETTE["C4"], foreground=PALETTE["C2"], font=subtitle_font)
    s.configure("Body.TLabel",     background=PALETTE["C4"], foreground=PALETTE["C2"], font=text_font)
    s.configure("Status.TLabel",   background=PALETTE["C4"], foreground=PALETTE["C2"], font=text_font)

    # Separators
    s.configure("TSeparator", background=PALETTE["C3"])

    # ---------------------------
    # Buttons (uniform, with auto-contrast text)
    # ---------------------------
    def _contrast_color(hex_color: str) -> str:
        """Return black or white depending on background brightness."""
        hex_color = hex_color.lstrip('#')
        r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        # relative luminance (simple version)
        luminance = (0.299*r + 0.587*g + 0.114*b) / 255
        return "#000000" if luminance > 0.6 else "#ffffff"

    def _btn(style_name, bg, hover_bg):
        fg = _contrast_color(bg)
        s.configure(style_name,
                    background=bg,
                    foreground=fg,
                    font=button_font,
                    padding=_pad(scale, 14, 10),
                    borderwidth=0,
                    relief="flat")
        s.map(style_name,
              background=[("active", hover_bg), ("pressed", hover_bg)],
              foreground=[("active", _contrast_color(hover_bg)),
                          ("pressed", _contrast_color(hover_bg))])

    # Uniform look: all button styles mapped to the same scheme
    base_bg   = PALETTE["C3"]   # normal background (#505081)
    hover_bg  = PALETTE["C1"]   # hover/pressed (#272757)

    for name in ("Primary.TButton", "Success.TButton",
                 "Warning.TButton", "Danger.TButton", "Ghost.TButton"):
        _btn(name, base_bg, hover_bg)


    # Notebook (tabs)
    s.configure("Modern.TNotebook", background=PALETTE["C4"], borderwidth=0, tabmargins=_pad(scale, 8, 6, 0, 0))
    s.layout("Modern.TNotebook.Tab", [
        ("Notebook.tab", {
            "sticky": "nswe",
            "children": [("Notebook.padding", {"side":"top","sticky":"nswe",
                              "children":[("Notebook.label", {"side":"top","sticky":""})]})]
        })
    ])
    s.configure("Modern.TNotebook.Tab",
                padding=_pad(scale, 20, 12),
                font=tab_font,
                background=PALETTE["C4"],
                foreground=PALETTE["C2"],
                borderwidth=1)
    s.map("Modern.TNotebook.Tab",
          background=[("selected", PALETTE["C1"]), ("active", PALETTE["C1"])],
          foreground=[("selected", PALETTE["C2"]), ("active", PALETTE["C2"])])

    # Inputs
    s.configure("TCombobox",
                fieldbackground=PALETTE["C4"],
                background=PALETTE["C4"],
                foreground=PALETTE["C2"],
                bordercolor=PALETTE["C3"])
    s.map("TCombobox",
          fieldbackground=[("readonly", PALETTE["C4"])],
          foreground=[("readonly", PALETTE["C2"])])

    s.configure("TSpinbox",
                fieldbackground=PALETTE["C4"],
                background=PALETTE["C4"],
                foreground=PALETTE["C2"])

    # Treeview (tables)
    s.configure("Modern.Treeview",
                background=PALETTE["C4"],
                fieldbackground=PALETTE["C4"],
                foreground=PALETTE["C2"],
                rowheight=row_h,
                font=table_font,
                bordercolor=PALETTE["C3"],
                borderwidth=1)
    s.configure("Modern.Treeview.Heading",
                background=PALETTE["C1"],
                foreground=PALETTE["C2"],
                font=table_head)
    s.map("Modern.Treeview.Heading",
          background=[("active", PALETTE["C1"])],
          foreground=[("active", PALETTE["C2"])])

    # Optional: we'll tag stripes in your code using only C4/C1
    try:
        s.configure("striped.Treeview", background=PALETTE["C4"])
    except Exception:
        pass

    return PALETTE
