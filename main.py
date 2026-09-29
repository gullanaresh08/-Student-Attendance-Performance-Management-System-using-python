"""Student Attendance & Performance Management System - Tkinter desktop app.

Run:  python main.py
"""
import tkinter as tk
from datetime import date
from tkinter import filedialog, messagebox, ttk

import charts
import database as dbm


def pct(value):
    return "-" if value is None else f"{value:.1f}%"


def make_tree(parent, columns, height=10):
    """columns = [(id, heading, width), ...]. Returns (frame, tree); caller packs the frame."""
    frame = ttk.Frame(parent)
    tree = ttk.Treeview(frame, columns=[c[0] for c in columns], show="headings", height=height)
    for cid, heading, width in columns:
        tree.heading(cid, text=heading)
        tree.column(cid, width=width, anchor="w" if cid == "name" else "center")
    scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    tree.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")
    tree.tag_configure("bad", foreground="#b91c1c")
    tree.tag_configure("good", foreground="#15803d")
    return frame, tree


def clear(tree):
    tree.delete(*tree.get_children())


def new_canvas(parent, height):
    return tk.Canvas(parent, height=height, bg="white", highlightthickness=1, highlightbackground="#d1d5db")


# ---------------------------------------------------------------- Dashboard
class DashboardTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app, self.subjects = app, []
        cards = ttk.Frame(self)
        cards.pack(fill="x", padx=10, pady=10)
        self.vars = {}
        for i, (key, label) in enumerate([("students", "Total students"), ("present", "Present today"),
                                          ("absent", "Absent today"), ("average", "Average performance")]):
            box = tk.Frame(cards, bg="#eff6ff", bd=1, relief="solid")
            box.grid(row=0, column=i, padx=6, sticky="nsew")
            cards.columnconfigure(i, weight=1)
            self.vars[key] = tk.StringVar(value="-")
            tk.Label(box, textvariable=self.vars[key], font=("Segoe UI", 22, "bold"),
                     bg="#eff6ff", fg="#1d4ed8").pack(pady=(8, 0))
            tk.Label(box, text=label, bg="#eff6ff").pack(pady=(0, 8))

        lists = ttk.Frame(self)
        lists.pack(fill="x", padx=10)
        left = ttk.LabelFrame(lists, text="Low attendance students (< 75%)")
        left.pack(side="left", fill="both", expand=True, padx=(0, 5))
        frame, self.low_tree = make_tree(left, [("name", "Name", 180), ("att", "Attendance", 90)], height=5)
        frame.pack(fill="both", expand=True, padx=5, pady=5)
        right = ttk.LabelFrame(lists, text="Top performers")
        right.pack(side="left", fill="both", expand=True, padx=(5, 0))
        frame, self.top_tree = make_tree(right, [("rank", "#", 40), ("name", "Name", 180), ("marks", "Marks", 80)],
                                         height=5)
        frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.canvas = new_canvas(self, 240)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)
        self.canvas.bind("<Configure>", lambda e: self.draw())

    def refresh(self):
        d = self.app.db.dashboard()
        self.vars["students"].set(d["students"])
        self.vars["present"].set(d["present"])
        self.vars["absent"].set(d["absent"])
        self.vars["average"].set(pct(d["average"]))
        clear(self.low_tree)
        for r in d["low_attendance"]:
            self.low_tree.insert("", "end", values=(r["name"], pct(r["attendance"])), tags=("bad",))
        clear(self.top_tree)
        for i, r in enumerate(d["top"], 1):
            self.top_tree.insert("", "end", values=(i, r["name"], pct(r["marks"])), tags=("good",))
        self.subjects = self.app.db.subject_averages()
        self.draw()

    def draw(self):
        charts.bar_chart(self.canvas, [s for s, _ in self.subjects], [v for _, v in self.subjects],
                         "Class average by subject (%)", threshold=dbm.PASS_MARK)


