"""
Probably not the best way to do this.

But whatever it works

"""

import tkinter as tk
from tkinter import filedialog
 
 
def select_folder(initial_directory: str) -> str:
    """Open a native folder picker and return the chosen path (or '' if cancelled)."""
    root = tk.Tk()
    root.attributes("-topmost", True)
    root.withdraw()
    path = filedialog.askdirectory(
        title="Select Directory",
        initialdir=initial_directory,
        parent=root,
    )
    root.destroy()
    return path