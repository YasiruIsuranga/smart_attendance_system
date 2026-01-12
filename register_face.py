import os
import cv2
import pickle
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from PIL import Image, ImageTk
import face_recognition

# ---- PATH CONFIG ----
DATASET_DIR = os.path.join("dataset", "faces")
ENCODINGS_PATH = os.path.join("encodings", "face_encodings.pkl")


class FaceRegisterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Attendance - Face Registration")
        self.root.geometry("900x600")
        self.root.configure(bg="#f0f2f5")

        style = ttk.Style()
        style.theme_use("default")
        style.configure("TLabel", background="#f0f2f5", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"))
        style.configure("Status.TLabel", font=(
            "Segoe UI", 9), foreground="#555555")

        os.makedirs(DATASET_DIR, exist_ok=True)
        os.makedirs(os.path.dirname(ENCODINGS_PATH), exist_ok=True)

        # ---- TOP FRAME (Title) ----
        top_frame = ttk.Frame(self.root)
        top_frame.pack(side="top", fill="x", padx=10, pady=10)

        ttk.Label(
            top_frame,
            text="Face Registration",
            style="Header.TLabel"
        ).pack(side="left")

        # ---- CONTROL FRAME ----
        control_frame = ttk.Frame(self.root)
        control_frame.pack(side="top", fill="x", padx=10, pady=(0, 10))

        ttk.Label(control_frame, text="User Name / ID:").grid(row=0,
                                                              column=0, padx=5, pady=5, sticky="e")

        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(
            control_frame, textvariable=self.name_var, width=30)
        name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        start_btn = ttk.Button(
            control_frame, text="Start Camera", command=self.start_camera)
        start_btn.grid(row=0, column=2, padx=5, pady=5)

        # ---- MIDDLE FRAME (Video + Buttons) ----
        middle_frame = ttk.Frame(self.root)
        middle_frame.pack(side="top", fill="both",
                          expand=True, padx=10, pady=5)

        # Left: video feed
        video_frame = ttk.LabelFrame(middle_frame, text="Camera Preview")
        video_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        self.video_label = tk.Label(video_frame, bg="black")
        self.video_label.pack(fill="both", expand=True, padx=5, pady=5)

        # Right: instructions + buttons
        right_frame = ttk.LabelFrame(middle_frame, text="Controls")
        right_frame.pack(side="right", fill="y", padx=(5, 0))

        instructions = (
            "Instructions:\n"
            "1. Enter a unique User Name / ID.\n"
            "2. Click 'Start Camera'.\n"
            "3. Ask user to look at the camera.\n"
            "4. Click 'Capture' 5–15 times from\n"
            "   slightly different angles.\n"
            "5. Click 'Finish & Save' to update\n"
            "   the face encodings.\n"
        )
        ttk.Label(
            right_frame,
            text=instructions,
            justify="left"
        ).pack(anchor="w", padx=5, pady=5)

        btn_frame = ttk.Frame(right_frame)
        btn_frame.pack(pady=10)

        capture_btn = ttk.Button(
            btn_frame, text="Capture", command=self.capture_frame)
        capture_btn.grid(row=0, column=0, padx=5, pady=5)

        finish_btn = ttk.Button(
            btn_frame, text="Finish & Save", command=self.finish_and_save)
        finish_btn.grid(row=0, column=1, padx=5, pady=5)

        # ---- STATUS BAR ----
        self.status_label = ttk.Label(
            self.root,
            text="Status: Idle",
            style="Status.TLabel",
            anchor="w"
        )
        self.status_label.pack(side="bottom", fill="x", padx=10, pady=5)


if __name__ == "__main__":
    root = tk.Tk()
    app = FaceRegisterApp(root)
    root.mainloop()
