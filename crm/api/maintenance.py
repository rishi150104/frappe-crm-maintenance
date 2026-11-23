import frappe
from frappe.utils import add_days, get_first_day, getdate, now_datetime, nowdate
from frappe.utils.pdf import get_pdf

from crm.maintenance import notify
from crm.maintenance.logic import add_months, month_start, payment_state

ROLES = ("Sales Manager", "Sales User", "System Manager")
MANAGERS = ("Sales Manager", "System Manager")


def _only():
	frappe.only_for(ROLES)


def _month(m: str | None):
	return month_start(getdate(m or nowdate()))


def _is_manager() -> bool:
	return bool(set(frappe.get_roles()) & set(MANAGERS))


def _hours_by_client(month) -> dict:
	rows = frappe.db.sql(
		"""select parent, sum(hours) from `tabCRM Maintenance Time Log`
		where date >= %s and date < %s group by parent""",
		(month, add_months(month, 1)),
	)
	return {p: h or 0 for p, h in rows}


def _scores(month) -> dict:
	rows = frappe.get_all(
		"CRM Maintenance Report", {"month": month}, ["name", "client", "score", "score_label", "status"]
	)
	return {r.client: r for r in rows}


def _rows(month, only_active=False) -> list[dict]:
	"""One enriched row per client for the given month (shared by dashboard, clients, reports, hours)."""
	hours, reports = _hours_by_client(month), _scores(month)
	pm_names = {u.name: u.full_name for u in frappe.get_all("User", ["name", "full_name"])}
	agencies = {a.name: a.agency_name for a in frappe.get_all("CRM Maintenance Agency", ["name", "agency_name"])}
	today = getdate(nowdate())
	out = []
	for c in frappe.get_all("CRM Maintenance Client", order_by="creation"):
		d = frappe.get_doc("CRM Maintenance Client", c.name)  # ponytail: per-client load, batch the queries past ~500 clients
		if only_active and d.status != "Active":
			continue
		state, days = payment_state(getdate(d.next_payment_due), d.billing_cycle, today)
		r = reports.get(d.name)
		out.append(
			{
				"name": d.name, "client_name": d.client_name, "status": d.status, "website": d.website,
				"agency": d.agency, "agency_name": agencies.get(d.agency) or "Direct client",
				"project_manager": d.project_manager, "pm_name": pm_names.get(d.project_manager),
				"plans": [f"{p.service}: {p.tier}" if p.tier else p.service or p.plan for p in d.plans],
				"price": d.price, "billing_cycle": d.billing_cycle,
				"hours_used": hours.get(d.name, 0), "hours_included": d.hours_included,
				"next_payment_due": str(d.next_payment_due), "payment_state": state, "days": days,
				"months_paid": d.months_paid, "paid_till": str(d.paid_till) if d.paid_till else None,
				"score": r.score if r else None, "score_label": r.score_label if r else None,
				"report": r.name if r else None, "report_status": r.status if r else None,
			}
		)
	return out


def _monthly_value(r) -> float:
	return (r["price"] or 0) / (12 if r["billing_cycle"] == "Annual" else 1)


@frappe.whitelist()
def get_clients(month: str | None = None) -> list[dict]:
	_only()
	return _rows(_month(month))


