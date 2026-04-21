from . import __version__ as app_version

app_name = "helpdeskhelper"
app_title = "Helpdeskhelper"
app_publisher = "itsdave GmbH"
app_description = "Helpdeskhelper"
app_email = "dev@itsdave.de"
app_license = "MIT"

# DocType Class Override
# ----------------------
# Fix: on_communication_update calls self.save() during insert, causing
# a cascading re-insert that breaks notifications in background jobs.

override_doctype_class = {
	"HD Ticket": "helpdeskhelper.hd_ticket_override.HDTicket"
}

# Permissions
# -----------
# Wrappers that call the helpdesk originals and extend them.
# The helpdesk originals are deregistered via boot_session hook.

permission_query_conditions = {
	"HD Ticket": "helpdeskhelper.permissions.permission_query",
}

has_permission = {
	"HD Ticket": "helpdeskhelper.permissions.has_permission",
}

boot_session = "helpdeskhelper.boot.remove_helpdesk_permission_hooks"

# Document Events
# ---------------

doc_events = {
	"Assignment Rule": {
		"before_save": "helpdeskhelper.overrides.keep_assignment_rules_empty"
	},
	"HD Ticket": {
		"after_insert": "helpdeskhelper.checklist.assignment.apply_rules_on_create",
		"on_update": "helpdeskhelper.checklist.assignment.apply_rules_on_update",
	},
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"all": [
		"helpdeskhelper.tools.apply_wiedervorlage"
	]
}
