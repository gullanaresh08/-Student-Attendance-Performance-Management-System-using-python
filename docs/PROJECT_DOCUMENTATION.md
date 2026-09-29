# Project Documentation

## 1. Objective
Replace paper registers with a desktop tool that records attendance and marks, calculates percentages, grades and ranks, and warns about students at risk.

## 2. Technology
- Python 3 (only language used)
- Tkinter: GUI
- SQLite (sqlite3 module): database
- csv, math, random, datetime: export, statistics, demo data, dates
- Canvas drawing: charts

## 3. Architecture
Three layers:
1. Presentation: `main.py` (tabs, forms, tables) and `charts.py`
2. Logic: `database.py` (grades, percentages, ranking, correlation, regression)
3. Data: SQLite file `student_management.db`

## 4. Database design
- students(roll PK, name, course, phone)
- attendance(roll FK, day, status) with PK (roll, day)
- marks(id PK, roll FK, subject, exam, score, max_score) with UNIQUE (roll, subject, exam)
Foreign keys use ON DELETE CASCADE, so deleting a student removes their records.

## 5. Key algorithms
- Attendance %: present / (present + absent) x 100
- Overall marks %: sum of scores / sum of max scores x 100
- Pearson correlation r between attendance and marks
- Least-squares line: marks = slope x attendance + intercept, used to predict performance
- Risk level: High if 2+ reasons, Medium if 1

## 6. Testing
`python -m unittest discover -s tests` covers CRUD, attendance maths, grading and ranking, cascade delete, analytics, CSV export and backup.

## 7. Future scope
Login for teachers, matplotlib/pandas reports, email alerts, Flask web version, machine learning model.