# ---------------------------------------------------------------- Students
class StudentsTab(ttk.Frame):
    FIELDS = (("roll", "Roll No"), ("name", "Name"), ("course", "Course"), ("phone", "Phone"))

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        form = ttk.LabelFrame(self, text="Student details")
        form.pack(fill="x", padx=10, pady=8)
        self.vars = {k: tk.StringVar() for k, _ in self.FIELDS}
        for i, (key, label) in enumerate(self.FIELDS):
            ttk.Label(form, text=label).grid(row=0, column=i * 2, padx=5, pady=8, sticky="e")
            ttk.Entry(form, textvariable=self.vars[key], width=16).grid(row=0, column=i * 2 + 1, padx=5)
        buttons = ttk.Frame(form)
        buttons.grid(row=1, column=0, columnspan=8, pady=(0, 8))
        for text, cmd in (("Add", self.add), ("Update", self.update), ("Delete", self.delete),
                          ("Profile", self.profile), ("Clear", self.clear_form)):
            ttk.Button(buttons, text=text, command=cmd).pack(side="left", padx=4)

        search = ttk.Frame(self)
        search.pack(fill="x", padx=10)
        ttk.Label(search, text="Search:").pack(side="left")
        self.query = tk.StringVar()
        self.query.trace_add("write", lambda *_: self.refresh())
        ttk.Entry(search, textvariable=self.query, width=30).pack(side="left", padx=6)

        frame, self.tree = make_tree(self, [("roll", "Roll", 90), ("name", "Name", 200), ("course", "Course", 140),
                                            ("phone", "Phone", 120), ("att", "Attendance", 90),
                                            ("marks", "Marks", 90)], height=14)
        frame.pack(fill="both", expand=True, padx=10, pady=8)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def refresh(self):
        clear(self.tree)
        db = self.app.db
        for s in db.list_students(self.query.get()):
            att, mp = db.attendance_pct(s["roll"]), db.overall_pct(s["roll"])
            tag = ("bad",) if att is not None and att < dbm.MIN_ATTENDANCE else ()
            self.tree.insert("", "end", iid=s["roll"], tags=tag,
                             values=(s["roll"], s["name"], s["course"], s["phone"], pct(att), pct(mp)))

    def on_select(self, _event=None):
        sel = self.tree.selection()
        if sel:
            v = self.tree.item(sel[0], "values")
            for key, val in zip(("roll", "name", "course", "phone"), v[:4]):
                self.vars[key].set(val)

    def clear_form(self):
        for v in self.vars.values():
            v.set("")

    def _run(self, action, done):
        try:
            action()
        except ValueError as exc:
            messagebox.showerror("Error", str(exc))
            return
        self.refresh()
        if done:
            messagebox.showinfo("Success", done)

    def add(self):
        v = {k: x.get() for k, x in self.vars.items()}
        self._run(lambda: self.app.db.add_student(v["roll"], v["name"], v["course"], v["phone"]), "Student added.")

    def update(self):
        v = {k: x.get() for k, x in self.vars.items()}
        self._run(lambda: self.app.db.update_student(v["roll"], v["name"], v["course"], v["phone"]),
                  "Student updated.")

    def delete(self):
        roll = self.vars["roll"].get().strip().upper()
        if roll and messagebox.askyesno("Confirm", f"Delete {roll} and all their records?"):
            self._run(lambda: self.app.db.delete_student(roll), None)
            self.clear_form()

    def profile(self):
        try:
            p = self.app.db.student_profile(self.vars["roll"].get().strip().upper())
        except ValueError as exc:
            messagebox.showerror("Error", str(exc))
            return
        lines = [f"{p['name']} ({p['roll']})", f"Course: {p['course'] or '-'}    Phone: {p['phone'] or '-'}", "",
                 f"Attendance: {pct(p['attendance'])}  (Present {p['present']}, Absent {p['absent']}, Leave {p['leave']})",
                 f"Overall marks: {pct(p['marks'])}   Grade: {p['grade']}   Result: {p['result']}",
                 f"Rank: {p['rank'] or '-'} of {p['ranked_total']}", f"Status: {p['flags']}", "", "Subject-wise:"]
        lines += [f"   {s}: {v:.1f}%" for s, v in p["subjects"]] or ["   no marks yet"]
        lines += ["", "Monthly attendance:"]
        lines += [f"   {m}: {v:.1f}%" for m, v in p["monthly"]] or ["   no attendance yet"]
        messagebox.showinfo("Student profile", "\n".join(lines))


