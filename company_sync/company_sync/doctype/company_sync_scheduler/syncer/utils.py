# File: company_sync/utils.py
import datetime
from company_sync.company_sync.doctype.company_sync_scheduler.syncer.observer.frappe import FrappeProgressObserver
import frappe
from dateutil.relativedelta import relativedelta


def get_fields(company: str) -> dict:
    company = company.lower()
    fields = {
        'aetna': {
            'memberID': 'Issuer Assigned ID',
            'paidThroughDate': 'Paid Through Date',
            'policyTermDate': 'Broker Term Date',
            'format': '%B %d, %Y',
            'policyStatus': 'Policy Status'
        },
        'oscar': {
            'memberID': 'Member ID',
            'paidThroughDate': 'Paid Through Date',
            'policyTermDate': 'Coverage end date',
            'format': '%B %d, %Y',
            'policyStatus': 'Policy status'
        },
        'ambetter': {
            'memberID': 'Policy Number',
            'paidThroughDate': 'Paid Through Date',
            'policyTermDate': 'Policy Term Date',
            'format': '%m/%d/%Y'
        },
        'molina': {
            'memberID': 'Subscriber_ID',
            'paidThroughDate': 'Paid_Through_Date',
            'policyTermDate': 'Broker_End_Date',
            'format': '%m/%d/%Y',
            'policyStatus': 'Status'
        }
    }
    default = {
        'memberID': 'Member ID',
        'paidThroughDate': 'Paid Through Date',
        'format': '%m/%d/%Y'
    }
    return fields.get(company, default)

def conditional_update(company: str) -> dict:
    company = company.lower()
    if company == 'aetna':
        return {'Relationship': 'Self', 'Policy Status': 'Active'}
    elif company == 'ambetter':
        return {'Payable Agent': 'Health Family Insurance'}
    elif company == 'molina':
        return {'Status': 'Active'}
    elif company == 'oscar':
        return {'cond': '!=', 'Policy status': 'Inactive'}
    return {}

def calculate_paid_through_date(status: str, date_format: str = '%B %d, %Y') -> str:
    today = datetime.date.today()
    if status == 'Active' or status == 'Paid binder':
        return last_day_of_month(today, date_format)
    elif status == 'Delinquent':
        two_months_ago = (today.replace(day=1) - datetime.timedelta(days=1))
        two_months_ago = (two_months_ago.replace(day=1) - datetime.timedelta(days=1))
        return last_day_of_month(two_months_ago, date_format)
    elif status == 'Grace period':
        last_month = today.replace(day=1) - datetime.timedelta(days=1)
        return last_day_of_month(last_month, date_format)
    else:
        return ''

def calculate_term_date(effective_date: str, input_format: str = '%B %d, %Y') -> str:
    effective_dt = datetime.datetime.strptime(effective_date, input_format)
    term_date = effective_dt.replace(year=effective_dt.year + 1, month=12)
    return last_day_of_month(term_date, input_format)

def last_day_of_month(any_day: datetime.date, date_format: str = '%B %d, %Y') -> str:
    next_month = any_day.replace(day=28) + datetime.timedelta(days=4)
    last_day = next_month - datetime.timedelta(days=next_month.day)
    return last_day.strftime(date_format)

progress_observer = FrappeProgressObserver()

def current_paid_date(day: int) -> datetime.datetime:
    now = datetime.datetime.now()
    
    try:
        # Try to create a date with the specified day
        paidDate = datetime.datetime(year=now.year, month=now.month, day=day)
    except ValueError:
        # If the day is out of range, set the paidDate to the last day of the current month
        paidDate = datetime.datetime(year=now.year, month=now.month, day=1) + relativedelta(day=31)


    # Si el día está entre 1 y 5, no restamos un mes
    if 1 <= day <= 5:
        return paidDate
    else:
        try:
            # Intentamos restar un mes
            return paidDate - relativedelta(months=1)
        except ValueError:
            # Si hay un error por día fuera de rango, ajustamos el día al último del mes anterior
            last_day_previous_month = (paidDate - relativedelta(day=31))
            return last_day_previous_month
            

def update_logs(doc_name, memberID, company, broker, error_log):
    doc_parent = frappe.get_doc('Company Sync Scheduler', doc_name)
    doc_parent.append("sync_log", {
        "memberid": memberID,
        "messages": error_log,
    })
    doc_parent.save()
    frappe.db.commit() 
    progress_observer.updateLog({'message': error_log, 'doc_name': doc_parent.name, 'memberID': memberID, 'company': company, 'broker': broker})

def add_business_days(start_date, business_days):
    current_date = start_date
    days_added = 0
    while days_added < business_days:
        current_date += datetime.timedelta(days=1)
        # En Python, Monday es 0 y Friday es 4; Saturday es 5 y Sunday es 6
        if current_date.weekday() < 5:
            days_added += 1
    return current_date