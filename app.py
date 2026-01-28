import os
import sys
import cv2
import pickle
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageOps
from datetime import datetime
import face_recognition


ENCODINGS_PATH = os.path.join("encodings", "face_encodings.pkl")
ATTENDANCE_PATH = os.path.join("attendance", "attendance.csv")


COLORS = {
    "app_bg":   "#F3F6FF",
    "card_bg":  "#FFFFFF",
    "border":   "#E5E7EB",
    "text":     "#0F172A",
    "muted":    "#64748B",
    "accent":   "#2563EB",
    "accent_h": "#1D4ED8",
    "success":  "#16A34A",
    "danger":   "#DC2626",
}


class AttendanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Attendance - Real-time Recognition")
        self.root.geometry("1000x650")
        self.root.configure(bg=COLORS["app_bg"])
        self.pending_name = None
        self.pending_start = None

        os.makedirs("attendance", exist_ok=True)

        self.known_data = self.load_encodings()

        self._setup_styles()
        self._build_layout()

        # Internal variables
        self.cap = None
        self.is_running = False
        self._video_after_id = None

        # Clean up on close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def load_encodings(self):
        """Load pre-trained face encodings"""
        if not os.path.exists(ENCODINGS_PATH):
            messagebox.showerror(
                "Error", "Encodings not found. Register faces first.")
            return None
        with open(ENCODINGS_PATH, "rb") as f:
            return pickle.load(f)

    def _setup_styles(self):
        """Configure UI styles"""
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("App.TFrame", background=COLORS["app_bg"])
        style.configure(
            "Card.TFrame", background=COLORS["card_bg"], relief="flat")
        style.configure("Title.TLabel", background=COLORS["app_bg"], foreground=COLORS["text"], font=(
            "Segoe UI", 20, "bold"))
        style.configure("Accent.TButton", background=COLORS["accent"], foreground="white", padding=(
            14, 10), font=("Segoe UI", 10, "bold"))
        style.map("Accent.TButton", background=[
                  ("active", COLORS["accent_h"])])

    def _build_layout(self):
        """Create UI layout elements"""
        header = ttk.Frame(self.root, style="App.TFrame")
        header.pack(fill="x", padx=20, pady=15)
        ttk.Label(header, text="Smart Attendance System",
                  style="Title.TLabel").pack(side="left")

        container = ttk.Frame(self.root, style="App.TFrame")
        container.pack(fill="both", expand=True, padx=20, pady=10)

        self.video_card = ttk.Frame(container, style="Card.TFrame")
        self.video_card.pack(side="left", fill="both",
                             expand=True, padx=(0, 10))

        self.video_label = tk.Label(self.video_card, bg="#0B1220")
        self.video_label.pack(fill="both", expand=True, padx=10, pady=10)

        side_panel = ttk.Frame(container, style="App.TFrame", width=300)
        side_panel.pack(side="right", fill="both")
        side_panel.pack_propagate(False)

        control_card = ttk.Frame(side_panel, style="Card.TFrame")
        control_card.pack(fill="x", pady=(0, 10))

        self.btn_toggle = ttk.Button(
            control_card, text="Mark Attendance", style="Accent.TButton", command=self.toggle_recognition)
        self.btn_toggle.pack(fill="x", padx=15, pady=25)

        tip_text = "Instructions:\n1. Click 'Mark Attendance'.\n2. Show your face.\n3. One entry per person per day."
        ttk.Label(control_card, text=tip_text, background=COLORS["card_bg"], foreground=COLORS["muted"], font=(
            "Segoe UI", 9)).pack(padx=15, pady=10)

        self.status_label = ttk.Label(
            control_card,
            text="Status: Idle",
            background=COLORS["card_bg"],
            foreground=COLORS["muted"],
            font=("Segoe UI", 9)
        )
        self.status_label.pack(padx=15, pady=(0, 10), anchor="w")

    def toggle_recognition(self):
        if not self.is_running:
            self.start_recognition()
        else:
            self.stop_recognition()

    def start_recognition(self):
        if self.known_data is None:
            return
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Cannot open camera.")
            return
        self.is_running = True
        self.btn_toggle.configure(text="Stop Camera")
        self.update_video()

    def stop_recognition(self):
        self.is_running = False
        self.btn_toggle.configure(text="Mark Attendance")
        if self.cap:
            self.cap.release()
            self.cap = None
        self.video_label.configure(image="")
        if self._video_after_id:
            self.root.after_cancel(self._video_after_id)

    def mark_attendance_logic(self, name):
        """Check for daily duplicates and save attendance"""
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")

        if not os.path.exists(ATTENDANCE_PATH):
            with open(ATTENDANCE_PATH, "w") as f:
                f.write("Name,Date,Time\n")

        # DAILY DUPLICATE CHECK START
        already_marked = False
        with open(ATTENDANCE_PATH, "r") as f:
            lines = f.readlines()
            for line in lines:

                if name in line and date_str in line:
                    already_marked = True
                    break

        if already_marked:
            self.stop_recognition()
            messagebox.showwarning(
                "Already Marked", f"Attendance already marked for {name} today!")
            return
        # DAILY DUPLICATE CHECK END

        with open(ATTENDANCE_PATH, "a") as f:
            f.write(f"{name},{date_str},{time_str}\n")

        self.stop_recognition()
        messagebox.showinfo(
            "Success", f"Attendance Marked Successfully!\nName: {name}\nTime: {time_str}")

    def update_video(self):
        if not self.is_running or self.cap is None:
            return

        ret, frame = self.cap.read()
        if ret:
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            face_locs = face_recognition.face_locations(rgb_small)
            face_encs = face_recognition.face_encodings(rgb_small, face_locs)

            for (top, right, bottom, left), face_enc in zip(face_locs, face_encs):
                matches = face_recognition.compare_faces(
                    self.known_data["encodings"], face_enc, 0.5)
                name = "Unknown"

                face_distances = face_recognition.face_distance(
                    self.known_data["encodings"], face_enc)
                if len(face_distances) > 0:
                    best_match_idx = np.argmin(face_distances)
                    if matches[best_match_idx]:
                        name = self.known_data["names"][best_match_idx]

                if name != "Unknown":
                    now = datetime.now()
                    if self.pending_name == name:
                        elapsed = (now - self.pending_start).total_seconds()
                        if elapsed >= 1.5:
                            self.mark_attendance_logic(name)
                            return
                    else:
                        self.pending_name = name
                        self.pending_start = now
                        self.status_label.config(
                            text=f"Detected {name}, Please hold still...")
                else:
                    self.pending_name = None
                    self.pending_start = None
                    self.status_label.config(
                        text=f"Status: Searching for face...")

                top, right, bottom, left = top*4, right*4, bottom*4, left*4
                color = (74, 163, 22) if name != "Unknown" else (38, 38, 220)
                cv2.rectangle(frame, (left, top),
                              (right, bottom), color[::-1], 2)
                cv2.putText(frame, name, (left, top-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color[::-1], 2)

            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            img = ImageOps.contain(
                img, (self.video_label.winfo_width(), self.video_label.winfo_height()))
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

        self._video_after_id = self.root.after(10, self.update_video)

    def on_close(self):
        self.stop_recognition()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    root.state("zoomed")
    app = AttendanceApp(root)
    root.mainloop()
