# Copyright (c) 2026, itsdave GmbH and contributors
# For license information, please see license.txt
"""Seed HR team, HD Ticket Types per service and HDA Checklist Assignment Rules.

Maps the OFORK checklist definitions to Frappe equivalents:
- OFORK Queue "Personalangelegenheiten" → HD Team "HR" (new)
- OFORK Queue "Projektplanung" → HD Team "Projektplanung" (new if missing)
- OFORK Queue "Gdata Academy" → HD Team "IT Intern" (new if missing)
- OFORK Service X → HD Ticket Type X (new)

Assignment Rules are trigger_event "On Create" so the checklist is attached
automatically when an agent creates a ticket with matching team + type.
"""

import frappe

TEAMS = ["HR", "Projektplanung", "IT Intern"]

TICKET_TYPES = [
	"Mitarbeiter Eintritt",
	"Mitarbeiter Austritt",
	"Mitarbeiter Änderung",
	"Praktikant Eintritt",
	"Praktikant Austritt",
	"Projektplanung",
]

# (template_title, team, ticket_type|None, priority)
RULES = [
	("Eintritt Mitarbeiter", "HR", "Mitarbeiter Eintritt", 100),
	("Austritt Mitarbeiter", "HR", "Mitarbeiter Austritt", 100),
	("Änderung Mitarbeiter", "HR", "Mitarbeiter Änderung", 100),
	("Eintritt Praktikant Suedsee-Camp", "HR", "Praktikant Eintritt", 100),
	("Austritt Praktikant Suedsee-Camp", "HR", "Praktikant Austritt", 100),
	("Projektplanung", "Projektplanung", "Projektplanung", 100),
	("GData Academy Prüfen", "IT Intern", None, 100),
]


def _ensure_team(name: str):
	if frappe.db.exists("HD Team", name):
		return
	doc = frappe.new_doc("HD Team")
	doc.team_name = name
	doc.insert(ignore_permissions=True)


def _ensure_type(name: str):
	if frappe.db.exists("HD Ticket Type", name):
		return
	doc = frappe.new_doc("HD Ticket Type")
	doc.name = name
	doc.insert(ignore_permissions=True)


def _ensure_rule(template: str, team: str, ticket_type: str | None, priority: int):
	title = f"Auto: {template}"
	if frappe.db.exists("HDA Checklist Assignment Rule", title):
		return
	if not frappe.db.exists("HDA Checklist Template", template):
		frappe.log_error(
			title="HDA Checklist Rule seed: Template fehlt",
			message=f"Template '{template}' nicht gefunden, Regel '{title}' übersprungen",
		)
		return
	doc = frappe.new_doc("HDA Checklist Assignment Rule")
	doc.title = title
	doc.enabled = 1
	doc.priority = priority
	doc.template = template
	doc.filter_team = team
	doc.filter_ticket_type = ticket_type
	doc.apply_once = 1
	doc.trigger_event = "On Create"
	doc.insert(ignore_permissions=True)


def execute():
	for team in TEAMS:
		_ensure_team(team)
	for ttype in TICKET_TYPES:
		_ensure_type(ttype)
	for template, team, ticket_type, priority in RULES:
		_ensure_rule(template, team, ticket_type, priority)
	frappe.db.commit()