# ---------------------------------------------------------------- Attendance
class AttendanceTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app, self.status = app, {}
        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=10, pady=8)
        ttk.Label(bar, text="Date (YYYY-MM-DD):").pack(side="left")
        self.day = tk.StringVar(value=date.today().isoformat())
        ttk.Entry(bar, textvariable=self.day, width=12).pack(side="left", padx=6)
        ttk.Button(bar, text="Load", command=self.load).pack(side="left", padx=4)
        ttk.Label(bar, text="   Mark selected as:").pack(side="left")
        for st in dbm.STATUSES:
            ttk.Button(bar, text=st, command=lambda s=st: self.set_selected(s)).pack(side="left", padx=2)
        ttk.Button(bar, text="All Present", command=self.all_present).pack(side="left", padx=(10, 2))
        ttk.Button(bar, text="Save Attendance", command=self.save).pack(side="right")

        frame, self.tree = make_tree(self, [("roll", "Roll", 90), ("name", "Name", 220), ("status", "Status", 100),
                                            ("pct", "Overall %", 100), ("warn", "Warning", 160)], height=18)
        frame.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        ttk.Label(self, text="Tip: Ctrl/Shift-click to select many students. Leave is excluded from the percentage."
                  ).pack(pady=(0, 6))

    def refresh(self):
        self.load()

    def load(self):
        try:
            day = dbm.valid_date(self.day.get())
        except ValueError as exc:
            messagebox.showerror("Error", str(exc))
            return
        saved = self.app.db.attendance_for_day(day)
        self.status = {s["roll"]: saved.get(s["roll"], "Present") for s in self.app.db.list_students()}
        clear(self.tree)
        for s in self.app.db.list_students():
            att = self.app.db.attendance_pct(s["roll"])
            low = att is not None and att < dbm.MIN_ATTENDANCE
            self.tree.insert("", "end", iid=s["roll"], tags=("bad",) if low else (),
                             values=(s["roll"], s["name"], self.status[s["roll"]], pct(att),
                                     "Below 75%!" if low else ""))

    def set_selected(self, st):
        for roll in self.tree.selection():
            self.status[roll] = st
            self.tree.set(roll, "status", st)

    def all_present(self):
        for roll in self.status:
            self.status[roll] = "Present"
            self.tree.set(roll, "status", "Present")

    def save(self):
        if not self.status:
            messagebox.showinfo("Attendance", "Add students first.")
            return
        try:
            self.app.db.save_attendance(self.day.get(), self.status)
        except ValueError as exc:
            messagebox.showerror("Error", str(exc))
            return
        messagebox.showinfo("Saved", f"Attendance saved for {self.day.get().strip()}.")
        self.load()


