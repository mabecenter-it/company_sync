# File: company_sync/repositories/crm_repository.py
from company_sync.company_sync.doctype.company_sync_scheduler.database.engine import get_engine
from company_sync.company_sync.doctype.company_sync_scheduler.database.unit_of_work import UnitOfWork
import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

class CRMRepository:
    def __init__(self, company: str, broker: str):
        self.company = company
        self.broker = broker
        self.unit_of_work = UnitOfWork(lambda: sessionmaker(bind=get_engine())())

    def fetch_sales_orders(self) -> pd.DataFrame:
        with self.unit_of_work as session:
            query = f"""
                SELECT member_id, so_no, Problema_2025
                FROM vtigercrm_2022.calendar_2025_materialized
                WHERE Compañía = '{self.company}'
                  AND Broker = '{'BEATRIZ SIERRA' if self.broker == 'BS' else 'ANA DANIELLA CORRALES'}'
                  AND Terminación >= DATE_FORMAT(CURRENT_DATE(), '%Y-%m-%d')
                  AND Month = DATE_FORMAT(CURRENT_DATE(), '%Y-%m-01')
                  AND rn = OV_Count;
            """
            
            result = session.execute(text(query)).fetchall()
            return pd.DataFrame(result, columns=["memberID", "salesOrder_no", "Problema_2025"])