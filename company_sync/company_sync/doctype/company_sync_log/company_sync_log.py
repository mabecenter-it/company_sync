# Copyright (c) 2025, Dante Devenir and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class CompanySyncLog(Document):
	def on_change(self):
		# This method is called when the document child table is changed
		# And execute autosave
		self.save()
