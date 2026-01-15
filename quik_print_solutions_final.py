import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageDraw
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import tempfile
import os
import win32api
import win32print
import webbrowser

# ================= CONFIG =================
APP_NAME = "Quik Print Solutions"
APP_URL = "https://printbuddyapp.netlify.app"
APP_VERSION = "v1.0"

ID_WIDTH = int(3.5 * 300)
ID_HEIGHT = int(2.3 * 300)

BORDER_COLOR = (180, 180, 180)
BORDER_WIDTH = 2

# ================= STATE =================
original_images = []
processed_images = []
preview_refs = []

# ================= IMAGE UTIL =================

def add_border(img):
    draw = ImageDraw.Draw(img)
    w, h = img.size
    for i in range(BORDER_WIDTH):
        draw.rectangle([i, i, w - i - 1, h - i - 1], outline=BORDER_COLOR)
    return img

def process_image(src_img):
    img = src_img.copy()
    mode = fit_fill_var.get()

    if mode == "fill":
        img = img.resize((ID_WIDTH, ID_HEIGHT), Image.Resampling.LANCZOS)
    else:  # FIT
        img.thumbnail((ID_WIDTH, ID_HEIGHT), Image.Resampling.LANCZOS)
        bg = Image.new("RGB", (ID_WIDTH, ID_HEIGHT), "white")
        x = (ID_WIDTH - img.width) // 2
        y = (ID_HEIGHT - img.height) // 2
        bg.paste(img, (x, y))
        img = bg

    return add_border(img)

# ================= CORE LOGIC =================

def select_images():
    files = filedialog.askopenfilenames(
        title="Select ONLY 2 Images",
        filetypes=[("Images", "*.jpg *.jpeg *.png")]
    )

    if len(files) != 2:
        messagebox.showerror("Error", "Please select exactly 2 images")
        return

    original_images.clear()
    processed_images.clear()

    for f in files:
        img = Image.open(f).convert("RGB")
        if img.height > img.width:
            img = img.rotate(-90, expand=True)
        original_images.append(img)

    rebuild_images()

def rebuild_images():
    processed_images.clear()
    for img in original_images:
        processed_images.append(process_image(img))
    update_preview()

def update_preview():
    for w in preview_inner.winfo_children():
        w.destroy()

    if len(processed_images) != 2:
        return

    preview_refs.clear()

    for img in processed_images:
        p = img.copy()
        p.thumbnail((220, 150))
        tk_img = ImageTk.PhotoImage(p)
        preview_refs.append(tk_img)
        tk.Label(preview_inner, image=tk_img).pack(pady=8)

def swap_images():
    if len(original_images) != 2:
        return
    original_images[0], original_images[1] = original_images[1], original_images[0]
    rebuild_images()

def build_page():
    page = Image.new("RGB", (2480, 3508), "white")
    x = (2480 - ID_WIDTH) // 2
    page.paste(processed_images[0], (x, 400))
    page.paste(processed_images[1], (x, 400 + ID_HEIGHT + 900))
    return page

def print_images(event=None):
    if len(processed_images) != 2:
        messagebox.showerror("Error", "Select 2 images first")
        return

    printer = printer_var.get()
    if not printer:
        messagebox.showerror("Error", "No printer selected")
        return

    page = build_page()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as img_tmp:
        page.save(img_tmp.name)
        img_path = img_tmp.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as pdf_tmp:
        c = canvas.Canvas(pdf_tmp.name, pagesize=A4)
        c.drawImage(img_path, 0, 0, A4[0], A4[1])
        c.showPage()
        c.save()
        pdf_path = pdf_tmp.name

    os.remove(img_path)

    win32api.ShellExecute(
        0, "printto", pdf_path, f'"{printer}"', ".", 0
    )

def open_website(event=None):
    webbrowser.open(APP_URL)

# ================= UI =================

root = tk.Tk()
root.title(APP_NAME)
root.geometry("400x670")
root.resizable(False, False)

# CTRL + P
root.bind_all("<Control-p>", print_images)
root.bind_all("<Control-P>", print_images)

# ---------- LOGO (CRASH SAFE) ----------
try:
    logo = Image.open("logo.png").resize((140, 140), Image.Resampling.LANCZOS)
    logo_tk = ImageTk.PhotoImage(logo)
    lbl_logo = tk.Label(root, image=logo_tk)
    lbl_logo.image = logo_tk
    lbl_logo.pack(pady=5)
except:
    pass

# ---------- APP NAME ----------
tk.Label(
    root,
    text=APP_NAME,
    font=("Segoe UI", 18, "bold")
).pack()

# ---------- CLICKABLE LINK ----------
link_label = tk.Label(
    root,
    text=APP_URL,
    fg="#2563EB",
    cursor="hand2",
    font=("Segoe UI", 9, "underline")
)
link_label.pack(pady=(2, 10))
link_label.bind("<Button-1>", open_website)

# ---------- SELECT ----------
tk.Button(
    root, text="📂 Select 2 Photos",
    height=2, command=select_images
).pack(pady=10)

# ---------- FIT / FILL ----------
fit_fill_var = tk.StringVar(value="fill")

mode_frame = tk.Frame(root)
mode_frame.pack()

tk.Radiobutton(
    mode_frame, text="Fill",
    variable=fit_fill_var, value="fill",
    command=rebuild_images
).pack(side="left", padx=12)

tk.Radiobutton(
    mode_frame, text="Fit",
    variable=fit_fill_var, value="fit",
    command=rebuild_images
).pack(side="left", padx=12)

# ---------- PREVIEW ----------
preview_frame = tk.Frame(root, bd=2, relief="groove")
preview_frame.pack(padx=10, pady=10, fill="x")

preview_inner = tk.Frame(preview_frame)
preview_inner.pack()

# ---------- ACTIONS ----------
action_row = tk.Frame(root)
action_row.pack(pady=10)

tk.Button(
    action_row, text="⇅ Swap",
    width=12, height=2,
    command=swap_images
).pack(side="left", padx=5)

tk.Button(
    action_row, text="🖨️ Print",
    width=12, height=2,
    bg="#2563EB", fg="white",
    command=print_images
).pack(side="left", padx=5)

# ---------- PRINTER ----------
printer_var = tk.StringVar()
printers = [p[2] for p in win32print.EnumPrinters(2)]

tk.Label(root, text="Printer").pack()

ttk.Combobox(
    root,
    values=printers,
    textvariable=printer_var,
    state="readonly"
).pack()

try:
    printer_var.set(win32print.GetDefaultPrinter())
except:
    if printers:
        printer_var.set(printers[0])

# ---------- VERSION ----------
tk.Label(
    root,
    text=APP_VERSION,
    font=("Segoe UI", 8),
    fg="gray"
).pack(side="bottom", pady=6)

root.mainloop()
