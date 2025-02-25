import frappe
from .base import ProgressObserver

class FrappeProgressObserver(ProgressObserver):
    def update(self, percentage: float, context: dict, event = 'company_sync_refresh'):
        frappe.publish_realtime(
            event,
            {
                'percentage': f"{percentage * 100:.2f}",
                'company_sync': context['doc_name']
            }
        )
    
    def updateError(self, error_log: str, context: dict, event = 'company_sync_error_log'):
        frappe.publish_realtime(
            event,
            {
                'error_log': error_log,
                'company_sync': context['doc_name']
            }
        )
    
    def updateLog(self, context: dict, event = 'company_sync_error_log'):
        frappe.publish_realtime(
            event,
            {
                'error_log': context['message'],
                'company_sync': context['doc_name'],
                'memberID': context['memberID'],
                'company': context['company'],
                'broker': context['broker']
            }
        )

