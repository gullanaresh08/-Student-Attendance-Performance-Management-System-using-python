"""Database + business logic for the Student Attendance & Performance Management System.

Pure Python standard library only (sqlite3, csv, statistics, math).
"""
import csv
import math
import os
import random
import sqlite3
from datetime import date, datetime, timedelta

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "student_management.db")
MIN_ATTENDANCE = 75.0
PASS_MARK = 40.0
STATUSES = ("Present", "Absent", "Leave")

SCHEMA = """
CREATE TABLE IF NOT EXISTS students(
    roll   TEXT PRIMARY KEY,
    name   TEXT NOT NULL,
    course TEXT DEFAULT '',
    phone  TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS attendance(
    roll   TEXT NOT NULL REFERENCES students(roll) ON DELETE CASCADE,
    day    TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('Present','Absent','Leave')),
    PRIMARY KEY(roll, day)
);
CREATE TABLE IF NOT EXISTS marks(
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    roll      TEXT NOT NULL REFERENCES students(roll) ON DELETE CASCADE,
    subject   TEXT NOT NULL,
    exam      TEXT NOT NULL,
    score     REAL NOT NULL,
    max_score REAL NOT NULL CHECK(max_score > 0),
    UNIQUE(roll, subject, exam)
);
"""


# ---------- pure helper functions ----------
def grade(pct):
    """Convert a percentage into a letter grade."""
    if pct is None:
        return "-"
    for cutoff, letter in ((90, "A+"), (80, "A"), (70, "B"), (60, "C"), (50, "D"), (PASS_MARK, "E")):
        if pct >= cutoff:
            return letter
    return "F"


def valid_date(text):
    try:
        return datetime.strptime(text.strip(), "%Y-%m-%d").date().isoformat()
    except ValueError:
        raise ValueError("Date must be in YYYY-MM-DD format.")


def pearson(xs, ys):
    """Pearson correlation coefficient (None if it cannot be computed)."""
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    if sxx == 0 or syy == 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def linear_fit(xs, ys):
    """Least-squares line y = slope*x + intercept (None if not enough data)."""
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return None
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    return slope, my - slope * mx


