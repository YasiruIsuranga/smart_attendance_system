import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import csv
from datetime import datetime
from fpdf import FPDF
from PIL import Image, ImageTk, ImageOps
import shutil

# ---- PATH CONFIGURATION ----
REGISTER_SCRIPT = "register_face.py"
MARK_ATTENDANCE_SCRIPT = "app.py"
ATTENDANCE_PATH = os.path.join("attendance", "attendance.csv")
DATASET_DIR = os.path.join("dataset", "faces")

# UI COLOR PALETTE
COLORS = {
    "sidebar": "#0F172A",
    "bg": "#F1F5F9",
    "card": "#FFFFFF",
    "accent": "#2563EB",
    "text": "#1E293B",
    "success": "#059669",
    "border": "#E2E8F0"
}

# ---------------- REPORT WINDOW ----------------


class ReportWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Attendance Analytics & Reports")
        self.geometry("900x600")
        self.configure(bg=COLORS["bg"])

        # Track current view: "all" or "today"
        self.current_mode = "all"

        # ---- Toolbar ----
        toolbar = tk.Frame(self, bg=COLORS["card"], pady=10)
        toolbar.pack(fill="x")

        tk.Button(
            toolbar,
            text="📅 Today",
            command=self.load_today,
            bg=COLORS["sidebar"],
            fg="white"
        ).pack(side="left", padx=20)

        tk.Button(
            toolbar,
            text="📊 All Records",
            command=self.load_all,
            bg=COLORS["sidebar"],
            fg="white"
        ).pack(side="left")

        tk.Button(
            toolbar,
            text="🔄 Refresh",
            command=self.refresh_current,
            bg=COLORS["sidebar"],
            fg="white"
        ).pack(side="left", padx=10)

        tk.Button(
            toolbar,
            text="📥 DOWNLOAD PDF",
            command=self.export_pdf,
            bg=COLORS["success"],
            fg="white",
            font=("Segoe UI", 9, "bold")
        ).pack(side="right", padx=20)

        # ---- Treeview ----
        style = ttk.Style()
        style.configure("Treeview", rowheight=30)

        self.tree = ttk.Treeview(
            self,
            columns=("Name", "Date", "Time"),
            show="headings"
        )
        self.tree.heading("Name", text="Student Name")
        self.tree.heading("Date", text="Date")
        self.tree.heading("Time", text="Check-in Time")
        self.tree.pack(fill="both", expand=True, padx=20, pady=20)

        # First load + auto-refresh
        self.load_all()
        self.after(2000, self.auto_refresh)   # refresh every 2 seconds

    # ---------- Data helpers ----------

    def get_data(self):
        """Read all attendance rows from the CSV."""
        rows = []
        if not os.path.exists(ATTENDANCE_PATH):
            return rows

        with open(ATTENDANCE_PATH, "r", newline="") as f:
            reader = csv.reader(f)
            header = next(reader, None)  # skip header
            for row in reader:
                if len(row) >= 3:
                    rows.append(row)
        return rows

    def load_all(self):
        """Show all attendance records."""
        self.current_mode = "all"
        self.update_table(self.get_data())

    def load_today(self):
        """Show only today's attendance records."""
        self.current_mode = "today"
        today = datetime.now().strftime("%Y-%m-%d")
        data = [row for row in self.get_data() if len(row) >=
                2 and row[1] == today]
        self.update_table(data)

    def refresh_current(self):
        """Reload table based on current mode (all or today)."""
        if self.current_mode == "today":
            self.load_today()
        else:
            self.load_all()

    def auto_refresh(self):
        """Periodic refresh to reflect new attendance marks."""
        self.refresh_current()
        self.after(2000, self.auto_refresh)  # call again in 2 seconds

    def update_table(self, rows):
        """Clear and refill the Treeview."""
        self.tree.delete(*self.tree.get_children())
        for r in rows:
            self.tree.insert("", "end", values=r)

    # ---------- PDF export ----------

    def export_pdf(self):
        """
        Export the currently selected view (All or Today) to a PDF.
        Reads directly from attendance.csv to avoid Treeview item-ID issues.
        """
        all_rows = self.get_data()

        if self.current_mode == "today":
            today = datetime.now().strftime("%Y-%m-%d")
            rows = [r for r in all_rows if len(r) >= 2 and r[1] == today]
        else:
            rows = all_rows

        if not rows:
            messagebox.showwarning("Warning", "No data available to export!")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Save attendance report as PDF"
        )
        if not path:
            return  # user cancelled

        try:
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()

            # Title
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(0, 10, "Attendance Report", ln=True, align="C")
            pdf.ln(8)

            # Date/time stamp
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(
                0,
                8,
                f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                ln=True,
                align="R"
            )
            pdf.ln(4)

            # Table header
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(80, 10, "Name", 1)
            pdf.cell(50, 10, "Date", 1)
            pdf.cell(50, 10, "Time", 1)
            pdf.ln()

            # Table rows
            pdf.set_font("Helvetica", "", 12)
            for name, date_str, time_str in rows:
                pdf.cell(80, 10, str(name), 1)
                pdf.cell(50, 10, str(date_str), 1)
                pdf.cell(50, 10, str(time_str), 1)
                pdf.ln()

            pdf.output(path)
            messagebox.showinfo(
                "Success", "PDF Report downloaded successfully!")

        except Exception as e:
            messagebox.showerror(
                "Error", f"Failed to generate PDF:\n{repr(e)}")

