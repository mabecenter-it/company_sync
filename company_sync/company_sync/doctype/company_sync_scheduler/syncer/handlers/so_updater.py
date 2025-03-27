# File: company_sync/handlers/so_updater.py
import datetime
import logging
from company_sync.company_sync.doctype.company_sync_scheduler.database.engine import get_engine
from company_sync.company_sync.doctype.company_sync_scheduler.database.unit_of_work import UnitOfWork
from sqlalchemy import text
import frappe
from sqlalchemy.orm import sessionmaker
from company_sync.company_sync.doctype.company_sync_scheduler.syncer.utils import add_business_days, last_day_of_month, update_logs, progress_observer, current_paid_date
from tqdm import tqdm

class SOUpdater:
    def __init__(self, vtiger_client, company: str, data_config: dict, broker: str, doc_name: str, logger=None):
        self.vtiger_client = vtiger_client
        self.company = company
        self.data_config = data_config
        self.broker = broker
        self.doc_name = doc_name
        self.logger = logger if logger is not None else logging.getLogger(__name__)
        self.unit_of_work = UnitOfWork(lambda: sessionmaker(bind=get_engine())())
    
    def update_sales_order(self, memberID: str, paidThroughDate: str, salesorder_no: dict):
        try:
            def getSOAllData(salesorder_no, memberID):
                query_sales = f"SELECT * FROM SalesOrder WHERE salesorder_no = '{salesorder_no}' AND cf_2119 = '{memberID}' LIMIT 1;"
                salesOrderData = self.vtiger_client.doQuery(query_sales)
                return salesOrderData
            
            [salesOrderData] = getSOAllData(salesorder_no, memberID)

            if paidThroughDate > salesOrderData.get('cf_2261'):
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

        if (policyTermDate and policyTermDate > datetime.date(2025, 1, 1)) or (paidThroughDate and paidThroughDate >= datetime.date(2024, 12, 31)):
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
                        problem, paidThroughDateCRM, salesOrderTermDateCRM, salesOrderEffecDateCRM = results[10], results[12], results[26], results[25]
                        salesOrderBrokerCRM, salesorder_no, tipoPago, diaPago = results[16], results[1], results[20], results[21]

                        if self.should_skip_update(tipoPago, diaPago) or self.should_skip_broker(salesOrderBrokerCRM, salesOrderEffecDateCRM):
                            return
                        
                        if self.validPaid(paidThroughDate):
                            if not paidThroughDateCRM or paidThroughDate > paidThroughDateCRM:
                                self.update_sales_order(memberID, paidThroughDate.strftime('%Y-%m-%d'), salesorder_no)
                                if problem in ('Problema Pago', 'Problema Campaña', 'Dejar cancelar MP'):
                                    update_logs(self.doc_name, memberID, self.company, self.broker, f"Se actualiza pago hasta pero continúa como problema")
                        elif paidThroughDateCRM and paidThroughDate and paidThroughDate < paidThroughDateCRM:
                            update_logs(self.doc_name, memberID, self.company, self.broker, f"A la póliza le rebotó la fecha de pago")
                        elif problem not in ('Problema Pago', 'Problema Campaña', 'Dejar cancelar MP'):
                            update_logs(self.doc_name, memberID, self.company, self.broker, f"Se encontró una orden de venta pero no está paga al {datetime.datetime.strptime(last_day_of_month(datetime.date.today()), '%B %d, %Y').date().strftime('%Y-%m-%d')}")

                        if policyTermDate and problem not in ('Problema Campaña', 'Dejar cancelar MP') and not self.validTerm(policyTermDate, salesOrderTermDateCRM):
                            update_logs(self.doc_name, memberID, self.company, self.broker, f"En el portal la fecha de terminación es { policyTermDate.strftime('%m/%d/%Y') }")
                            return
                    elif (policyTermDate and policyTermDate > datetime.date(2025, 1, 1)) or (paidThroughDate and paidThroughDate > datetime.date(2025, 1, 1)):
                        update_logs(self.doc_name, memberID, self.company, self.broker, "La póliza no está en el crm")
            except Exception as e:
                update_logs(self.doc_name, memberID, self.company, self.broker, f"Error procesando memberID {memberID}: {e}")

    def should_skip_update(self, tipoPago, diaPago):
        return tipoPago in ("CALENDAR", "YES") and datetime.date.today() < add_business_days(current_paid_date(diaPago), 3).date()

    def should_skip_broker(self, salesOrderBrokerCRM, salesOrderEffecDateCRM):
        last_day = datetime.datetime.strptime(last_day_of_month(datetime.date.today()), '%B %d, %Y').date()
        return salesOrderBrokerCRM == 'BROKER ERROR' or salesOrderEffecDateCRM > last_day

    def validPaid(self, paidThroughDate):
        return paidThroughDate and paidThroughDate >= datetime.datetime.strptime(last_day_of_month(datetime.date.today()), '%B %d, %Y').date()

    def validTerm(self, policyTermDate, salesOrderTermDateCRM):
        return policyTermDate and salesOrderTermDateCRM and policyTermDate == salesOrderTermDateCRM

    def update_orders(self, df):
        total = len(df)
        for i, (_, row) in enumerate(tqdm(df.iterrows(), total=len(df), desc="Validando Órdenes de Venta 2..."), start=1):
            self.process_order(row)
            # Calcula el progreso en porcentaje
            progress = float(i / total)
            # Guarda el progreso en caché
            progress_observer.update(progress, {'doc_name': self.doc_name})
        
        progress_observer.updateSuccess({'success': True, 'doc_name': self.doc_name})
