# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from frappe.desk.page.setup_wizard.setup_wizard import make_records


def create_company_sync_settings(args):
	frappe.get_doc(
		{
			"doctype": "Company Sync Settings",
			"host": args.get("host"),
			"user": args.get("user"),
			"type": args.get("type"),
			"name_db": args.get("name_db"),
			"port": args.get("port"),
			"password": args.get("password"),
			"connector": args.get("connector"),
			"user_api": args.get("user_db"),
			"endpoint": args.get("endpoint"),
			"token": args.get("token"),
		}
	).insert()