# ----------REGISTERD DATA WINDOW ------------


class RegisteredDataWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Registered Persons Data")
        self.geometry("900x600")
        self.configure(bg=COLORS["bg"])

        # State
        self.users = self.get_users()
        self.current_user = None
        self.image_paths = []
        self.current_index = 0
        self.current_photo = None  # keep reference to avoid GC

        # Layout
        main = tk.Frame(self, bg=COLORS["bg"])
        main.pack(fill="both", expand=True, padx=20, pady=20)

        # Left: user list
        left = tk.Frame(main, bg=COLORS["bg"], width=250)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        tk.Label(
            left,
            text="Registered Persons",
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["bg"],
            fg=COLORS["text"]
        ).pack(anchor="w", pady=(0, 10))

        self.listbox = tk.Listbox(left, font=("Segoe UI", 10))
        self.listbox.pack(fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.on_user_select)

        for u in self.users:
            self.listbox.insert("end", u)

        # Right: photo preview
        right = tk.Frame(main, bg=COLORS["card"],
                         highlightthickness=1,
                         highlightbackground=COLORS["border"])
        right.pack(side="right", fill="both", expand=True)
        right.pack_propagate(False)

        self.user_label = tk.Label(
            right,
            text="Select a user from the left",
            font=("Segoe UI", 12, "bold"),
            bg=COLORS["card"],
            fg=COLORS["text"]
        )
        self.user_label.pack(anchor="w", padx=20, pady=(15, 5))

        self.photo_label = tk.Label(
            right,
            bg="#0B1220"
        )
        self.photo_label.pack(fill="both", expand=True,
                              padx=20, pady=10)

        # Bottom buttons
        btn_frame = tk.Frame(right, bg=COLORS["card"])
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame,
            text="◀ Previous",
            command=self.show_prev,
            font=("Segoe UI", 10),
            bg="#E5E7EB",
            fg=COLORS["text"],
            relief="flat",
            padx=10, pady=6
        ).grid(row=0, column=0, padx=5)

        tk.Button(
            btn_frame,
            text="Next ▶",
            command=self.show_next,
            font=("Segoe UI", 10),
            bg="#E5E7EB",
            fg=COLORS["text"],
            relief="flat",
            padx=10, pady=6
        ).grid(row=0, column=1, padx=5)

        tk.Button(
            btn_frame,
            text="⬇ Download Photos",
            command=self.download_photos,
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["accent"],
            fg="white",
            relief="flat",
            padx=10, pady=6
        ).grid(row=0, column=2, padx=15)

    def get_users(self):
        """Return list of user folders inside dataset/faces."""
        if not os.path.exists(DATASET_DIR):
            return []
        return sorted(
            d for d in os.listdir(DATASET_DIR)
            if os.path.isdir(os.path.join(DATASET_DIR, d))
        )

    def on_user_select(self, event):
        if not self.listbox.curselection():
            return
        idx = self.listbox.curselection()[0]
        user = self.listbox.get(idx)
        self.current_user = user

        user_dir = os.path.join(DATASET_DIR, user)
        files = []
        if os.path.exists(user_dir):
            for name in os.listdir(user_dir):
                if name.lower().endswith((".jpg", ".jpeg", ".png")):
                    files.append(os.path.join(user_dir, name))

        self.image_paths = sorted(files)
        self.current_index = 0

        if not self.image_paths:
            self.user_label.config(text=f"{user} (no photos found)")
            self.photo_label.config(image="", text="No photos")
            self.current_photo = None
        else:
            self.user_label.config(
                text=f"{user} - {len(self.image_paths)} photo(s) found")
            self.show_current_image()

    def show_current_image(self):
        if not self.image_paths:
            return
        path = self.image_paths[self.current_index]
        try:
            img = Image.open(path)
            # Fit into label size (fallback size if not yet measured)
            w = self.photo_label.winfo_width() or 600
            h = self.photo_label.winfo_height() or 400
            img = ImageOps.contain(img, (w, h))
            photo = ImageTk.PhotoImage(img)
            self.current_photo = photo
            self.photo_label.config(image=photo, text="")
        except Exception as e:
            print(f"Error loading {path}: {e}")
            self.photo_label.config(text="Error loading image", image="")
            self.current_photo = None

    def show_next(self):
        if not self.image_paths:
            return
        if self.current_index < len(self.image_paths) - 1:
            self.current_index += 1
        else:
            self.current_index = 0  # wrap around
        self.show_current_image()

    def show_prev(self):
        if not self.image_paths:
            return
        if self.current_index > 0:
            self.current_index -= 1
        else:
            self.current_index = len(self.image_paths) - 1  # wrap
        self.show_current_image()

    def download_photos(self):
        if not self.current_user:
            messagebox.showwarning(
                "No user selected",
                "Please select a user on the left first."
            )
            return

        user_dir = os.path.join(DATASET_DIR, self.current_user)
        if not os.path.exists(user_dir):
            messagebox.showerror(
                "Error",
                "User photo folder not found on disk."
            )
            return

        dest_root = filedialog.askdirectory(
            title="Select destination folder to copy photos"
        )
        if not dest_root:
            return

        target = os.path.join(dest_root, self.current_user)

        if os.path.exists(target):
            messagebox.showerror(
                "Folder exists",
                f"A folder named '{self.current_user}' already exists at the destination.\n"
                "Please choose another location or rename/remove the existing folder."
            )
            return

        try:
            shutil.copytree(user_dir, target)
            messagebox.showinfo(
                "Success",
                f"Photos for '{self.current_user}' copied to:\n{target}"
            )
        except Exception as e:
            messagebox.showerror(
                "Error copying photos",
                f"An error occurred while copying photos:\n{e}"
            )

