import frappe
from .base import ProgressObserver

class FrappeProgressObserver(ProgressObserver):
    def update(self, percentage: float, context: dict, event = 'company_sync_refresh'):
        frappe.publish_realtime(
            event,
            {
                'percentage': f"{percentage * 100:.2f}",
            },
            docname=context['doc_name'],
        )
    
    def updateError(self, error_log: str, context: dict, event = 'company_sync_error_log'):
        frappe.publish_realtime(
            event,
            {
                'error_log': error_log,
            },
            docname=context['doc_name'],
        )
    
    def updateLog(self, context: dict, event = 'company_sync_error_log'):
        frappe.publish_realtime(
            event,
            {
                'error_log': context['message'],
                'memberID': context['memberID'],
                'company': context['company'],
                'broker': context['broker']
            },
            docname=context['doc_name'],
        )
    
    
    def updateSuccess(self, context: dict, event = 'company_sync_success'):
        frappe.publish_realtime(
            event,
            {
                'success': context['success'],
            },
            docname=context['doc_name'],
        )


