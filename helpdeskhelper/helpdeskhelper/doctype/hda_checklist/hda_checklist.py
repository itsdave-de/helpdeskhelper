# Copyright (c) 2026, itsdave GmbH and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import get_fullname, now_datetime


class HDAChecklist(Document):
	def before_insert(self):
		if self.template and not self.items:
			self._copy_items_from_template()
		if self.template and not self.title:
			self.title = frappe.db.get_value("HDA Checklist Template", self.template, "title")

	def validate(self):
		self._sync_item_metadata()
		self._recalculate_progress()

	def on_update(self):
		self._emit_item_status_comments()

	def _copy_items_from_template(self):
		template = frappe.get_cached_doc("HDA Checklist Template", self.template)
		for t_item in template.items:
			self.append(
				"items",
				{
					"item_type": t_item.item_type,
					"label": t_item.label,
					"status": "Offen" if t_item.item_type == "Task" else None,
				},
			)

	def _sync_item_metadata(self):
		now = now_datetime()
		user = frappe.session.user
		old = self.get_doc_before_save() if not self.is_new() else None
		old_items_by_name = {i.name: i for i in (old.items if old else [])}
		for item in self.items:
			if item.item_type == "Headline":
				item.status = None
				item.completed_by = None
				item.completed_at = None
				continue
			old_item = old_items_by_name.get(item.name)
			old_status = old_item.status if old_item else None
			status_changed = old_status != item.status
			if item.status and item.status != "Offen":
				if status_changed or not item.completed_by:
					item.completed_by = user
					item.completed_at = now
			else:
				item.completed_by = None
				item.completed_at = None

	def _recalculate_progress(self):
		tasks = [i for i in self.items if i.item_type == "Task"]
		self.total_tasks = len(tasks)
		self.completed_tasks = sum(1 for i in tasks if i.status and i.status != "Offen")
		if self.total_tasks > 0 and self.total_tasks == self.completed_tasks:
			self.status = "Abgeschlossen"
		else:
			self.status = "Aktiv"

	def _emit_item_status_comments(self):
		if not self.ticket or not self.template:
			return
		template_doc = frappe.get_cached_doc("HDA Checklist Template", self.template)
		if not template_doc.create_ticket_comment_on_change:
			return
		old = self.get_doc_before_save()
		if not old:
			return
		old_items_by_name = {i.name: i for i in old.items}
		user_name = get_fullname(frappe.session.user) or frappe.session.user
		for item in self.items:
			if item.item_type != "Task":
				continue
			old_item = old_items_by_name.get(item.name)
			old_status = old_item.status if old_item else "Offen"
			if old_status == item.status:
				continue
			new_status = item.status or "Offen"
			if new_status == "Erledigt":
				action = "als <b>erledigt</b> markiert"
			elif new_status == "Nicht benötigt":
				action = "als <b>nicht benötigt</b> markiert"
			else:
				action = "wieder als <b>offen</b> markiert"
			content = f'{user_name} hat „{item.label}" {action} (Checkliste „{self.title}").'
			frappe.get_doc(
				{
					"doctype": "Comment",
					"comment_type": "Info",
					"reference_doctype": "HD Ticket",
					"reference_name": self.ticket,
					"content": content,
				}
			).insert(ignore_permissions=True)
