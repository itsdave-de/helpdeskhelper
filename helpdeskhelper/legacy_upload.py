import frappe
from frappe import _
from frappe.handler import check_write_permission
from frappe.utils import cint

ALLOWED_DOCTYPES = {"HD Ticket"}


@frappe.whitelist(methods=["POST"])
def uploadfile():
    """Legacy-Shim: die InsideAPP sendet cmd=uploadfile, das Frappe >= v14 nicht mehr kennt."""
    doctype = frappe.form_dict.doctype
    docname = frappe.form_dict.docname
    filename = frappe.form_dict.filename
    filedata = frappe.form_dict.filedata

    if doctype not in ALLOWED_DOCTYPES:
        frappe.throw(_("Upload für {0} nicht erlaubt").format(doctype), frappe.PermissionError)
    if not (docname and filename and filedata):
        frappe.throw(_("docname, filename und filedata sind erforderlich"))

    check_write_permission(doctype, docname)

    file_doc = frappe.get_doc(
        {
            "doctype": "File",
            "attached_to_doctype": doctype,
            "attached_to_name": docname,
            "file_name": filename,
            "is_private": cint(frappe.form_dict.get("is_private") or 1),
            "content": filedata,
            "decode": True,
        }
    ).save()

    return {"file_url": file_doc.file_url, "file_name": file_doc.file_name}
