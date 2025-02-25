from company_sync.company_sync.doctype.company_sync_scheduler.syncer.WSClient import VTigerWSClient
import frappe


def get_client():
    conf = frappe.get_doc("Company Sync Settings")
    api_user = conf.user_api
    api_endpoint = conf.endpoint
    api_token = conf.get_password("token")

    client = VTigerWSClient(api_endpoint)
    client.doLogin(api_user, api_token)

    return client