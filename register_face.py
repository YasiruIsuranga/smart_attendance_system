import os
import cv2
import pickle
import re
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from PIL import Image, ImageTk, ImageOps
import face_recognition

# ---- PATH CONFIG ----
DATASET_DIR = os.path.join("dataset", "faces")
ENCODINGS_PATH = os.path.join("encodings", "face_encodings.pkl")


# ---- UI COLORS (modern light theme) ----
COLORS = {
    "app_bg":   "#F3F6FF",
    "card_bg":  "#FFFFFF",
    "border":   "#E5E7EB",
    "text":     "#0F172A",
    "muted":    "#64748B",
    "accent":   "#2563EB",
    "accent_h": "#1D4ED8",
    "success":  "#16A34A",
    "success_h": "#15803D",
    "danger":   "#DC2626",
    "warn":     "#D97706",
}


class FaceRegisterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Attendance - Face Registration")
        self.root.geometry("1000x650")
        self.root.minsize(950, 620)
        self.root.configure(bg=COLORS["app_bg"])

        os.makedirs(DATASET_DIR, exist_ok=True)
        os.makedirs(os.path.dirname(ENCODINGS_PATH), exist_ok=True)

        self._setup_styles()
        self._build_layout()

        # ---- Internal state ----
        self.cap = None
        self.current_frame = None
        self.captured_count = 0
        self.user_folder = None
        self._video_after_id = None

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.set_status("Idle", kind="info")

    # ---------------- UI ----------------
    def _setup_styles(self):
        style = ttk.Style()
        # enables custom colors reliably across platforms
        style.theme_use("clam")

        # Base frames
        style.configure("App.TFrame", background=COLORS["app_bg"])
        style.configure(
            "Card.TFrame", background=COLORS["card_bg"], relief="flat")

        # Labels
        style.configure("Title.TLabel",
                        background=COLORS["app_bg"],
                        foreground=COLORS["text"],
                        font=("Segoe UI", 20, "bold"))
        style.configure("Subtitle.TLabel",
                        background=COLORS["app_bg"],
                        foreground=COLORS["muted"],
                        font=("Segoe UI", 10))
        style.configure("CardTitle.TLabel",
                        background=COLORS["card_bg"],
                        foreground=COLORS["text"],
                        font=("Segoe UI", 12, "bold"))
        style.configure("CardText.TLabel",
                        background=COLORS["card_bg"],
                        foreground=COLORS["muted"],
                        font=("Segoe UI", 10))

        # Entry
        style.configure("Modern.TEntry",
                        padding=8,
                        relief="flat",
                        fieldbackground="#F8FAFC",
                        foreground=COLORS["text"])

        # Buttons
        style.configure("Accent.TButton",
                        background=COLORS["accent"],
                        foreground="white",
                        padding=(14, 10),
                        borderwidth=0,
                        focusthickness=0,
                        font=("Segoe UI", 10, "bold"))
        style.map("Accent.TButton",
                  background=[("active", COLORS["accent_h"]), ("pressed", COLORS["accent_h"])])

        style.configure("Success.TButton",
                        background=COLORS["success"],
                        foreground="white",
                        padding=(14, 10),
                        borderwidth=0,
                        focusthickness=0,
                        font=("Segoe UI", 10, "bold"))
        style.map("Success.TButton",
                  background=[("active", COLORS["success_h"]), ("pressed", COLORS["success_h"])])

        style.configure("Ghost.TButton",
                        background="#EEF2FF",
                        foreground=COLORS["accent"],
                        padding=(14, 10),
                        borderwidth=0,
                        focusthickness=0,
                        font=("Segoe UI", 10, "bold"))
        style.map("Ghost.TButton",
                  background=[("active", "#E0E7FF"), ("pressed", "#E0E7FF")])

        # Status bar
        style.configure("StatusBar.TFrame", background=COLORS["card_bg"])
        style.configure(
            "StatusInfo.TLabel", background=COLORS["card_bg"], foreground=COLORS["muted"], font=("Segoe UI", 10))
        style.configure("StatusOk.TLabel",   background=COLORS["card_bg"], foreground=COLORS["success"], font=(
            "Segoe UI", 10, "bold"))
        style.configure("StatusWarn.TLabel", background=COLORS["card_bg"], foreground=COLORS["warn"], font=(
            "Segoe UI", 10, "bold"))
        style.configure("StatusErr.TLabel",  background=COLORS["card_bg"], foreground=COLORS["danger"], font=(
            "Segoe UI", 10, "bold"))

        style.configure("Thin.TSeparator", background=COLORS["border"])

    def _build_layout(self):
        # Root grid
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Header
        header = ttk.Frame(self.root, style="App.TFrame")
        header.grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 10))
        header.grid_columnconfigure(0, weight=1)

        ttk.Label(header, text="Face Registration", style="Title.TLabel").grid(
            row=0, column=0, sticky="w")
        ttk.Label(header,
                  text="Register a user by capturing multiple angles and updating encodings.",
                  style="Subtitle.TLabel").grid(row=1, column=0, sticky="w", pady=(2, 0))

        # Content
        content = ttk.Frame(self.root, style="App.TFrame")
        content.grid(row=1, column=0, sticky="nsew", padx=18, pady=10)
        content.grid_columnconfigure(0, weight=3)
        content.grid_columnconfigure(1, weight=2)
        content.grid_rowconfigure(0, weight=1)

        # Video Card
        video_card = ttk.Frame(content, style="Card.TFrame")
        video_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        video_card.grid_rowconfigure(1, weight=1)
        video_card.grid_columnconfigure(0, weight=1)

        ttk.Label(video_card, text="Camera Preview", style="CardTitle.TLabel").grid(
            row=0, column=0, sticky="w", padx=14, pady=(12, 6)
        )

        # Use tk.Label for easy solid background (video area)
        self.video_label = tk.Label(
            video_card,
            bg="#0B1220",
            highlightthickness=1,
            highlightbackground=COLORS["border"],
            bd=0
        )
        self.video_label.grid(
            row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))

        # Controls Card
        controls_card = ttk.Frame(content, style="Card.TFrame")
        controls_card.grid(row=0, column=1, sticky="nsew")
        controls_card.grid_columnconfigure(0, weight=1)

        ttk.Label(controls_card, text="Controls", style="CardTitle.TLabel").grid(
            row=0, column=0, sticky="w", padx=14, pady=(12, 6)
        )

        # Name/ID
        form = ttk.Frame(controls_card, style="Card.TFrame")
        form.grid(row=1, column=0, sticky="ew", padx=14, pady=(2, 8))
        form.grid_columnconfigure(0, weight=1)

        ttk.Label(form, text="User Name / ID",
                  style="CardText.TLabel").grid(row=0, column=0, sticky="w")
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(
            form, textvariable=self.name_var, style="Modern.TEntry")
        self.name_entry.grid(row=1, column=0, sticky="ew", pady=(6, 0))

        # Buttons
        btns = ttk.Frame(controls_card, style="Card.TFrame")
        btns.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 10))
        btns.grid_columnconfigure(0, weight=1)
        btns.grid_columnconfigure(1, weight=1)

        ttk.Button(btns, text="Start Camera", style="Accent.TButton",
                   command=self.start_camera).grid(row=0, column=0, sticky="ew", padx=(0, 6), pady=6)

        ttk.Button(btns, text="Capture", style="Ghost.TButton",
                   command=self.capture_frame).grid(row=0, column=1, sticky="ew", padx=(6, 0), pady=6)

        ttk.Button(controls_card, text="Finish & Save", style="Success.TButton",
                   command=self.finish_and_save).grid(row=3, column=0, sticky="ew", padx=14, pady=(0, 12))

        ttk.Separator(controls_card, orient="horizontal", style="Thin.TSeparator").grid(
            row=4, column=0, sticky="ew", padx=14, pady=10
        )

        tips = (
            "Tips:\n"
            "• Capture 5–15 photos.\n"
            "• Slightly change angles.\n"
            "• Avoid backlight; keep face centered.\n"
            "• Use a unique User Name / ID."
        )
        ttk.Label(controls_card, text=tips, style="CardText.TLabel", justify="left").grid(
            row=5, column=0, sticky="nw", padx=14, pady=(0, 14)
        )

        # Status bar
        status_bar = ttk.Frame(self.root, style="StatusBar.TFrame")
        status_bar.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 14))
        status_bar.grid_columnconfigure(0, weight=1)

        self.status_label = ttk.Label(
            status_bar, text="", style="StatusInfo.TLabel", anchor="w")
        self.status_label.grid(row=0, column=0, sticky="ew", padx=12, pady=10)

    def set_status(self, text, kind="info"):
        style = {
            "info": "StatusInfo.TLabel",
            "ok":   "StatusOk.TLabel",
            "warn": "StatusWarn.TLabel",
            "err":  "StatusErr.TLabel",
        }.get(kind, "StatusInfo.TLabel")
        self.status_label.configure(text=f"Status: {text}", style=style)
        self.root.update_idletasks()

    # ---------------- Logic ----------------
    def sanitize_name(self, name: str) -> str:
        name = name.strip()
        name = re.sub(r"\s+", "_", name)
        name = re.sub(r"[^a-zA-Z0-9_\-\.]", "", name)
        return name

    def start_camera(self):
        raw_name = self.name_var.get().strip()
        if not raw_name:
            messagebox.showwarning(
                "Input required", "Please enter a user name/ID first.")
            self.set_status("Please enter a user name/ID.", kind="warn")
            return

        name = self.sanitize_name(raw_name)
        if not name:
            messagebox.showwarning(
                "Invalid name", "Use letters/numbers (spaces allowed).")
            self.set_status("Invalid user name/ID.", kind="warn")
            return

        self.user_folder = os.path.join(DATASET_DIR, name)
        os.makedirs(self.user_folder, exist_ok=True)

        # If camera already open, release and reopen cleanly
        if self.cap is not None:
            self.cap.release()
            self.cap = None

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Could not open camera.")
            self.set_status("Could not open camera.", kind="err")
            self.cap = None
            return

        self.captured_count = 0
        self.set_status(
            "Camera started. Look at the camera and press 'Capture'.", kind="ok")
        self.update_frame()

    def update_frame(self):
        if self.cap is None:
            return

        ret, frame = self.cap.read()
        if not ret:
            self.set_status("Failed to get frame from camera.", kind="err")
            return

        self.current_frame = frame

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)

        # Fit image into the available label size
        w = max(1, self.video_label.winfo_width())
        h = max(1, self.video_label.winfo_height())
        img = ImageOps.contain(img, (w, h))

        imgtk = ImageTk.PhotoImage(image=img)
        self.video_label.imgtk = imgtk
        self.video_label.configure(image=imgtk)

        self._video_after_id = self.root.after(30, self.update_frame)

    def capture_frame(self):
        if self.cap is None or self.current_frame is None:
            messagebox.showwarning("No camera", "Start the camera first.")
            self.set_status("Start the camera first.", kind="warn")
            return

        filename = os.path.join(
            self.user_folder, f"img_{self.captured_count}.jpg")
        cv2.imwrite(filename, self.current_frame)
        self.captured_count += 1
        self.set_status(f"Captured {self.captured_count} image(s).", kind="ok")

    def finish_and_save(self):
        # Stop camera
        if self.cap is not None:
            self.cap.release()
            self.cap = None

        if self._video_after_id is not None:
            try:
                self.root.after_cancel(self._video_after_id)
            except Exception:
                pass
            self._video_after_id = None

        # Clear video feed
        self.video_label.configure(image="")
        self.video_label.imgtk = None

        if self.captured_count == 0:
            self.set_status(
                "No images captured. Nothing to save.", kind="warn")
            return

        self.set_status("Generating encodings... Please wait.", kind="info")
        self.generate_encodings()

        self.set_status(
            f"Done. Saved {self.captured_count} images. Encodings updated.", kind="ok")
        messagebox.showinfo(
            "Success", "User registered and encodings updated.")

    def generate_encodings(self):
        known_encodings = []
        known_names = []

        for user in os.listdir(DATASET_DIR):
            user_dir = os.path.join(DATASET_DIR, user)
            if not os.path.isdir(user_dir):
                continue

            for img_name in os.listdir(user_dir):
                img_path = os.path.join(user_dir, img_name)
                try:
                    image = face_recognition.load_image_file(img_path)
                    face_locations = face_recognition.face_locations(image)

                    # Only use images with exactly one face
                    if len(face_locations) != 1:
                        continue

                    encoding = face_recognition.face_encodings(
                        image, face_locations)[0]
                    known_encodings.append(encoding)
                    known_names.append(user)
                except Exception as e:
                    print(f"Error processing {img_path}: {e}")

        data = {"encodings": known_encodings, "names": known_names}
        with open(ENCODINGS_PATH, "wb") as f:
            pickle.dump(data, f)

    def on_close(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    root.state("zoomed")
    app = FaceRegisterApp(root)
    root.mainloop()
