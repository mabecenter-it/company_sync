import frappe
from .base import ProgressObserver

class FrappeProgressObserver(ProgressObserver):
    def update(self, percentage: float, context: dict, event = 'vtigercrm_sync_refresh'):
        frappe.publish_realtime(
            event,
            {
                'percentage': f"{percentage * 100:.2f}",
                'vtigercrm_sync': context['doc_name']
            }
        )
    
    def updateError(self, error_log: str, context: dict, event = 'vtigercrm_sync_error_log'):
        frappe.publish_realtime(
            event,
            {
                'error_log': error_log,
                'vtigercrm_sync': context['doc_name']
            }
        )

