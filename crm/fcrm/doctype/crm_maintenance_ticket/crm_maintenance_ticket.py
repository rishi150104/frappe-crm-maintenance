import frappe
from frappe.model.document import Document

from crm.maintenance import notify


class CRMMaintenanceTicket(Document):
	def before_insert(self):
		if not self.assigned_to:
			self.assigned_to = frappe.db.get_value("CRM Maintenance Client", self.client, "project_manager")

	def after_insert(self):
		notify.send(
			notify.recipients(self.assigned_to),
			f"New support ticket {self.name}: {self.subject}",
			f"{self.raised_by or 'A client'} raised a {self.priority} ticket for {self.client}.<br><br>{(self.description or '').replace(chr(10), '<br>')}",
			reference=(self.doctype, self.name),
		)
