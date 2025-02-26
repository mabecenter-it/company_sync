from frappe import _
from company_sync.setup.setup_wizard.operations import install_fixtures as fixtures

def get_setup_stages(args=None):
	return [
		{
			"status": _("Setting item default"),
			"fail_msg": "Failed to set defaults",
			"tasks": [
				{"fn": setup_company_sync_settings, "args": args, "fail_msg": _("Failed to setup defaults")},
			],
		},
	]

def setup_company_sync_settings(args):
	fixtures.create_company_sync_settings(args)
