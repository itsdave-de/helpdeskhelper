# Copyright (c) 2026, itsdave GmbH and contributors
# For license information, please see license.txt
"""One-time import of the 7 productive OFORK checklist templates.

Reads seeds.json (extracted from ofork.checklist + checklist_field) and
creates HDA Checklist Template + Items. Safe to run multiple times — skips
templates that already exist.
"""

import json
from pathlib import Path

import frappe

ITEM_TYPE_MAP = {
	"Headline": "Headline",
	"Task": "Task",
}


def execute():
	seeds_path = Path(__file__).with_name("seeds.json")
	if not seeds_path.exists():
		frappe.log_error(
			title="HDA Checklist seed: seeds.json missing",
			message=f"Expected file at {seeds_path}",
		)
		return

	seeds = json.loads(seeds_path.read_text(encoding="utf-8"))

	created = 0
	skipped = 0
	for seed in seeds:
		title = seed["title"]
		if frappe.db.exists("HDA Checklist Template", title):
			skipped += 1
			continue

		doc = frappe.new_doc("HDA Checklist Template")
		doc.title = title
		doc.description = seed.get("description")
		doc.enabled = 1
		doc.create_ticket_comment_on_change = 1 if seed.get("set_article") else 0
		for item in seed["items"]:
			doc.append(
				"items",
				{
					"item_type": ITEM_TYPE_MAP.get(item["field_type"], "Task"),
					"label": item["task"],
				},
			)
		doc.insert(ignore_permissions=True)
		created += 1

	frappe.db.commit()
	print(f"HDA Checklist seed: {created} templates created, {skipped} already existed.")
