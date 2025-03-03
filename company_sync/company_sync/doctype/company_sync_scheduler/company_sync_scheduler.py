# Copyright (c) 2024, Dante Devenir and contributors
# For license information, please see license.txt

# Import Frappe framework components
import frappe
from frappe import _
# Import sync implementation
#from company_sync_scheduler.company_sync_scheduler.doctype.vtigercrm_sync.syncer.factory.factory import HandlerFactory
#from company_sync_scheduler.company_sync_scheduler.doctype.vtigercrm_sync.syncer.record import RecordProcessor
from company_sync.company_sync.doctype.company_sync_scheduler.syncer.syncer import Syncer
# Import job timeout exception
import frappe.realtime
from rq.timeouts import JobTimeoutException
# Import document base class
from frappe.model.document import Document
# Import background job utilities
from frappe.utils.background_jobs import enqueue, is_job_enqueued

class CompanySyncScheduler(Document):
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
		job_id = f"company_sync_scheduler::{self.name}"

		# Enqueue sync job if not already running
		if not is_job_enqueued(job_id):
			enqueue(
				start_sync,
				queue="default",
				timeout=10000,
				event="company_sync_scheduler",
				job_id=job_id,
				company_sync_scheduler=self.name,
				now=run_now,
			)
			return True

		return False
	
	def get_sync_logs(self):
		# Get sync logs
		#doc = frappe.get_doc("Company Sync", self.name)
		#doc.check_permission("read")

		return frappe.get_all(
			"Company Sync Log",
			fields=["*"],
			filters={"company_sync": self.name},
			limit_page_length=5000,
			order_by="log_index",
		)

@frappe.whitelist(allow_guest=True)
def update_log_review(name: str, review: str):
	#return frappe.get_doc("Company Sync Scheduler", company_sync_scheduler, filter["memberid"]).update_review(review)
	doc_log =  frappe.get_doc("Company Sync Log", name)
	doc_log.review = review
	doc_log.save()

@frappe.whitelist(allow_guest=True)
def form_start_sync(company_sync_scheduler: str):
	# Start sync from form
	return frappe.get_doc("Company Sync Scheduler", company_sync_scheduler).start_sync()	

@frappe.whitelist(allow_guest=True)
def get_sync_logs(company_sync_scheduler: str):
	return frappe.get_doc("Company Sync Scheduler", company_sync_scheduler).get_sync_logs()


def start_sync(company_sync_scheduler):
	"""This method runs in background job"""
	try:
		# Execute sync process
		Syncer(doc_name=company_sync_scheduler).sync()
	except JobTimeoutException:
		# Handle timeout
		frappe.db.rollback()
		doc = frappe.get_doc("Company Sync Scheduler", company_sync_scheduler)
		doc.db_set("status", "Timed Out")
	except Exception as e:
		# Handle general errors
		frappe.db.rollback()
		doc = frappe.get_doc("Company Sync Scheduler", company_sync_scheduler)
		doc.db_set("status", "Error")
		doc.log_error("Company Sync failed")
	finally:
		# Reset import flag
		frappe.flags.in_import = False
		#frappe.realtime()
		#frappe.db.commit
		doc = frappe.get_doc("Company Sync Scheduler", company_sync_scheduler)
		doc.db_set("status", "Success")
