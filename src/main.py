# main.py
import os
import sys
import traceback
import tkinter as tk
from tkinter import ttk, messagebox

def _errbox(title, msg):
    try:
        # Show a dialog only if Tk initialized
        root = tk._default_root or tk.Tk()
        root.withdraw()
        messagebox.showerror(title, msg)
        try:
            root.destroy()
        except Exception:
            pass
    except Exception:
        # Fallback: just print
        print(f"[FATAL] {title}\n{msg}", file=sys.stderr)

def main():
    print("[OMR] Starting…")

    # 1) Create Tk root early so any dialog can show
    try:
        root = tk.Tk()
    except Exception as e:
        traceback.print_exc()
        print("\nTip: On Linux, install Tk:  sudo apt-get install python3-tk", file=sys.stderr)
        return

    # 2) DPI / theme warm-up (don’t hide errors)
    
    try:
        if os.name == "nt":
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        style = ttk.Style(root)
        # Choose a safe base; theme.py will restyle anyway
        if "clam" in style.theme_names():
            style.theme_use("clam")
    except Exception:
        traceback.print_exc()

    # 3) Apply our professional theme (optional first-run toggle)
    try:
        from theme import apply_theme
        apply_theme(root, scale=1.0)
        print("[OMR] Theme applied.")
    except ModuleNotFoundError:
        print("[OMR] theme.py not found — continuing with default ttk look.")
    except Exception:
        traceback.print_exc()
        _errbox("Theme Error", "Failed to apply theme. See console for details.")

    # 4) Import and launch the UI app
    try:
        from ui_app import OMRApp
        app = OMRApp(root)
        # Show a placeholder image so the window isn’t empty on first run
        try:
            app._show_placeholder_annot()
        except Exception:
            pass
        print("[OMR] UI created. Entering mainloop…")
        root.mainloop()
        print("[OMR] Exited cleanly.")
    except Exception as e:
        tb = traceback.format_exc()
        print(tb, file=sys.stderr)
        _errbox("Startup Error", f"OMR app failed to start:\n\n{e}\n\nSee console for full traceback.")

if __name__ == "__main__":
    main()

