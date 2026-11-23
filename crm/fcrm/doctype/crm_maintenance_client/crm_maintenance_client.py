import frappe
from frappe.model.document import Document
from frappe.utils import getdate

from crm.maintenance.logic import next_due


class CRMMaintenanceClient(Document):
	def validate(self):
		for row in self.plans:
			if not row.custom and row.plan:  # catalog plan: copy price/hours/deliverables
				p = frappe.get_doc("CRM Maintenance Plan", row.plan)
				row.monthly_price, row.annual_price, row.hours_per_month = p.monthly_price, p.annual_price, p.hours_per_month
				row.deliverables = "\n".join(d.text for d in p.deliverables)
		annual = self.billing_cycle == "Annual"
		self.price = sum((r.annual_price if annual else r.monthly_price) or 0 for r in self.plans)
		self.hours_included = sum(r.hours_per_month or 0 for r in self.plans)
		if not self.extra_hours_rate:
			self.extra_hours_rate = frappe.db.get_single_value("CRM Maintenance Settings", "extra_hours_rate")
		self.months_paid = len(self.payments)
		self.total_received = sum(p.amount or 0 for p in self.payments)
		self.paid_till = max((getdate(p.month) for p in self.payments), default=None)
		self.next_payment_due = next_due(getdate(self.start_date), self.months_paid, self.billing_cycle)
