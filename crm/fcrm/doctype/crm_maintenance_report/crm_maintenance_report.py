import frappe
from frappe.model.document import Document
from frappe.utils import getdate

from crm.maintenance.logic import compute_score, hours_in_month, month_start, score_label


class CRMMaintenanceReport(Document):
	def validate(self):
		self.month = month_start(getdate(self.month))
		client = frappe.get_doc("CRM Maintenance Client", self.client)
		if not self.items:
			self.copy_checks(client)
		self.score = compute_score(self.items)
		self.score_label = score_label(self.score)
		self.hours_used = hours_in_month([frappe._dict(date=getdate(l.date), hours=l.hours) for l in client.time_logs], self.month)
		self.hours_included = client.hours_included
		if self.status != "Sent":
			self.status = "Ready" if self.items and all(i.status for i in self.items) else "Draft"

	def copy_checks(self, client):
		services = {p.service for p in client.plans}
		checks = frappe.get_all(
			"CRM Maintenance Check", fields=["category", "label", "service", "weight"], order_by="sort, creation"
		)
		for c in checks:
			if not c.service or c.service in services:
				self.append("items", {"category": c.category, "item": c.label, "weight": c.weight})
		for c in client.checklist:
			self.append("items", {"category": c.category or "Other", "item": c.label, "weight": c.weight})
