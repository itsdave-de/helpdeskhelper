# Copyright (c) 2023, itsdave GmbH and contributors
# License: MIT. See LICENSE

import frappe


def keep_assignment_rules_empty(doc, method):
	"""
	Prevent automatic ticket assignment by disabling assignment rules
	for HD Tickets and keeping their users list empty.

	The helpdesk app automatically creates and enables assignment rules
	when agents are added to teams (HDTeam.update_support_rotations).
	This hook intercepts the save to ensure the rules stay disabled.

	Without this, an enabled rule with no users causes an IndexError
	in the round-robin assignment logic.

	Args:
		doc: Assignment Rule document
		method: Event method (before_save)
	"""
	if doc.document_type == "HD Ticket":
		if doc.users:
			doc.users = []
		if not doc.disabled:
			doc.disabled = 1
