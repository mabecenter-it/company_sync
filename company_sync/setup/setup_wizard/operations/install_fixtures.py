# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe


def install():
	doc = frappe.new_doc('Item')
	doc.update({
		"item_code": "BS",
		"item_group": "Services",
		"is_stock_item": 0,
	})
	doc.insert(ignore_permissions=True, ignore_if_duplicate=True)