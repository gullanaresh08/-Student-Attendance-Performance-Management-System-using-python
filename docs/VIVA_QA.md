# Viva Questions and Answers

1. **What is the project about?** A desktop app that manages student records, attendance and marks, and shows reports and at-risk students.
2. **Why Python?** Simple, readable, and has built-in support for GUI (Tkinter), databases (sqlite3) and CSV.
3. **Why SQLite?** Serverless, one file, built into Python, ideal for small desktop apps.
4. **Why Tkinter?** Standard GUI library that ships with Python, so nothing extra to install.
5. **How is attendance percentage calculated?** Present divided by (Present + Absent) times 100. Leave is excluded.
6. **What happens if attendance is below 75%?** The student is highlighted in red and appears in the dashboard's low-attendance list.
7. **How are ranks decided?** By overall marks percentage, highest first. Equal marks share the same rank.
8. **What is a foreign key and where is it used?** A column linking to another table's primary key. attendance.roll and marks.roll refer to students.roll.
9. **What does ON DELETE CASCADE do?** Deleting a student automatically deletes their attendance and marks.
10. **What is INSERT OR REPLACE used for?** Re-saving attendance for a date, or re-entering marks for the same subject and exam, updates the old record instead of duplicating.
11. **How do you find at-risk students?** Rules (low attendance, failing marks) plus a regression line that predicts marks from attendance.
12. **What is correlation?** A number from -1 to 1 showing how strongly two values move together. Here it shows the link between attendance and marks.
13. **What is linear regression?** Fitting the best straight line through the data so we can predict marks for a given attendance.
14. **How did you draw charts without matplotlib?** Using Tkinter Canvas primitives (rectangles, lines, ovals and text).
15. **How do you prevent bad input?** Validation raises ValueError for empty fields, wrong dates, and scores outside 0 to max; the GUI shows an error box.
16. **How do you back up data?** SQLite's backup API copies the live database to a timestamped file.
17. **How did you test it?** Unit tests with unittest on a temporary database.
18. **What are the limitations?** Single user, no login, desktop only.
19. **What improvements are possible?** Teacher login, email alerts, web version, machine learning prediction.
20. **What is the role of each file?** main.py is the GUI, database.py is data and logic, charts.py draws charts.
