# Copyright (c) 2026, itsdave GmbH and contributors
# License: MIT. See LICENSE

"""
Wrapper around Helpdesk's HD Ticket permission functions.

Strategy: We register our handlers via hooks.py AND remove the helpdesk
originals from the hook registry at startup (via boot.py). This way only
our handlers run, and we call the originals internally.

Our handlers call the original helpdesk functions and extend them with
custom_creator_team logic (OR, not AND).
"""

import frappe

from helpdesk.helpdesk.doctype.hd_ticket.hd_ticket import (
	has_permission as _original_has_permission,
	permission_query as _original_permission_query,
)
from helpdesk.utils import get_agents_team, is_agent

logger = frappe.logger("helpdeskhelper.permissions", allow_site=True)


def has_permission(doc, user=None):
	"""Extended has_permission: original logic OR creator-team check."""
	if _original_has_permission(doc, user):
		return True

	# --- Future extension point ---
	# Here we will add: if the requesting agent's team matches
	# doc.custom_creator_team → return True
	# For now (PoC): just return the original result
	return False


def permission_query(user):
	"""Extended permission_query: original SQL OR creator-team condition."""
	original = _original_permission_query(user)

	# --- Future extension point ---
	# Here we will append:
	#   OR (`tabHD Ticket`.custom_creator_team IN ('TeamA', 'TeamB'))
	# For now (PoC): return original unchanged
	return original
