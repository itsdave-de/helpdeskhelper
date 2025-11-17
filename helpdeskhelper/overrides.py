# Copyright (c) 2023, itsdave GmbH and contributors
# License: MIT. See LICENSE

import frappe


def keep_assignment_rules_empty(doc, method):
	"""
	Prevent automatic ticket assignment by keeping assignment rules empty.

	Assignment rules need users to assign to - if the users list is empty,
	they can't assign anyone even if enabled.

	This prevents the helpdesk app from automatically enabling support rotation
	when agents are added to teams. Manual ticket assignment still works normally.

	Args:
		doc: Assignment Rule document
		method: Event method (before_save)
	"""
	if doc.document_type == "HD Ticket" and doc.users:
		# Clear all users from HD Ticket assignment rules
		doc.users = []
		frappe.msgprint(
			"Assignment Rule users list has been cleared to prevent automatic ticket assignment. "
			"Use manual assignment instead.",
			alert=True,
			indicator="orange"
		)
