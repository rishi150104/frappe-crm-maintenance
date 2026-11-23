import unittest
from datetime import date
from types import SimpleNamespace as N

from crm.maintenance import logic as L


class TestLogic(unittest.TestCase):
	def test_score(self):
		items = [N(status="Done", weight=1), N(status="Issue", weight=1), N(status="N/A", weight=5), N(status="", weight=2)]
		self.assertEqual(L.compute_score(items), 25)  # 1 / (1+1+2)
		self.assertEqual(L.compute_score([]), 0)
		self.assertEqual(L.score_label(70), "Needs some work")

	def test_dates(self):
		self.assertEqual(L.add_months(date(2026, 1, 31), 1), date(2026, 2, 28))
		self.assertEqual(L.next_due(date(2026, 11, 16), 0, "Monthly"), date(2026, 11, 16))
		self.assertEqual(L.next_due(date(2026, 11, 16), 2, "Annual"), date(2028, 11, 16))
		self.assertEqual(L.payment_state(date(2026, 11, 16), "Monthly", date(2026, 11, 23)), ("overdue", -7))
		self.assertEqual(L.payment_state(date(2026, 12, 16), "Monthly", date(2026, 11, 23))[0], "ok")
		self.assertEqual(L.payment_state(date(2026, 12, 16), "Annual", date(2026, 11, 23))[0], "due_soon")

	def test_hours(self):
		logs = [N(date=date(2026, 11, 5), hours=2), N(date=date(2026, 12, 1), hours=9)]
		self.assertEqual(L.hours_in_month(logs, date(2026, 11, 20)), 2)


if __name__ == "__main__":
	unittest.main()