# ---------------------------------------------------------------- Marks
class MarksTab(ttk.Frame):
    EXAMS = ("Unit Test 1", "Unit Test 2", "Mid Term", "Assignment", "Final")

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        form = ttk.LabelFrame(self, text="Enter marks")
        form.pack(fill="x", padx=10, pady=8)
        ttk.Label(form, text="Student").grid(row=0, column=0, padx=5, pady=8, sticky="e")
        self.student = ttk.Combobox(form, state="readonly", width=28)
        self.student.grid(row=0, column=1, padx=5)
        self.student.bind("<<ComboboxSelected>>", lambda e: self.load())
        self.subject, self.exam = tk.StringVar(), tk.StringVar(value=self.EXAMS[2])
        self.score, self.max = tk.StringVar(), tk.StringVar(value="100")
        ttk.Label(form, text="Subject").grid(row=0, column=2, padx=5, sticky="e")
        ttk.Entry(form, textvariable=self.subject, width=14).grid(row=0, column=3, padx=5)
        ttk.Label(form, text="Exam").grid(row=1, column=0, padx=5, pady=8, sticky="e")
        ttk.Combobox(form, textvariable=self.exam, values=self.EXAMS, width=26).grid(row=1, column=1, padx=5)
        ttk.Label(form, text="Score").grid(row=1, column=2, padx=5, sticky="e")
        ttk.Entry(form, textvariable=self.score, width=8).grid(row=1, column=3, padx=5, sticky="w")
        ttk.Label(form, text="Max").grid(row=1, column=4, padx=5, sticky="e")
        ttk.Entry(form, textvariable=self.max, width=8).grid(row=1, column=5, padx=5, sticky="w")
        ttk.Button(form, text="Save Marks", command=self.save).grid(row=0, column=6, padx=10)
        ttk.Button(form, text="Delete Selected", command=self.delete).grid(row=1, column=6, padx=10)

        frame, self.tree = make_tree(self, [("subject", "Subject", 150), ("exam", "Exam", 130), ("score", "Score", 80),
                                            ("max", "Max", 80), ("pct", "Percent", 90), ("grade", "Grade", 70)],
                                     height=12)
        frame.pack(fill="both", expand=True, padx=10, pady=8)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.summary = tk.StringVar()
        ttk.Label(self, textvariable=self.summary, font=("Segoe UI", 11, "bold")).pack(pady=(0, 10))
        self.rolls = []

    def refresh(self):
        students = self.app.db.list_students()
        self.rolls = [s["roll"] for s in students]
        self.student["values"] = [f"{s['roll']} - {s['name']}" for s in students]
        if self.rolls and self.student.current() < 0:
            self.student.current(0)
        self.load()

    def current_roll(self):
        idx = self.student.current()
        return self.rolls[idx] if 0 <= idx < len(self.rolls) else None

    def load(self):
        clear(self.tree)
        roll = self.current_roll()
        if not roll:
            self.summary.set("Add a student first.")
            return
        for m in self.app.db.marks_for(roll):
            p = m["score"] / m["max_score"] * 100
            self.tree.insert("", "end", iid=str(m["id"]), tags=("bad",) if p < dbm.PASS_MARK else (),
                             values=(m["subject"], m["exam"], m["score"], m["max_score"], f"{p:.1f}%", dbm.grade(p)))
        row = next(r for r in self.app.db.class_table() if r["roll"] == roll)
        self.summary.set(f"Overall {pct(row['marks'])} | Grade {row['grade']} | Result {row['result']} | "
                         f"Rank {row['rank'] or '-'}")

    def on_select(self, _event=None):
        sel = self.tree.selection()
        if sel:
            v = self.tree.item(sel[0], "values")
            self.subject.set(v[0])
            self.exam.set(v[1])
            self.score.set(v[2])
            self.max.set(v[3])

    def save(self):
        roll = self.current_roll()
        if not roll:
            return
        try:
            self.app.db.add_marks(roll, self.subject.get(), self.exam.get(), self.score.get(), self.max.get())
        except ValueError as exc:
            messagebox.showerror("Error", str(exc))
            return
        self.score.set("")
        self.load()

    def delete(self):
        for iid in self.tree.selection():
            self.app.db.delete_marks(int(iid))
        self.load()