@frappe.whitelist()
def get_dashboard(month: str | None = None) -> dict:
	_only()
	m = _month(month)
	rows = _rows(m)
	active = [r for r in rows if r["status"] == "Active"]
	me = frappe.session.user
	mine = [r for r in active if _is_manager() or r["project_manager"] == me]
	due = [r for r in mine if r["payment_state"] != "ok"]
	scored = [r["score"] for r in active if r["score"] is not None]
	trend = []
	for i in range(5, -1, -1):
		mm = add_months(m, -i)
		sc = [s.score for s in _scores(mm).values()]
		hrs = sum(_hours_by_client(mm).values())
		trend.append({"month": mm.strftime("%b"), "score": round(sum(sc) / len(sc)) if sc else 0, "hours": hrs})
	recent = frappe.db.sql(
		"""select t.parent as client, c.client_name, t.hours, t.description, t.date, t.work_type
		from `tabCRM Maintenance Time Log` t join `tabCRM Maintenance Client` c on c.name = t.parent
		order by t.date desc, t.creation desc limit 5""",
		as_dict=True,
	)
	return {
		"kpis": {
			"active": len(active), "total": len(rows),
			"revenue": round(sum(_monthly_value(r) for r in active)),
			"hours_used": sum(r["hours_used"] for r in active), "hours_included": sum(r["hours_included"] or 0 for r in active),
			"avg_score": round(sum(scored) / len(scored)) if scored else 0,
			"reports_sent": len([r for r in active if r["report_status"] == "Sent"]),
			"payments_due": len([r for r in active if r["payment_state"] != "ok"]),
		},
		"reminders": due,
		"trend": trend,
		"attention": {
			"reports_unsent": len([r for r in active if r["report_status"] != "Sent"]),
			"payments_due": len(due),
			"open_tickets": frappe.db.count("CRM Maintenance Ticket", {"status": ["!=", "Resolved"]}),
		},
		"clients": active,
		"recent": recent,
	}


@frappe.whitelist()
def get_client(name: str, month: str | None = None) -> dict:
	_only()
	d = frappe.get_doc("CRM Maintenance Client", name)
	d.check_permission("read")
	by_month = frappe.db.sql(
		"""select date_format(date, '%%Y-%%m-01') as month, sum(hours) as hours from `tabCRM Maintenance Time Log`
		where parent = %s group by 1 order by 1 desc limit 12""",
		name, as_dict=True,
	)
	return {
		"doc": d.as_dict(),
		"row": next((r for r in _rows(_month(month)) if r["name"] == name), None),
		"hours_by_month": by_month,
		"tickets": frappe.get_all("CRM Maintenance Ticket", {"client": name}, ["name", "subject", "status", "creation"], order_by="creation desc"),
		"logins": [
			frappe.db.get_value("CRM Maintenance Client Login", l, ["name", "user", "full_name", "company"], as_dict=True)
			for l in frappe.get_all("CRM Maintenance Login Client", {"client": name}, pluck="parent")
		],
		"reports": frappe.get_all("CRM Maintenance Report", {"client": name}, ["name", "month", "score", "status"], order_by="month desc"),
	}


@frappe.whitelist()
def get_agencies() -> list[dict]:
	_only()
	rows = _rows(_month(None))
	out = []
	for a in frappe.get_all("CRM Maintenance Agency", ["*"], order_by="creation"):
		mine = [r for r in rows if r["agency"] == a.name]
		out.append({**a, "clients": len(mine), "monthly_value": round(sum(_monthly_value(r) for r in mine))})
	return out


@frappe.whitelist()
def get_payments() -> dict:
	_only()
	rows = [r for r in _rows(_month(None)) if r["status"] == "Active"]
	groups = {"overdue": [], "due_soon": [], "ok": []}
	for r in rows:
		groups[r["payment_state"]].append(r)
	return groups


@frappe.whitelist()
def record_payment(client: str, amount: float | None = None, paid_on: str | None = None, note: str | None = None) -> None:
	"""Mark the next unpaid period as paid (used by both 'Mark paid' and 'Record payment')."""
	_only()
	d = frappe.get_doc("CRM Maintenance Client", client)
	d.append("payments", {"month": month_start(getdate(d.next_payment_due)), "amount": amount or d.price, "paid_on": paid_on or nowdate(), "note": note})
	d.save()


@frappe.whitelist()
def log_hours(client: str, hours: float, date: str | None = None, work_type: str = "Support", description: str | None = None) -> None:
	_only()
	d = frappe.get_doc("CRM Maintenance Client", client)
	d.append("time_logs", {"date": date or nowdate(), "hours": hours, "work_type": work_type, "description": description, "logged_by": frappe.session.user})
	d.save()
	m = month_start(getdate(date or nowdate()))
	used = _hours_by_client(m).get(client, 0)
	if d.hours_included and used > d.hours_included and str(d.over_hours_alert_month or "") != str(m):
		d.db_set("over_hours_alert_month", m)
		notify.send(
			notify.admin_emails() + notify.head_emails(),
			f"{d.client_name} went over plan hours",
			f"{d.client_name} has used {used}h of {d.hours_included}h in {m:%B %Y}. Extra hours may need to be invoiced.",
		)


