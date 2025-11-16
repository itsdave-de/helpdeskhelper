# Copyright (c) 2024, itsdave GmbH and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils.password import get_decrypted_password


class HelpdeskAppSettings(Document):
	pass


@frappe.whitelist()
def get_user_api_credentials(user):
	"""
	Get decrypted API credentials for a user.
	Returns api_key and api_secret in plain text, or None if not set.
	"""
	# Check permissions - only System Managers can access API credentials
	frappe.only_for("System Manager")

	# Check if user exists and has api_key
	user_doc = frappe.get_doc("User", user)

	if not user_doc.api_key:
		return None

	# Get the decrypted api_secret
	try:
		api_secret = get_decrypted_password("User", user, fieldname="api_secret")

		if not api_secret:
			return None

		return {
			"api_key": user_doc.api_key,
			"api_secret": api_secret
		}
	except Exception as e:
		frappe.log_error(f"Error retrieving API credentials for user {user}: {str(e)}")
		return None
