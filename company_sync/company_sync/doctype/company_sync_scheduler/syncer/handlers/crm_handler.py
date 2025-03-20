# File: company_sync/handlers/crm_handler.py
import pandas as pd
import logging
from tqdm import tqdm
from company_sync.company_sync.doctype.company_sync_scheduler.syncer.repositories.crm_repository import CRMRepository
from company_sync.company_sync.doctype.company_sync_scheduler.syncer.utils import update_logs, progress_observer


class CRMHandler:
    def __init__(self, doc_name: str, company: str, broker: str):
        self.repo = CRMRepository(company, broker)
        self.company = company
        self.broker = broker
        self.logger = logging.getLogger(__name__)
        self.doc_name = doc_name
    
    def fetch_data(self) -> pd.DataFrame:
        return self.repo.fetch_sales_orders()
    
    def merge_data(self, df_crm: pd.DataFrame, df_csv: pd.DataFrame) -> pd.DataFrame:
        df_merged = pd.merge(df_crm, df_csv, on="memberID", how="outer", indicator=True)
        df_missing = df_merged[df_merged['_merge'] == 'left_only']
        total = len(df_missing)
        for i, (_, row) in enumerate(tqdm(df_missing.iterrows(), total=len(df_missing), desc="Validando Órdenes de Venta..."), start=1):
            memberID = str(row['memberID'])
            progress = float(i / total)
            progress_observer.update(progress, {'doc_name': self.doc_name})
            if row['Problema_2025'] not in ('No portal', 'Problema Campaña', 'Problema Pago', 'Dejar cancelar MP'):
                update_logs(self.doc_name, memberID if memberID else str(row['salesOrder_no']), self.company, self.broker, "Se encontró una orden de venta pero no está en el portal")
        return df_merged[df_merged['_merge'] != 'left_only']
