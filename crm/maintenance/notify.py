import frappe


def settings():
	return frappe.get_cached_doc("CRM Maintenance Settings")


def admin_emails() -> list[str]:
	users = frappe.get_all("Has Role", {"role": "System Manager", "parenttype": "User"}, pluck="parent")
	users = [u for u in users if u not in ("Administrator", "Guest")]
	return [e for e in frappe.get_all("User", {"name": ["in", users or [""]], "enabled": 1}, pluck="email") if e]


def head_emails() -> list[str]:
	raw = settings().head_emails or ""
	return [e.strip() for e in raw.replace("\n", ",").split(",") if e.strip()]


def recipients(pm: str | None = None) -> list[str]:
	"""Admins + head emails + the client's project manager (deduplicated)."""
	out = admin_emails() + head_emails()
	if pm:
		email = frappe.db.get_value("User", pm, "email")
		if email:
			out.append(email)
	return list(dict.fromkeys(out))


def send(to: list[str], subject: str, message: str, attachments=None, reference=None):
	if not to:
		return
	s = settings()
	frappe.sendmail(
		recipients=to,
		subject=subject,
		message=message,
		sender=s.send_from or None,
		reply_to=s.reply_to or None,
		attachments=attachments,
		reference_doctype=reference[0] if reference else None,
		reference_name=reference[1] if reference else None,
		now=True,
	)
