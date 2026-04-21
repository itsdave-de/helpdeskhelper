# Copyright (c) 2026, itsdave GmbH and contributors
# For license information, please see license.txt

import frappe


def apply_rules_on_create(doc, method=None):
	_apply_rules(doc, trigger_events=["On Create"])


def apply_rules_on_update(doc, method=None):
	_apply_rules(doc, trigger_events=["On Update"])


def _apply_rules(ticket, trigger_events):
	rules = frappe.get_all(
		"HDA Checklist Assignment Rule",
		filters={
			"enabled": 1,
			"trigger_event": ["in", trigger_events],
		},
		fields=[
			"name",
			"priority",
			"template",
			"filter_team",
			"filter_ticket_type",
			"apply_once",
		],
		order_by="priority desc",
	)
	if not rules:
		return
	for rule in rules:
		if not _rule_matches(rule, ticket):
			continue
		if rule.apply_once and _already_applied(ticket.name, rule.template):
			continue
		_create_checklist(ticket.name, rule.template, rule.name)


def _rule_matches(rule, ticket):
	if rule.filter_team and ticket.agent_group != rule.filter_team:
		return False
	if rule.filter_ticket_type and ticket.ticket_type != rule.filter_ticket_type:
		return False
	return True


def _already_applied(ticket_name, template_name):
	return bool(
		frappe.db.exists(
			"HDA Checklist",
			{"ticket": ticket_name, "template": template_name},
		)
	)


def _create_checklist(ticket_name, template_name, rule_name):
	try:
		frappe.get_doc(
			{
				"doctype": "HDA Checklist",
				"ticket": ticket_name,
				"template": template_name,
			}
		).insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(
			title=f"HDA Checklist: Auto-Assignment via {rule_name} fehlgeschlagen",
			message=frappe.get_traceback(),
		)
