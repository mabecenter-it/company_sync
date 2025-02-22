from frappe import _
from mabecenter.setup.setup_wizard.operations import install_fixtures as fixtures

def get_setup_stages(args=None):
	return [
		{
			"status": _("Setting item default"),
			"fail_msg": "Failed to set defaults",
			"tasks": [
				{"fn": setup_item_default, "args": args, "fail_msg": _("Failed to setup defaults")},
			],
		},
	]

def setup_item_default(args):
	fixtures.install()