@frappe.whitelist()
def get_hours(month: str | None = None, client: str | None = None) -> dict:
	_only()
	m = _month(month)
	rows = _rows(m, only_active=True)
	entries = frappe.db.sql(
		"""select t.name, t.parent as client, c.client_name, t.date, t.hours, t.work_type, t.description, u.full_name as logged_by
		from `tabCRM Maintenance Time Log` t join `tabCRM Maintenance Client` c on c.name = t.parent
		left join `tabUser` u on u.name = t.logged_by
		where t.date >= %s and t.date < %s and (%s = '' or t.parent = %s) order by t.date desc, t.creation desc""",
		(m, add_months(m, 1), client or "", client or ""), as_dict=True,
	)
	return {"usage": rows, "entries": entries}


@frappe.whitelist()
def get_reports(month: str | None = None) -> list[dict]:
	"""All active clients for the month; creates the draft report if it does not exist yet."""
	_only()
	m = _month(month)
	for c in frappe.get_all("CRM Maintenance Client", {"status": "Active"}, pluck="name"):
		if not frappe.db.exists("CRM Maintenance Report", {"client": c, "month": m}):
			frappe.get_doc({"doctype": "CRM Maintenance Report", "client": c, "month": m}).insert()
	rows = _rows(m, only_active=True)
	for r in rows:
		items = frappe.get_all("CRM Maintenance Report Item", {"parent": r["report"]}, ["status"])
		r["unchecked"] = len([i for i in items if not i.status])
		r["issues"] = len([i for i in items if i.status == "Issue"])
	return rows


@frappe.whitelist()
def create_month_report(client: str, month: str | None = None) -> str:
	_only()
	m = _month(month)
	return frappe.db.exists("CRM Maintenance Report", {"client": client, "month": m}) or frappe.get_doc(
		{"doctype": "CRM Maintenance Report", "client": client, "month": m}
	).insert().name


@frappe.whitelist()
def get_report(name: str) -> dict:
	_only()
	doc = frappe.get_doc("CRM Maintenance Report", name)
	doc.check_permission("read")
	c = frappe.get_doc("CRM Maintenance Client", doc.client)
	return {
		"doc": doc.as_dict(),
		"client": {"name": c.name, "client_name": c.client_name, "website": c.website, "agency": c.agency,
		           "contact_email": c.contact_email, "report_to": c.report_to, "hours_included": c.hours_included},
		"work": [l.as_dict() for l in c.time_logs if month_start(getdate(l.date)) == getdate(doc.month)],
	}


def _render_pdf(doc) -> bytes:
	c = frappe.get_doc("CRM Maintenance Client", doc.client)
	s = notify.settings()
	agency = frappe.get_doc("CRM Maintenance Agency", c.agency) if c.agency else None
	brand = (agency.agency_name if agency and agency.branded else None) or s.company_name or ""
	cats = {}
	for i in doc.items:
		cats.setdefault(i.category or "Other", []).append(i)
	html = frappe.render_template(
		"crm/templates/maintenance/report.html",
		{"doc": doc, "client": c, "settings": s, "brand": brand, "categories": cats, "frappe": frappe,
		 "color": s.brand_color or "#171717", "base_url": frappe.utils.get_url()},
	)
	return get_pdf(html)


@frappe.whitelist()
def generate_pdf(report: str) -> str:
	_only()
	doc = frappe.get_doc("CRM Maintenance Report", report)
	doc.check_permission("write")
	f = frappe.get_doc(
		{"doctype": "File", "file_name": f"{doc.name}.pdf", "attached_to_doctype": doc.doctype,
		 "attached_to_name": doc.name, "content": _render_pdf(doc), "is_private": 1}
	).insert(ignore_permissions=True)
	doc.db_set("pdf", f.file_url)
	return f.file_url


