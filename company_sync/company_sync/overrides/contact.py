import frappe
from frappe import _
from frappe.utils import getdate, nowdate

from mabecenter.overrides.exception.base_document_exist import BaseDocumentExist

def validate_contact(doc, method):
    # Validar duplicados basados en first_name y last_name
    filters = {
        "first_name": doc.first_name,
        "last_name": doc.last_name,
        "custom_day_of_birth": doc.custom_day_of_birth
    }

    # Excluir el registro actual en caso de edición
    if doc.name:
        filters["name"] = ["!=", doc.name]

    existing_contact = frappe.db.exists("Contact", filters)

    message = None

    if existing_contact:
        message = _("A contact with the same name and dob already exists")
    if doc.custom_day_of_birth and getdate(doc.custom_day_of_birth) > getdate(nowdate()):
        message = _("DOB is not possible in the future")

    if message:
        if frappe.flags.from_script:
            print(existing_contact)
            frappe.log_error(message, reference_name=existing_contact)
            raise BaseDocumentExist(message, existing_contact)
        else:
            frappe.throw(message)