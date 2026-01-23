import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import csv
from datetime import datetime
from fpdf import FPDF

# ---- PATH CONFIGURATION ----
REGISTER_SCRIPT = "register_face.py"
MARK_ATTENDANCE_SCRIPT = "mark.py" 
ATTENDANCE_PATH = os.path.join("attendance", "attendance.csv")

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

        # Top Toolbar
        toolbar = tk.Frame(self, bg=COLORS["card"], pady=10)
        toolbar.pack(fill="x")
        
        tk.Button(toolbar, text="📅 Today", command=self.load_today, bg=COLORS["sidebar"], fg="white").pack(side="left", padx=20)
        tk.Button(toolbar, text="📊 All Records", command=self.load_all, bg=COLORS["sidebar"], fg="white").pack(side="left")
        tk.Button(toolbar, text="📥 DOWNLOAD PDF", command=self.export_pdf, bg=COLORS["success"], fg="white", font=("Segoe UI", 9, "bold")).pack(side="right", padx=20)

        # Treeview Table
        style = ttk.Style()
        style.configure("Treeview", rowheight=30)
        
        self.tree = ttk.Treeview(self, columns=("Name", "Date", "Time"), show="headings")
        self.tree.heading("Name", text="Student Name")
        self.tree.heading("Date", text="Date")
        self.tree.heading("Time", text="Check-in Time")
        self.tree.pack(fill="both", expand=True, padx=20, pady=20)

        self.load_all()

    def get_data(self):
        if not os.path.exists(ATTENDANCE_PATH): return []
        with open(ATTENDANCE_PATH, "r") as f:
            reader = csv.reader(f)
            next(reader, None)
            return list(reader)

    def load_all(self):
        self.update_table(self.get_data())

    def load_today(self):
        today = datetime.now().strftime("%Y-%m-%d")
        data = [row for row in self.get_data() if row[1] == today]
        self.update_table(data)

    def update_table(self, rows):
        self.tree.delete(*self.tree.get_children())
        for r in rows: self.tree.insert("", "end", values=r)

    def export_pdf(self):
        items = self.tree.get_children()
        if not items: 
            messagebox.showwarning("Warning", "No data available to export!")
            return
            
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if path:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, "Attendance Report", ln=True, align='C')
            pdf.ln(10)
            
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(80, 10, "Name", 1); pdf.cell(50, 10, "Date", 1); pdf.cell(50, 10, "Time", 1)
            pdf.ln()

            pdf.set_font("Arial", size=12)
            for i in items:
                v = self.tree.item(i)['values']
                pdf.cell(80, 10, str(v[0]), 1); pdf.cell(50, 10, str(v[1]), 1); pdf.cell(50, 10, str(v[2]), 1)
                pdf.ln()
            
            pdf.output(path)
            messagebox.showinfo("Success", "PDF Report downloaded successfully!")

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

        tk.Label(sidebar, text="SYSTEM MENU", font=("Segoe UI", 10, "bold"), bg=COLORS["sidebar"], fg="#64748B").pack(pady=40)

        # Menu Buttons
        self.create_menu_btn(sidebar, "👤 Register Face", self.run_register)
        self.create_menu_btn(sidebar, "📸 Mark Attendance", self.run_attendance)
        self.create_menu_btn(sidebar, "📊 View Reports", lambda: ReportWindow(self.root))

        # Main Content Area
        main = tk.Frame(self.root, bg=COLORS["bg"])
        main.pack(side="right", fill="both", expand=True, padx=40, pady=40)

        tk.Label(main, text="Welcome Back,", font=("Segoe UI", 14), bg=COLORS["bg"], fg="#64748B").pack(anchor="w")
        tk.Label(main, text="Smart Attendance Dashboard", font=("Segoe UI", 26, "bold"), bg=COLORS["bg"], fg=COLORS["text"]).pack(anchor="w", pady=(0, 30))

        # Quick Status Card
        card = tk.Frame(main, bg=COLORS["card"], padx=30, pady=30, highlightthickness=1, highlightbackground=COLORS["border"])
        card.pack(fill="x")
        
        # Today's attendance count logic
        count = 0
        if os.path.exists(ATTENDANCE_PATH):
            today = datetime.now().strftime("%Y-%m-%d")
            with open(ATTENDANCE_PATH, "r") as f:
                count = sum(1 for line in f if today in line)

        tk.Label(card, text="Today's Attendance Count", font=("Segoe UI", 12), bg=COLORS["card"], fg="#64748B").pack(anchor="w")
        tk.Label(card, text=f"{count} Students Present", font=("Segoe UI", 32, "bold"), bg=COLORS["card"], fg=COLORS["accent"]).pack(anchor="w", pady=10)

    def create_menu_btn(self, parent, text, cmd):
        btn = tk.Button(parent, text=text, command=cmd, font=("Segoe UI", 11), bg=COLORS["sidebar"], fg="white", 
                        relief="flat", anchor="w", padx=30, pady=18, activebackground="#1E293B", cursor="hand2")
        btn.pack(fill="x")

    def run_register(self):
        if os.path.exists(REGISTER_SCRIPT):
            subprocess.Popen(["python", REGISTER_SCRIPT])
        else:
            messagebox.showerror("Error", f"File '{REGISTER_SCRIPT}' not found!")

    def run_attendance(self):
        if os.path.exists(MARK_ATTENDANCE_SCRIPT):
            subprocess.Popen(["python", MARK_ATTENDANCE_SCRIPT])
        else:
            messagebox.showerror("Error", f"File '{MARK_ATTENDANCE_SCRIPT}' not found!")

if __name__ == "__main__":
    root = tk.Tk()
    app = MainDashboard(root)
    root.mainloop()