# ---------- database class ----------
class Database:
    def __init__(self, path=DB_FILE):
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)

    def close(self):
        self.conn.close()

    # ----- students -----
    def add_student(self, roll, name, course="", phone=""):
        roll, name = roll.strip().upper(), name.strip().title()
        if not roll or not name:
            raise ValueError("Roll number and name are required.")
        try:
            self.conn.execute("INSERT INTO students VALUES(?,?,?,?)",
                              (roll, name, course.strip(), phone.strip()))
            self.conn.commit()
        except sqlite3.IntegrityError:
            raise ValueError(f"Roll number {roll} already exists.")

    def update_student(self, roll, name, course="", phone=""):
        if not name.strip():
            raise ValueError("Name is required.")
        cur = self.conn.execute("UPDATE students SET name=?, course=?, phone=? WHERE roll=?",
                                (name.strip().title(), course.strip(), phone.strip(), roll.strip().upper()))
        self.conn.commit()
        if cur.rowcount == 0:
            raise ValueError("Student not found.")

    def delete_student(self, roll):
        cur = self.conn.execute("DELETE FROM students WHERE roll=?", (roll.strip().upper(),))
        self.conn.commit()
        if cur.rowcount == 0:
            raise ValueError("Student not found.")

    def list_students(self, query=""):
        like = f"%{query.strip()}%"
        rows = self.conn.execute(
            "SELECT * FROM students WHERE roll LIKE ? OR name LIKE ? OR course LIKE ? ORDER BY roll",
            (like, like, like)).fetchall()
        return [dict(r) for r in rows]

    # ----- attendance -----
    def save_attendance(self, day, statuses):
        day = valid_date(day)
        self.conn.executemany("INSERT OR REPLACE INTO attendance VALUES(?,?,?)",
                              [(roll, day, st) for roll, st in statuses.items()])
        self.conn.commit()

    def attendance_for_day(self, day):
        rows = self.conn.execute("SELECT roll, status FROM attendance WHERE day=?", (day,)).fetchall()
        return {r["roll"]: r["status"] for r in rows}

    def attendance_counts(self, roll):
        r = self.conn.execute(
            "SELECT COALESCE(SUM(status='Present'),0) p, COALESCE(SUM(status='Absent'),0) a,"
            " COALESCE(SUM(status='Leave'),0) l FROM attendance WHERE roll=?", (roll,)).fetchone()
        return r["p"], r["a"], r["l"]

    def attendance_pct(self, roll):
        """Present / (Present + Absent). Approved leave is excluded from the calculation."""
        p, a, _ = self.attendance_counts(roll)
        return p / (p + a) * 100 if p + a else None

    def monthly_attendance(self, roll):
        rows = self.conn.execute(
            "SELECT substr(day,1,7) m, SUM(status='Present') p, SUM(status='Absent') a"
            " FROM attendance WHERE roll=? GROUP BY m HAVING p+a>0 ORDER BY m", (roll,)).fetchall()
        return [(r["m"], r["p"] / (r["p"] + r["a"]) * 100) for r in rows]

    # ----- marks -----
    def add_marks(self, roll, subject, exam, score, max_score):
        subject, exam = subject.strip().title(), exam.strip().title()
        if not subject or not exam:
            raise ValueError("Subject and exam are required.")
        try:
            score, max_score = float(score), float(max_score)
        except ValueError:
            raise ValueError("Score and max score must be numbers.")
        if max_score <= 0 or not 0 <= score <= max_score:
            raise ValueError("Score must be between 0 and the maximum score.")
        self.conn.execute("INSERT OR REPLACE INTO marks(roll,subject,exam,score,max_score) VALUES(?,?,?,?,?)",
                          (roll, subject, exam, score, max_score))
        self.conn.commit()

    def marks_for(self, roll):
        rows = self.conn.execute("SELECT * FROM marks WHERE roll=? ORDER BY subject, exam", (roll,)).fetchall()
        return [dict(r) for r in rows]

    def delete_marks(self, mark_id):
        self.conn.execute("DELETE FROM marks WHERE id=?", (mark_id,))
        self.conn.commit()

    def overall_pct(self, roll):
        r = self.conn.execute("SELECT SUM(score) s, SUM(max_score) m FROM marks WHERE roll=?", (roll,)).fetchone()
        return r["s"] / r["m"] * 100 if r["m"] else None

    def subject_pct(self, roll):
        rows = self.conn.execute(
            "SELECT subject, SUM(score)*100.0/SUM(max_score) p FROM marks WHERE roll=? GROUP BY subject ORDER BY subject",
            (roll,)).fetchall()
        return [(r["subject"], r["p"]) for r in rows]

    def subject_averages(self):
        rows = self.conn.execute(
            "SELECT subject, SUM(score)*100.0/SUM(max_score) p FROM marks GROUP BY subject ORDER BY subject").fetchall()
        return [(r["subject"], r["p"]) for r in rows]

    # ----- reports -----
    def class_table(self):
        rows = []
        for s in self.list_students():
            att, mp = self.attendance_pct(s["roll"]), self.overall_pct(s["roll"])
            flags = []
            if att is not None and att < MIN_ATTENDANCE:
                flags.append("Low attendance")
            if mp is not None and mp < PASS_MARK:
                flags.append("Failing")
            rows.append({**s, "attendance": att, "marks": mp, "grade": grade(mp),
                         "result": "-" if mp is None else ("Pass" if mp >= PASS_MARK else "Fail"),
                         "flags": ", ".join(flags) or "OK", "rank": None})
        ranked = sorted((r for r in rows if r["marks"] is not None), key=lambda r: -r["marks"])
        for i, r in enumerate(ranked):
            # ties share a rank
            r["rank"] = ranked[i - 1]["rank"] if i and abs(ranked[i - 1]["marks"] - r["marks"]) < 1e-9 else i + 1
        return rows

    def student_profile(self, roll):
        table = self.class_table()
        row = next((r for r in table if r["roll"] == roll), None)
        if not row:
            raise ValueError("Student not found.")
        p, a, l = self.attendance_counts(roll)
        return {**row, "present": p, "absent": a, "leave": l,
                "subjects": self.subject_pct(roll), "monthly": self.monthly_attendance(roll),
                "ranked_total": sum(1 for r in table if r["rank"] is not None)}

    def dashboard(self):
        today = date.today().isoformat()
        counts = {st: 0 for st in STATUSES}
        for st in self.attendance_for_day(today).values():
            counts[st] += 1
        table = self.class_table()
        marked = [r["marks"] for r in table if r["marks"] is not None]
        return {
            "students": len(table),
            "present": counts["Present"], "absent": counts["Absent"], "leave": counts["Leave"],
            "average": sum(marked) / len(marked) if marked else None,
            "low_attendance": [r for r in table if r["attendance"] is not None and r["attendance"] < MIN_ATTENDANCE],
            "top": sorted((r for r in table if r["marks"] is not None), key=lambda r: -r["marks"])[:3],
        }

    def analysis(self):
        """Correlation between attendance & marks + rule/regression based risk detection."""
        table = self.class_table()
        pts = [(r["attendance"], r["marks"], r["name"]) for r in table
               if r["attendance"] is not None and r["marks"] is not None]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        fit = linear_fit(xs, ys)
        risk = []
        for r in table:
            reasons, predicted = [], None
            att, mp = r["attendance"], r["marks"]
            if att is not None and att < MIN_ATTENDANCE:
                reasons.append(f"attendance {att:.0f}% is below {MIN_ATTENDANCE:.0f}%")
            if mp is not None and mp < PASS_MARK:
                reasons.append(f"marks {mp:.0f}% are below the pass mark")
            if fit and att is not None:
                predicted = max(0.0, min(100.0, fit[0] * att + fit[1]))
                if predicted < PASS_MARK + 10 and not (mp is not None and mp < PASS_MARK):
                    reasons.append(f"predicted score from attendance is only {predicted:.0f}%")
            if reasons:
                risk.append({"roll": r["roll"], "name": r["name"], "level": "High" if len(reasons) > 1 else "Medium",
                             "reasons": "; ".join(reasons), "predicted": predicted})
        risk.sort(key=lambda x: (x["level"] != "High", x["name"]))
        return {"points": pts, "correlation": pearson(xs, ys), "fit": fit, "risk": risk}

    # ----- export / backup / demo data -----
    def export_csv(self, path):
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["rank", "roll", "name", "course", "attendance_pct", "marks_pct", "grade", "result", "status"])
            for r in self.class_table():
                w.writerow([r["rank"] or "", r["roll"], r["name"], r["course"],
                            "" if r["attendance"] is None else round(r["attendance"], 1),
                            "" if r["marks"] is None else round(r["marks"], 1),
                            r["grade"], r["result"], r["flags"]])

    def backup(self, folder):
        dest = os.path.join(folder, f"backup_{datetime.now():%Y%m%d_%H%M%S}.db")
        target = sqlite3.connect(dest)
        self.conn.backup(target)
        target.close()
        return dest

    def load_sample_data(self):
        """Insert 10 demo students with 20 school days of attendance and two exams in 4 subjects."""
        rnd = random.Random(7)
        names = ["Aarav Kumar", "Diya Sharma", "Rahul Reddy", "Sneha Patel", "Kiran Rao",
                 "Priya Nair", "Vikram Singh", "Ananya Das", "Rohit Verma", "Meera Iyer"]
        days, d = [], date.today()
        while len(days) < 20:
            if d.weekday() < 5:
                days.append(d.isoformat())
            d -= timedelta(days=1)
        for i, name in enumerate(names, 1):
            roll = f"CS{i:03d}"
            self.conn.execute("INSERT OR IGNORE INTO students VALUES(?,?,?,?)",
                              (roll, name, "B.Tech CSE", f"98765{i:05d}"))
            ability = rnd.uniform(0.3, 0.95)
            p_present = min(0.98, 0.45 + ability * 0.55)
            for day in days:
                r = rnd.random()
                st = "Present" if r < p_present else ("Leave" if r < p_present + 0.03 else "Absent")
                self.conn.execute("INSERT OR IGNORE INTO attendance VALUES(?,?,?)", (roll, day, st))
            for subject in ("Python", "SQL", "Maths", "English"):
                for exam in ("Mid Term", "Final"):
                    score = max(5, min(100, round(ability * 100 + rnd.uniform(-12, 12))))
                    self.conn.execute(
                        "INSERT OR IGNORE INTO marks(roll,subject,exam,score,max_score) VALUES(?,?,?,?,100)",
                        (roll, subject, exam, score))
        self.conn.commit()
