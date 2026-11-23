"""Pure helpers for the maintenance feature (stdlib only, no frappe import)."""

import calendar
from datetime import date

DONE, ISSUE, NA = "Done", "Issue", "N/A"


def add_months(d: date, n: int) -> date:
	m = d.month - 1 + n
	y, m = d.year + m // 12, m % 12 + 1
	return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def month_start(d: date) -> date:
	return d.replace(day=1)


def compute_score(items) -> int:
	"""Weighted % of applicable checks that are Done. N/A is excluded; Issue and unchecked count against."""
	applicable = [i for i in items if i.status != NA]
	total = sum(i.weight or 1 for i in applicable)
	return round(sum(i.weight or 1 for i in applicable if i.status == DONE) * 100 / total) if total else 0


def score_label(score: int) -> str:
	return "Excellent" if score >= 90 else "Good" if score >= 75 else "Needs some work" if score >= 50 else "Poor"


def next_due(start: date, units_paid: int, cycle: str) -> date:
	"""Date the next payment falls due: start + units already paid (months or years)."""
	return add_months(start, units_paid * (12 if cycle == "Annual" else 1))


def payment_state(due: date, cycle: str, today: date) -> tuple[str, int]:
	"""-> ('overdue'|'due_soon'|'ok', days_until_due). Window: 7 days monthly, 30 days annual."""
	days = (due - today).days
	window = 30 if cycle == "Annual" else 7
	return ("overdue" if days < 0 else "due_soon" if days <= window else "ok"), days


def hours_in_month(logs, month: date) -> float:
	end = add_months(month_start(month), 1)
	return sum(l.hours or 0 for l in logs if month_start(month) <= l.date < end)