@frappe.whitelist()
def send_report(report: str, recipients: str | None = None) -> None:
	_only()
	doc = frappe.get_doc("CRM Maintenance Report", report)
	doc.check_permission("write")
	c = frappe.get_doc("CRM Maintenance Client", doc.client)
	to = recipients or c.contact_email
	if c.report_to == "Agency" and not recipients and c.agency:
		to = frappe.db.get_value("CRM Maintenance Agency", c.agency, "email") or to
	if not to:
		frappe.throw("No recipient email. Set a report recipient on the client (or agency).")
	s = notify.settings()
	notify.send(
		[e.strip() for e in to.split(",")],
		f"{c.client_name} - website care report ({doc.month:%B %Y})",
		f"Hi,<br><br>Your website care report for {doc.month:%B %Y} is attached. Health score: {doc.score}/100.<br><br>{s.report_footer or ''}",
		attachments=[{"fname": f"{doc.name}.pdf", "fcontent": _render_pdf(doc)}],
		reference=(doc.doctype, doc.name),
	)
	doc.db_set({"status": "Sent", "sent_on": now_datetime()})


# ---- tickets
@frappe.whitelist()
def get_tickets() -> list[dict]:
	_only()
	return frappe.db.sql(
		"""select t.name, t.subject, t.ticket_type, t.priority, t.status, t.raised_by, t.client_replied, t.modified,
		t.client, c.client_name, c.agency, u.full_name as pm_name, t.assigned_to
		from `tabCRM Maintenance Ticket` t join `tabCRM Maintenance Client` c on c.name = t.client
		left join `tabUser` u on u.name = t.assigned_to order by t.modified desc""",
		as_dict=True,
	)


@frappe.whitelist()
def get_ticket(name: str) -> dict:
	_only()
	return frappe.get_doc("CRM Maintenance Ticket", name).as_dict()


@frappe.whitelist()
def reply_ticket(ticket: str, message: str, status: str | None = None) -> None:
	_only()
	t = frappe.get_doc("CRM Maintenance Ticket", ticket)
	t.append("replies", {"message": message, "by_user": frappe.session.user, "by_name": frappe.utils.get_fullname(), "is_client": 0})
	t.client_replied = 0
	if status:
		t.status = status
	t.save()
	if t.raised_by and "@" in t.raised_by:
		notify.send([t.raised_by], f"Re: {t.subject} [{t.name}]", message.replace("\n", "<br>"), reference=(t.doctype, t.name))


@frappe.whitelist()
def update_ticket(ticket: str, status: str | None = None, priority: str | None = None, assigned_to: str | None = None) -> None:
	_only()
	t = frappe.get_doc("CRM Maintenance Ticket", ticket)
	for k, v in {"status": status, "priority": priority, "assigned_to": assigned_to}.items():
		if v is not None:
			t.set(k, v or None)
	t.save()


# ---- client logins (portal users)
PORTAL_ROLE = "Maintenance Client"


def _ensure_role():
	if not frappe.db.exists("Role", PORTAL_ROLE):
		frappe.get_doc({"doctype": "Role", "role_name": PORTAL_ROLE, "desk_access": 0, "home_page": "/portal"}).insert(ignore_permissions=True)


@frappe.whitelist()
def get_logins() -> list[dict]:
	_only()
	out = []
	for l in frappe.get_all("CRM Maintenance Client Login", ["name", "user", "full_name", "company", "active"]):
		l["clients"] = frappe.get_all("CRM Maintenance Login Client", {"parent": l.name}, pluck="client")
		l["last_login"] = frappe.db.get_value("User", l.user, "last_login")
		out.append(l)
	return out


