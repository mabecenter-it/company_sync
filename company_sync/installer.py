def before_install():
    save_config_vtigercrm()

def save_config_vtigercrm():
    print("save_config_vtigercrm")
    """Save VTiger CRM configuration from environment variables to site config"""
    import os
    import frappe
    from frappe.installer import update_site_config
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

    # Update site config with VTiger settings
    for key, value in vtiger_config.items():
        if value:  # Only update if environment variable exists
            update_site_config(key, value) 