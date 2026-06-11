"""Small GUI helpers for double-click / packaged launches without a terminal."""


def show_error(title: str, message: str) -> None:
    """Show a native error dialog when possible, else print to stderr."""
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        messagebox.showerror(title, message)
        root.destroy()
    except Exception:
        print(f"{title}: {message}", flush=True)


def show_info(title: str, message: str) -> None:
    """Show a native info dialog when possible."""
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        messagebox.showinfo(title, message)
        root.destroy()
    except Exception:
        print(f"{title}: {message}", flush=True)
