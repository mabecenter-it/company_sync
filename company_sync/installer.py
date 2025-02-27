import frappe

DEFAULT_ROLE_PROFILES = {
	"Syncer": [
		"Syncer User",
		"Syncer Admin",
	],
}

def before_install():
	#save_config_vtigercrm()
	pass

def after_install():
	#save_config_vtigercrm()
	#create_default_role_profiles()
	create_custom_role()

def create_custom_role(data = {"role": "Syncer User"}):
	if data.get("role") and not frappe.db.exists("Role", data.get("role")):
		frappe.get_doc(
			{"doctype": "Role", "role_name": data.get("role"), "desk_access": 1, "is_custom": 1}
		).insert(ignore_permissions=True)

def create_default_role_profiles():
	for role_profile_name, roles in DEFAULT_ROLE_PROFILES.items():
		if frappe.db.exists("Role Profile", role_profile_name):
			continue

		role_profile = frappe.new_doc("Role Profile")
		role_profile.role_profile = role_profile_name
		for role in roles:
			role_profile.append("roles", {"role": role})

		role_profile.insert(ignore_permissions=True)

def save_config_vtigercrm():
	print("save_config_vtigercrm")
	"""Save VTiger CRM configuration from environment variables to site config"""
	import os
	import frappe
	#from frappe.installer import update_site_config
	frappe.logger("save_config_vtigercrm")
	# Environment variables
	vtiger_config = {
		"db_user_vtiger": os.getenv('VTIGER_USERNAME'),
		"db_password_vtiger": os.getenv('VTIGER_PASSWORD'),
		"db_host_vtiger": os.getenv('VTIGER_HOST'),
		"db_port_vtiger": os.getenv('VTIGER_PORT'),
		"db_name_vtiger": os.getenv('VTIGER_DB_NAME'),
		"db_type_vtiger": os.getenv('VTIGER_DB_TYPE'),
		"db_conn_vtiger": os.getenv('VTIGER_DB_CONN'),
		"vt_api_root_endpoint": os.getenv('VTIGER_API_ROOT_ENDPOINT'),
		"vt_api_user": os.getenv('VTIGER_API_USER'),
		"vt_api_token": os.getenv('VTIGER_API_TOKEN'),
	}

	conf = frappe.get_doc("Company Sync Settings")
	db_user = conf.user
	db_password = conf.password
	db_host = conf.host
	db_port = conf.port
	db_name = conf.name_db
	db_type = str(conf.type).islower()
	db_conn = str(conf.connector).islower()

	conf.mi_campo = "Nuevo valor"  # Asigna el nuevo valor a un campo
	conf.save()  # Guarda el documento

	# Update site config with VTiger settings
	#for key, value in vtiger_config.items():
	#    if value:  # Only update if environment variable exists
	#        update_site_config(key, value) 