@frappe.whitelist()
def save_client_login(email: str, full_name: str, clients: list, company: str | None = None, password: str | None = None, active: int = 1) -> str:
	frappe.only_for(MANAGERS)
	_ensure_role()
	if not frappe.db.exists("User", email):
		if not password:
			frappe.throw("Set a password for the new login.")
		u = frappe.get_doc({"doctype": "User", "email": email, "first_name": full_name, "user_type": "Website User",
		                    "send_welcome_email": 0, "roles": [{"role": PORTAL_ROLE}]}).insert(ignore_permissions=True)
	else:
		u = frappe.get_doc("User", email)
		if u.user_type != "Website User":
			frappe.throw("That email belongs to a team user. Use a different email for the client login.")
	if password:
		from frappe.utils.password import update_password
		update_password(email, password)
	u.enabled = int(active)
	u.save(ignore_permissions=True)
	login = frappe.get_doc("CRM Maintenance Client Login", email) if frappe.db.exists("CRM Maintenance Client Login", email) else frappe.new_doc("CRM Maintenance Client Login")
	login.update({"user": email, "full_name": full_name, "company": company, "active": int(active)})
	login.set("clients", [{"client": c} for c in clients])
	login.save(ignore_permissions=True)
	return login.name


@frappe.whitelist()
def get_team() -> list[dict]:
	_only()
	return frappe.get_all("User", {"enabled": 1, "user_type": "System User", "name": ["not in", ["Administrator", "Guest"]]}, ["name", "full_name"])


# ---- reminders + scheduler
def _reminder_rows():
	return [r for r in _rows(_month(None), only_active=True) if r["payment_state"] != "ok"]


def _renewals():
	days = notify.settings().renewal_alert_days or 30
	soon = add_days(nowdate(), days)
	return frappe.get_all("CRM Maintenance Client", {"status": "Active", "contract_end": ["between", [nowdate(), soon]]}, ["client_name", "contract_end"])


def _digest(rows, pm=None) -> str:
	lines = [f"<li>{r['client_name']}: {r['price']:.0f} ({r['billing_cycle']}) - {'overdue by ' + str(-r['days']) + ' days' if r['days'] < 0 else 'due in ' + str(r['days']) + ' days'}</li>" for r in rows]
	return "<b>Payments due or overdue</b><ul>" + "".join(lines) + "</ul>"


@frappe.whitelist()
def email_reminders_now() -> int:
	frappe.only_for(MANAGERS)
	return send_payment_reminders()


def send_payment_reminders() -> int:
	"""Daily: one summary to admins + head emails, and each PM gets their own clients. Never sent to clients."""
	rows = _reminder_rows()
	renew = _renewals()
	body = _digest(rows) if rows else ""
	if renew:
		body += "<b>Contracts ending soon</b><ul>" + "".join(f"<li>{c.client_name}: {c.contract_end}</li>" for c in renew) + "</ul>"
	if body:
		notify.send(notify.admin_emails() + notify.head_emails(), "Daily payment reminders", body)
	for pm in {r["project_manager"] for r in rows if r["project_manager"]}:
		email = frappe.db.get_value("User", pm, "email")
		notify.send([email] if email else [], "Your payment reminders", _digest([r for r in rows if r["project_manager"] == pm]))
	return len(rows)


def create_monthly_reports():
	"""Scheduler (monthly): draft a report for every active client."""
	m = get_first_day(nowdate())
	for name in frappe.get_all("CRM Maintenance Client", {"status": "Active"}, pluck="name"):
		if not frappe.db.exists("CRM Maintenance Report", {"client": name, "month": m}):
			frappe.get_doc({"doctype": "CRM Maintenance Report", "client": name, "month": m}).insert(ignore_permissions=True)


@frappe.whitelist()
def get_counts() -> dict:
	"""Sidebar badges."""
	_only()
	return {"payments_due": len(_reminder_rows()), "open_tickets": frappe.db.count("CRM Maintenance Ticket", {"status": ["!=", "Resolved"]})}


@frappe.whitelist()
def get_overview() -> dict:
	_only()
	d = get_dashboard()["kpis"]
	return {"active_clients": d["active"], "unsent_invoices": frappe.db.count("CRM Maintenance Invoice", {"status": "Scheduled"}), "avg_score": d["avg_score"]}
