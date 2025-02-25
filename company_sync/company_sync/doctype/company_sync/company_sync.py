# Copyright (c) 2024, Dante Devenir and contributors
# For license information, please see license.txt

# Import Frappe framework components
import frappe
from frappe import _
# Import sync implementation
#from company_sync.company_sync.doctype.vtigercrm_sync.syncer.factory.factory import HandlerFactory
#from company_sync.company_sync.doctype.vtigercrm_sync.syncer.record import RecordProcessor
from company_sync.company_sync.doctype.company_sync.syncer.syncer import Syncer
# Import job timeout exception
from rq.timeouts import JobTimeoutException
# Import document base class
from frappe.model.document import Document
# Import background job utilities
from frappe.utils.background_jobs import enqueue, is_job_enqueued

class CompanySync(Document):
	def before_save(self):
		# Set sync timestamp before saving
		self.sync_on = self.creation

	def start_sync(self):
		# Import scheduler status check
		from frappe.utils.scheduler import is_scheduler_inactive

		# Determine if sync should run immediately
		run_now = frappe.flags.in_test or frappe.conf.developer_mode
		if is_scheduler_inactive() and not run_now:
			frappe.throw(_("Scheduler is inactive. Cannot import data."), title=_("Scheduler Inactive"))

		# Create unique job ID
		job_id = f"company_sync::{self.name}"

		# Enqueue sync job if not already running
		if not is_job_enqueued(job_id):
			enqueue(
				start_sync,
				queue="default",
				timeout=10000,
				event="company_sync",
				job_id=job_id,
				company_sync=self.name,
				now=run_now,
			)
			return True

		return False
	
	def get_sync_logs(self):
		# Get sync logs
		#doc = frappe.get_doc("Company Sync", self.name)
		#doc.check_permission("read")

		print("company_sync.company_sync.doctype.company_sync.get_sync_logs")

		return frappe.get_all(
			"Company Sync Log",
			fields=["*"],
			filters={"company_sync": self.name},
			limit_page_length=5000,
			order_by="log_index",
		)

@frappe.whitelist(allow_guest=True)
def form_start_sync(company_sync: str):
	# Start sync from form
	return frappe.get_doc("Company Sync", company_sync).start_sync()	

@frappe.whitelist(allow_guest=True)
def get_sync_logs(company_sync: str):
	return frappe.get_doc("Company Sync", company_sync).get_sync_logs()


def start_sync(company_sync):
	"""This method runs in background job"""
	try:
		# Execute sync process
		Syncer(doc_name=company_sync).sync()
	except JobTimeoutException:
		# Handle timeout
		frappe.db.rollback()
		doc = frappe.get_doc("Company Sync", company_sync)
		doc.db_set("status", "Timed Out")
	except Exception:
		# Handle general errors
		frappe.db.rollback()
		doc = frappe.get_doc("Company Sync", company_sync)
		doc.db_set("status", "Error")
		doc.log_error("Company Sync failed")
	finally:
		# Reset import flag
		frappe.flags.in_import = False