# ---------------------------------------------------------------- Reports
class ReportsTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app, self.mode, self.data = app, "attendance", None
        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=10, pady=8)
        for text, mode in (("Attendance chart", "attendance"), ("Performance chart", "marks"),
                           ("Attendance vs Marks", "scatter")):
            ttk.Button(bar, text=text, command=lambda m=mode: self.set_mode(m)).pack(side="left", padx=3)
        ttk.Button(bar, text="Backup DB", command=app.backup).pack(side="right", padx=3)
        ttk.Button(bar, text="Export CSV", command=app.export_csv).pack(side="right", padx=3)

        frame, self.tree = make_tree(self, [("rank", "Rank", 50), ("roll", "Roll", 80), ("name", "Name", 180),
                                            ("att", "Attendance", 90), ("marks", "Marks", 80), ("grade", "Grade", 60),
                                            ("result", "Result", 60), ("flags", "Status", 170)], height=7)
        frame.pack(fill="x", padx=10)
        self.canvas = new_canvas(self, 230)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=8)
        self.canvas.bind("<Configure>", lambda e: self.draw())
        self.info = tk.StringVar()
        ttk.Label(self, textvariable=self.info, wraplength=950, justify="left").pack(fill="x", padx=10)
        self.risk = tk.Text(self, height=5, wrap="word", bg="#fef2f2")
        self.risk.pack(fill="x", padx=10, pady=8)

    def set_mode(self, mode):
        self.mode = mode
        self.draw()

    def refresh(self):
        table = self.app.db.class_table()
        self.data = {"table": table, "analysis": self.app.db.analysis()}
        clear(self.tree)
        for r in table:
            bad = r["flags"] != "OK"
            self.tree.insert("", "end", tags=("bad",) if bad else (),
                             values=(r["rank"] or "-", r["roll"], r["name"], pct(r["attendance"]),
                                     pct(r["marks"]), r["grade"], r["result"], r["flags"]))
        a = self.data["analysis"]
        if a["correlation"] is None:
            self.info.set("Correlation: not enough data (need 3+ students with attendance and marks).")
        else:
            r = a["correlation"]
            strength = "strong" if abs(r) >= 0.7 else "moderate" if abs(r) >= 0.4 else "weak"
            direction = "positive" if r > 0 else "negative"
            self.info.set(f"Correlation between attendance and marks: r = {r:.2f} ({strength} {direction}). "
                          + (f"Each extra 10% attendance is linked with {a['fit'][0] * 10:+.1f}% marks."
                             if a["fit"] else ""))
        self.risk.configure(state="normal")
        self.risk.delete("1.0", "end")
        if a["risk"]:
            self.risk.insert("end", "Students at risk:\n")
            for r in a["risk"]:
                self.risk.insert("end", f"[{r['level']}] {r['name']} ({r['roll']}): {r['reasons']}\n")
        else:
            self.risk.insert("end", "No at-risk students detected.")
        self.risk.configure(state="disabled")
        self.draw()

    def draw(self):
        if not self.data:
            return
        table = self.data["table"]
        names = [r["name"].split()[0] for r in table]
        if self.mode == "attendance":
            charts.bar_chart(self.canvas, names, [r["attendance"] or 0 for r in table],
                             "Attendance % per student", threshold=dbm.MIN_ATTENDANCE)
        elif self.mode == "marks":
            charts.bar_chart(self.canvas, names, [r["marks"] or 0 for r in table],
                             "Overall marks % per student", threshold=dbm.PASS_MARK)
        else:
            a = self.data["analysis"]
            charts.scatter_chart(self.canvas, a["points"], a["fit"], "Attendance vs Marks (with trend line)")


# ---------------------------------------------------------------- Application
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Student Attendance & Performance Management System")
        self.geometry("1020x720")
        self.minsize(900, 640)
        self.db = dbm.Database()

        menu = tk.Menu(self)
        file_menu = tk.Menu(menu, tearoff=0)
        file_menu.add_command(label="Load sample data", command=self.load_sample)
        file_menu.add_command(label="Export report to CSV", command=self.export_csv)
        file_menu.add_command(label="Backup database", command=self.backup)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)
        menu.add_cascade(label="File", menu=file_menu)
        self.config(menu=menu)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)
        self.tabs = {}
        for title, cls in (("Dashboard", DashboardTab), ("Students", StudentsTab), ("Attendance", AttendanceTab),
                           ("Marks", MarksTab), ("Reports & Analysis", ReportsTab)):
            tab = cls(self.notebook, self)
            self.notebook.add(tab, text=title)
            self.tabs[title] = tab
        self.notebook.bind("<<NotebookTabChanged>>", lambda e: self.notebook.nametowidget(
            self.notebook.select()).refresh())
        self.after(100, self.tabs["Dashboard"].refresh)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def load_sample(self):
        self.db.load_sample_data()
        self.notebook.nametowidget(self.notebook.select()).refresh()
        messagebox.showinfo("Sample data", "10 demo students with attendance and marks were added.")

    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="class_report.csv",
                                            filetypes=[("CSV file", "*.csv")])
        if path:
            self.db.export_csv(path)
            messagebox.showinfo("Export", f"Report saved to:\n{path}")

    def backup(self):
        folder = filedialog.askdirectory(title="Choose backup folder")
        if folder:
            messagebox.showinfo("Backup", f"Database backed up to:\n{self.db.backup(folder)}")


if __name__ == "__main__":
    App().mainloop()
