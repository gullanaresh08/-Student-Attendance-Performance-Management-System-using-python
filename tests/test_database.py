import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database as dbm  # noqa: E402


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db = dbm.Database(os.path.join(self.tmp, "test.db"))

    def tearDown(self):
        self.db.close()

    def test_student_crud(self):
        self.db.add_student("cs1", "asha rao", "CSE", "123")
        self.assertEqual(self.db.list_students()[0]["roll"], "CS1")
        with self.assertRaises(ValueError):
            self.db.add_student("CS1", "Dup")
        self.db.update_student("CS1", "Asha R", "IT", "999")
        self.assertEqual(self.db.list_students("asha")[0]["course"], "IT")
        self.db.delete_student("CS1")
        self.assertEqual(self.db.list_students(), [])

    def test_attendance_percentage_excludes_leave(self):
        self.db.add_student("A1", "Test")
        for i, st in enumerate(["Present", "Present", "Absent", "Leave"], 1):
            self.db.save_attendance(f"2026-09-0{i}", {"A1": st})
        self.assertAlmostEqual(self.db.attendance_pct("A1"), 66.666, places=2)

    def test_marks_grade_and_rank(self):
        self.db.add_student("A1", "High")
        self.db.add_student("A2", "Low")
        self.db.add_marks("A1", "Python", "Final", 92, 100)
        self.db.add_marks("A2", "Python", "Final", 30, 100)
        table = {r["roll"]: r for r in self.db.class_table()}
        self.assertEqual(table["A1"]["grade"], "A+")
        self.assertEqual(table["A1"]["rank"], 1)
        self.assertEqual(table["A2"]["result"], "Fail")
        with self.assertRaises(ValueError):
            self.db.add_marks("A1", "Python", "Mid", 150, 100)

    def test_cascade_delete(self):
        self.db.add_student("A1", "Test")
        self.db.add_marks("A1", "Maths", "Final", 50, 100)
        self.db.save_attendance("2026-09-01", {"A1": "Present"})
        self.db.delete_student("A1")
        self.assertEqual(self.db.subject_averages(), [])
        self.assertEqual(self.db.attendance_for_day("2026-09-01"), {})

    def test_sample_data_analysis_and_export(self):
        self.db.load_sample_data()
        self.assertEqual(len(self.db.list_students()), 10)
        a = self.db.analysis()
        self.assertIsNotNone(a["correlation"])
        self.assertGreater(a["correlation"], 0.5)
        out = os.path.join(self.tmp, "r.csv")
        self.db.export_csv(out)
        self.assertTrue(os.path.getsize(out) > 0)
        self.assertTrue(os.path.exists(self.db.backup(self.tmp)))

    def test_stats_helpers(self):
        self.assertAlmostEqual(dbm.pearson([1, 2, 3], [2, 4, 6]), 1.0)
        self.assertEqual(dbm.linear_fit([1, 2, 3], [2, 4, 6]), (2.0, 0.0))
        self.assertIsNone(dbm.pearson([1, 1, 1], [1, 2, 3]))


if __name__ == "__main__":
    unittest.main()
