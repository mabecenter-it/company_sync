# File: company_sync/handlers/so_updater.py
import datetime
import logging
from company_sync.company_sync.doctype.company_sync_scheduler.database.engine import get_engine
from company_sync.company_sync.doctype.company_sync_scheduler.database.unit_of_work import UnitOfWork
from sqlalchemy import text
import frappe
from sqlalchemy.orm import sessionmaker
from company_sync.company_sync.doctype.company_sync_scheduler.syncer.utils import add_business_days, last_day_of_month, update_logs, progress_observer

class SOUpdater:
    def __init__(self, vtiger_client, company: str, data_config: dict, broker: str, doc_name: str, logger=None):
        self.vtiger_client = vtiger_client
        self.company = company
        self.data_config = data_config
        self.broker = broker
        self.doc_name = doc_name
        self.logger = logger if logger is not None else logging.getLogger(__name__)
        self.unit_of_work = UnitOfWork(lambda: sessionmaker(bind=get_engine())())
    
    def update_sales_order(self, memberID: str, paidThroughDate: str, salesOrderData: dict):
        try:
            if salesOrderData.get('cf_2261') != paidThroughDate:
                salesOrderData['cf_2261'] = paidThroughDate
                salesOrderData['productid'] = '14x29415'
                salesOrderData['assigned_user_id'] = '19x113'
                salesOrderData['LineItems'] = {
                    'productid': '14x29415',
                    'listprice': '0',
                    'quantity': '1'
                }
                return self.vtiger_client.doUpdate(salesOrderData)
        except Exception as e:
            self.logger.error(f"Error updating memberID {memberID}: {e}")
            return None

    def process_order(self, row):
        memberID = str(row['memberID'])
        paidThroughDateString = str(row.get('paidThroughDate', ''))
        policyTermDateString = str(row.get('policyTermDate', ''))
        paidThroughDate = None
        policyTermDate = None

        if paidThroughDateString not in ('None', '', 'nan'):
            paidThroughDate = datetime.datetime.strptime(paidThroughDateString, self.data_config['format']).date()
        if policyTermDateString not in ('None', '', 'nan'):
            policyTermDate = datetime.datetime.strptime(policyTermDateString, '%m/%d/%Y').date()
        if policyTermDate and self.company.lower() == 'molina':
            policyTermDate = datetime.datetime.strptime('12/31/2025', '%m/%d/%Y').date()

        if (policyTermDate and policyTermDate > datetime.date(2025, 1, 1)) or (paidThroughDate and paidThroughDate > datetime.date(2025, 1, 1)):
            try:
                with self.unit_of_work as session:
                    query = f"""
                        SELECT *
                        FROM vtigercrm_2022.calendar_2025_materialized
                        WHERE member_id = '{memberID}'
                          AND Terminación >= DATE_FORMAT(CURRENT_DATE(), '%Y-%m-%d')
                          AND Month >= DATE_FORMAT(CURRENT_DATE(), '%Y-%m-01')
                        LIMIT 1;
                    """
                    results = session.execute(text(query)).fetchone()
                    if results:
                        problem = results[10]
                        paidThroughDateCRM = results[12]
                        salesOrderTermDateCRM = results[13]
                        salesOrderEffecDateCRM = results[25]
                        salesOrderBrokerCRM = results[16]
                        salesorder_no = results[1]
                        tipoPago =  results[20]
                        diaPago = results[21]

                        if problem == 'Problema Pago':
                            pass
                        elif salesOrderTermDateCRM and salesOrderTermDateCRM == policyTermDate:
                            if paidThroughDate and paidThroughDate >= datetime.datetime.strptime(last_day_of_month(datetime.date.today()), '%B %d, %Y').date():
                                query_sales = f"SELECT * FROM SalesOrder WHERE salesorder_no = '{salesorder_no}' LIMIT 1;"
                                [salesOrderData] = self.vtiger_client.doQuery(query_sales)
                                if paidThroughDateCRM and paidThroughDate < paidThroughDateCRM:
                                    if not (self.company == 'Oscar' and paidThroughDateCRM >= paidThroughDate):   
                                        #self.logger.info(f"A la póliza le rebotó la fecha de pago", extra={'memberid': memberID, 'company': self.company, 'broker': self.broker})
                                        update_logs(self.doc_name, memberID, self.company, self.broker, f"A la póliza le rebotó la fecha de pago")
                                elif not paidThroughDateCRM or paidThroughDate > paidThroughDateCRM:
                                    response = self.update_sales_order(memberID, paidThroughDate.strftime('%Y-%m-%d'), salesOrderData)
                                    if response and not response['success']:
                                        if not response['error']['message'] == "Permission to perform the operation is denied":
                                            #self.logger.info(f"No se encontró la orden de venta", extra={'memberid': memberID, 'company': self.company, 'broker': self.broker})
                                            update_logs(self.doc_name, memberID, self.company, self.broker, "No se encontró la orden de venta")
                            else:
                                if not salesOrderEffecDateCRM > datetime.date.today():
                                    if not salesOrderBrokerCRM == 'BROKER ERROR' and tipoPago in ("CALENDAR", "YES") and diaPago > add_business_days(datetime.date.today(), 3):
                                        #self.logger.info(f"Se encontró una orden de venta pero no está paga al {datetime.datetime.strptime(last_day_of_month(datetime.date.today()), '%B %d, %Y').date().strftime('%Y-%m-%d')}", extra={'memberid': memberID, 'company': self.company, 'broker': self.broker})
                                        update_logs(self.doc_name, memberID, self.company, self.broker, f"Se encontró una orden de venta pero no está paga al {datetime.datetime.strptime(last_day_of_month(datetime.date.today()), '%B %d, %Y').date().strftime('%Y-%m-%d')}")
                        else:
                            if not policyTermDate or salesOrderTermDateCRM == policyTermDate:
                                #self.logger.info(f"No se encontró una orden de venta pero si está en el portal", extra={'memberid': memberID, 'company': self.company, 'broker': self.broker})
                                update_logs(self.doc_name, memberID, self.company, self.broker, "No se encontró una orden de venta pero si está en el portal")
                            else:
                                update_logs(self.doc_name, memberID, self.company, self.broker, f"En el portal la fecha de terminación es { policyTermDate.strftime('%m/%d/%Y') }")
                    elif (policyTermDate and policyTermDate > datetime.date(2025, 1, 1)) or (paidThroughDate and paidThroughDate > datetime.date(2025, 1, 1)):
                        #self.logger.info(f"La póliza no está en el crm", extra={'memberid': memberID, 'company': self.company, 'broker': self.broker})
                        update_logs(self.doc_name, memberID, self.company, self.broker, "La póliza no está en el crm")
            except Exception as e:
                #self.logger.error(f"Error procesando memberID {memberID}: {e}", extra={'memberid': memberID, 'company': self.company, 'broker': self.broker})
                update_logs(self.doc_name, memberID, self.company, self.broker, f"Error procesando memberID {memberID}: {e}")

    def update_orders(self, df):
        total = len(df)
        for idx, row in df.iterrows():
            self.process_order(row,)
            # Calcula el progreso en porcentaje
            progress = float((idx + 1) / total)
            # Guarda el progreso en caché
            progress_observer.update(progress, {'doc_name': self.doc_name})
        
        progress_observer.updateSuccess(1, {'doc_name': self.doc_name})
