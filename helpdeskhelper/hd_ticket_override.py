# Copyright (c) 2026, itsdave GmbH and contributors
# License: MIT. See LICENSE

"""
Override for HDTicket to fix a bug in on_communication_update.

Problem: When a new ticket is created, after_insert() calls
create_communication_via_contact(), which creates a Communication.
The Communication's on_update hook calls back to
HDTicket.on_communication_update(), which calls self.save().

During insert, __islocal is still True, so self.save() triggers a
second insert() call. This second cycle removes __islocal, causing
run_notifications to call evaluate_alert with is_new()=False, which
calls doc.reload(). In background jobs (Auto Repeat), the reload()
fails because the transaction is not yet committed → crash →
Auto Repeat disables itself.

Fix: During insert (__islocal is set), use db_update() instead of
save(). db_update() writes the field changes to the database without
triggering the full save cycle (no hooks, no notifications, no
re-insert). The outer insert() will handle post-save methods.
"""

import frappe
from frappe.utils import now_datetime
from helpdesk.helpdesk.doctype.hd_ticket.hd_ticket import HDTicket as _OriginalHDTicket


class HDTicket(_OriginalHDTicket):
	def after_insert(self):
		super().after_insert()
		if self.get("description"):
			# Die aus der Beschreibung erzeugte Erst-Communication wird von
			# update_comment_in_doc in _comments gespiegelt und laesst die
			# Kommentar-Sprechblase der Listenansicht sofort 1 zeigen.
			# _comments ist nur der Anzeige-Cache; die Communication selbst
			# (Ticketverlauf) bleibt unangetastet.
			self.db_set("_comments", None, update_modified=False)

	def on_communication_update(self, c):
		if c.sent_or_received == "Received":
			if self.has_agent_replied:
				self.status = self.ticket_reopen_status
			else:
				self.status = self.default_open_status
			self.last_customer_response = now_datetime()

		if c.sent_or_received == "Sent":
			if c.communication_type and c.communication_type == "Automated Message":
				return
			self.first_responded_on = self.first_responded_on or now_datetime()
			self.last_agent_response = now_datetime()

			if frappe.db.get_single_value("HD Settings", "auto_update_status"):
				self.status = frappe.db.get_single_value("HD Settings", "update_status_to")

		self.description = self.description or c.content

		# Fix: During insert, the document is still in a transaction.
		# self.save() would trigger a second insert() because __islocal
		# is still set, causing a cascade that breaks notifications.
		# Use db_update() to persist field changes without triggering hooks.
		if self.get("__islocal"):
			self.db_update()
		else:
			self.save()
