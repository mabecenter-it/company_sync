from sqlalchemy import text
from mabecenter.mabecenter.doctype.vtigercrm_sync.models.vtigercrm_salesordercf import VTigerSalesOrderCF

class QueryService:
    def __init__(self, config):
        self.config = config
        
    def validate_connection(self, session):
        result = session.execute(text("SELECT VERSION();"))
        return result.fetchone()[0]
        
    def fetch_records(self, session):
        return (session.query(VTigerSalesOrderCF)
            .filter(
                VTigerSalesOrderCF.cf_2141.in_(self.config.status_values),
                VTigerSalesOrderCF.cf_2059 == self.config.effective_date,
                VTigerSalesOrderCF.cf_2179 >= self.config.sell_date
            ).order_by(VTigerSalesOrderCF.salesorderid.desc())
            .limit(1)
            .all()
        ) 