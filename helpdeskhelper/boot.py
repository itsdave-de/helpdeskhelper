# Copyright (c) 2026, itsdave GmbH and contributors
# License: MIT. See LICENSE

import frappe


def remove_helpdesk_permission_hooks(bootinfo=None):
	"""Remove helpdesk's original HD Ticket permission handlers from the registry.

	Called via boot_session hook. The bootinfo parameter is passed by Frappe
	but not needed here.
	"""
	if frappe.flags.get("helpdesk_hooks_cleaned"):
		return
	frappe.flags.helpdesk_hooks_cleaned = True

	helpdesk_hp = "helpdesk.helpdesk.doctype.hd_ticket.hd_ticket.has_permission"
	helpdesk_pq = "helpdesk.helpdesk.doctype.hd_ticket.hd_ticket.permission_query"

	hooks = frappe.get_hooks()

	hp_list = hooks.get("has_permission", {}).get("HD Ticket", [])
	if helpdesk_hp in hp_list:
		hp_list.remove(helpdesk_hp)

	pq_list = hooks.get("permission_query_conditions", {}).get("HD Ticket", [])
	if helpdesk_pq in pq_list:
		pq_list.remove(helpdesk_pq)
