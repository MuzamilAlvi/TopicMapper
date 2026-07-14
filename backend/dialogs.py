from __future__ import annotations

import os
from typing import Optional

# Note: We are not using Tkinter as the primary GUI framework.
# This is only for native file/folder picking dialogs under Windows.
import tkinter as tk
from tkinter import filedialog


def pick_directory() -> Optional[str]:
    # Avoid "main thread is not in main loop" by creating an event loop
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        path = filedialog.askdirectory(title="Select videos folder")
        if path:
            return os.path.normpath(path)
        return None
    finally:
        try:
            root.update_idletasks()
        except Exception:
            pass
        root.destroy()



def pick_topics_txt() -> Optional[str]:
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        path = filedialog.askopenfilename(
            title="Select topics text file",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if path:
            return os.path.normpath(path)
        return None
    finally:
        root.destroy()
