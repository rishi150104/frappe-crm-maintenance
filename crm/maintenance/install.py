import frappe

SERVICES = ["Website Maintenance", "Technical SEO", "On-page SEO"]

BASIC = [
	"Monthly CMS core, plugin and theme updates", "Weekly off-site backups", "24/7 uptime monitoring",
	"Monthly malware / security scan", "SSL certificate monitoring", "Monthly website care report",
	"Up to 2 hours of small edits", "Email support (48-hour response)",
]
STANDARD = [
	"Everything in Basic", "Daily off-site backups", "Malware clean-up included", "Monthly speed check and cache tuning",
	"Contact form and key-page testing", "Broken link checks and fixes", "Up to 4 hours of edits / development",
	"Email support (24-hour response)",
]
PREMIUM = [
	"Everything in Standard", "Updates tested on staging first", "Monthly Core Web Vitals optimisation",
	"Monthly SEO health check (Search Console, 404s, sitemap)", "Analytics and conversion tracking checks",
	"Up to 6 hours of edits / development", "Priority support (same business day)", "Quarterly website review call",
]
PLANS = [  # service, tier, order, monthly, annual, hours, deliverables
	("Website Maintenance", "Basic", 1, 120, 1440, 2, BASIC),
	("Website Maintenance", "Standard", 2, 250, 3000, 4, STANDARD),
	("Website Maintenance", "Premium", 3, 330, 3960, 6, PREMIUM),
]
CHECKS = {
	"Updates": ["CMS core updated to latest stable version", "Plugins / apps updated", "Theme updated", "PHP / server version is supported"],
	"Security": ["Full backup taken and restore point verified", "Malware / security scan is clean", "SSL certificate valid (30+ days left)", "Admin users and passwords reviewed"],
	"Performance": ["Uptime 99%+ this month", "PageSpeed mobile score checked", "Cache / CDN working correctly", "Database cleaned and optimised"],
	"Functionality": ["Contact forms tested and delivering", "Checkout / key conversion flow tested", "Mobile layout spot-checked", "Broken links checked and fixed"],
}
SEO_CHECKS = ["Search Console crawl errors reviewed and fixed", "Index coverage / pages not indexed reviewed", "XML sitemap and robots.txt valid", "404s and broken links fixed"]


def seed_defaults():
	"""Idempotent: only seeds an empty catalog, so edits made in the UI are never overwritten."""
	if not frappe.db.exists("CRM Maintenance Service Type", "Website Maintenance"):
		for s in SERVICES:
			frappe.get_doc({"doctype": "CRM Maintenance Service Type", "service_name": s}).insert(ignore_permissions=True)
		for svc, tier, order, m, a, h, items in PLANS:
			frappe.get_doc({"doctype": "CRM Maintenance Plan", "service": svc, "tier_name": tier, "tier_order": order,
			                "monthly_price": m, "annual_price": a, "hours_per_month": h,
			                "deliverables": [{"text": t} for t in items]}).insert(ignore_permissions=True)
	if not frappe.db.count("CRM Maintenance Check"):
		n = 0
		for cat, labels in CHECKS.items():
			for label in labels:
				n += 1
				frappe.get_doc({"doctype": "CRM Maintenance Check", "category": cat, "label": label, "sort": n}).insert(ignore_permissions=True)
		for label in SEO_CHECKS:
			n += 1
			frappe.get_doc({"doctype": "CRM Maintenance Check", "category": "Technical SEO", "label": label,
			                "service": "Technical SEO", "sort": n}).insert(ignore_permissions=True)
	if not frappe.db.exists("Role", "Maintenance Client"):
		frappe.get_doc({"doctype": "Role", "role_name": "Maintenance Client", "desk_access": 0, "home_page": "/portal"}).insert(ignore_permissions=True)
