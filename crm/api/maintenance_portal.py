"""Client portal API. Portal users are Website Users with NO doctype permissions: every call is scoped here."""

import frappe

from crm.api.maintenance import _render_pdf
from crm.maintenance import notify


def _my_clients() -> list[str]:
	login = frappe.db.get_value("CRM Maintenance Client Login", {"user": frappe.session.user, "active": 1})
	if frappe.session.user == "Guest" or not login:
		frappe.throw("Not permitted", frappe.PermissionError)
	return frappe.get_all("CRM Maintenance Login Client", {"parent": login}, pluck="client")


def _own_ticket(name: str):
	t = frappe.get_doc("CRM Maintenance Ticket", name)
	if t.client not in _my_clients():
		frappe.throw("Not permitted", frappe.PermissionError)
	return t


@frappe.whitelist()
def get_portal() -> dict:
	clients = _my_clients()
	login = frappe.get_doc("CRM Maintenance Client Login", frappe.session.user)
	return {
		"name": login.full_name,
		"company": notify.settings().company_name,
		"clients": frappe.get_all("CRM Maintenance Client", {"name": ["in", clients or [""]]}, ["name", "client_name", "website"]),
		# clients only see reports that were actually sent to them
		"reports": frappe.get_all(
			"CRM Maintenance Report", {"client": ["in", clients or [""]], "status": "Sent"},
			["name", "client", "month", "score", "score_label", "sent_on"], order_by="month desc",
		),
		"tickets": frappe.get_all(
			"CRM Maintenance Ticket", {"client": ["in", clients or [""]]},
			["name", "client", "subject", "ticket_type", "priority", "status", "modified"], order_by="modified desc",
		),
	}


@frappe.whitelist()
def download_report(report: str) -> None:
	doc = frappe.get_doc("CRM Maintenance Report", report)
	if doc.client not in _my_clients() or doc.status != "Sent":
		frappe.throw("Not permitted", frappe.PermissionError)
	frappe.local.response.filename = f"{doc.name}.pdf"
	frappe.local.response.filecontent = _render_pdf(doc)
	frappe.local.response.type = "download"


@frappe.whitelist()
def create_ticket(client: str, subject: str, description: str = "", ticket_type: str = "Other", priority: str = "Normal") -> str:
	if client not in _my_clients():
		frappe.throw("Not permitted", frappe.PermissionError)
	if priority not in ("Low", "Normal", "High", "Urgent"):
		priority = "Normal"
	return frappe.get_doc(
		{"doctype": "CRM Maintenance Ticket", "client": client, "subject": subject[:140], "description": description,
		 "ticket_type": ticket_type, "priority": priority, "raised_by": frappe.session.user}
	).insert(ignore_permissions=True).name


@frappe.whitelist()
def get_ticket(name: str) -> dict:
	t = _own_ticket(name)
	return {"name": t.name, "subject": t.subject, "status": t.status, "priority": t.priority, "description": t.description,
	        "replies": [{"by_name": r.by_name, "message": r.message, "is_client": r.is_client, "creation": str(r.creation)} for r in t.replies]}


@frappe.whitelist()
def reply_ticket(name: str, message: str) -> None:
	t = _own_ticket(name)
	t.append("replies", {"message": message, "by_user": frappe.session.user, "by_name": frappe.utils.get_fullname(), "is_client": 1})
	t.client_replied = 1
	if t.status in ("Resolved", "Waiting on client"):
		t.status = "Open"
	t.save(ignore_permissions=True)
	notify.send(notify.recipients(t.assigned_to), f"Client replied: {t.subject} [{t.name}]", message.replace("\n", "<br>"), reference=(t.doctype, t.name))