# ---------------- MAIN DASHBOARD ----------------


class MainDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Face Attendance System v2.0")
        self.root.geometry("1000x600")
        self.root.configure(bg=COLORS["bg"])
        self._setup_ui()

    def _setup_ui(self):
        # Sidebar
        sidebar = tk.Frame(self.root, bg=COLORS["sidebar"], width=260)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar,
            text="SYSTEM MENU",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["sidebar"],
            fg="#64748B"
        ).pack(pady=40)

        # Menu Buttons
        self.create_menu_btn(sidebar, "👤 Register Face", self.run_register)
        self.create_menu_btn(sidebar, "📸 Mark Attendance", self.run_attendance)
        self.create_menu_btn(sidebar, "📊 View Reports",
                             lambda: ReportWindow(self.root))
        self.create_menu_btn(sidebar, "📂 Registered Person's Data",
                             lambda: RegisteredDataWindow(self.root))

        # Main Content Area
        main = tk.Frame(self.root, bg=COLORS["bg"])
        main.pack(side="right", fill="both", expand=True, padx=40, pady=40)

        tk.Label(
            main,
            text="Welcome Back,",
            font=("Segoe UI", 14),
            bg=COLORS["bg"],
            fg="#64748B"
        ).pack(anchor="w")

        tk.Label(
            main,
            text="Smart Attendance Dashboard",
            font=("Segoe UI", 26, "bold"),
            bg=COLORS["bg"],
            fg=COLORS["text"]
        ).pack(anchor="w", pady=(0, 30))

        # Quick Status Card
        card = tk.Frame(
            main,
            bg=COLORS["card"],
            padx=30,
            pady=30,
            highlightthickness=1,
            highlightbackground=COLORS["border"]
        )
        card.pack(fill="x")

        # Calculate today's count initially
        today = datetime.now().strftime("%Y-%m-%d")
        count = 0
        if os.path.exists(ATTENDANCE_PATH):
            with open(ATTENDANCE_PATH, "r", newline="") as f:
                reader = csv.reader(f)
                header = next(reader, None)  # skip header
                for row in reader:
                    # row: [Name, Date, Time]
                    if len(row) >= 2 and row[1] == today:
                        count += 1

        tk.Label(
            card,
            text="Today's Attendance Count",
            font=("Segoe UI", 12),
            bg=COLORS["card"],
            fg="#64748B"
        ).pack(anchor="w")

        # Store the label on self so we can update it later
        self.count_label = tk.Label(
            card,
            text=f"{count} Person Present",
            font=("Segoe UI", 32, "bold"),
            bg=COLORS["card"],
            fg=COLORS["accent"]
        )
        self.count_label.pack(anchor="w", pady=10)

    def create_menu_btn(self, parent, text, cmd):
        btn = tk.Button(
            parent,
            text=text,
            command=cmd,
            font=("Segoe UI", 11),
            bg=COLORS["sidebar"],
            fg="white",
            relief="flat",
            anchor="w",
            padx=30,
            pady=18,
            activebackground="#1E293B",
            cursor="hand2"
        )
        btn.pack(fill="x")

    def run_register(self):
        if os.path.exists(REGISTER_SCRIPT):
            subprocess.Popen(["python", REGISTER_SCRIPT])
        else:
            messagebox.showerror(
                "Error", f"File '{REGISTER_SCRIPT}' not found!")

    def run_attendance(self):
        if os.path.exists(MARK_ATTENDANCE_SCRIPT):
            # Wait until app.py finishes (user closes attendance window)
            subprocess.call(["python", MARK_ATTENDANCE_SCRIPT])
            # Then recompute today's count
            self.update_today_count()
        else:
            messagebox.showerror(
                "Error", f"File '{MARK_ATTENDANCE_SCRIPT}' not found!")

    def update_today_count(self):
        """
        Recalculate today's attendance count from attendance/attendance.csv
        and update the big label on the dashboard.
        """
        today = datetime.now().strftime("%Y-%m-%d")
        count = 0

        if os.path.exists(ATTENDANCE_PATH):
            with open(ATTENDANCE_PATH, "r", newline="") as f:
                reader = csv.reader(f)
                header = next(reader, None)  # skip header
                for row in reader:
                    # row format: [Name, Date, Time]
                    if len(row) >= 2 and row[1] == today:
                        count += 1

        self.count_label.config(text=f"{count} Person Present")


if __name__ == "__main__":
    root = tk.Tk()
    root.state("zoomed")
    app = MainDashboard(root)
    root.mainloop()
