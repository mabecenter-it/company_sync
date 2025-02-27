# File: company_sync/strategies/ambetter_strategy.py
from company_sync.company_sync.doctype.company_sync_scheduler.syncer.strategies.base_strategy import BaseStrategy
from company_sync.company_sync.doctype.company_sync_scheduler.syncer.utils import get_fields

class AmbetterStrategy(BaseStrategy):
    def __init__(self):
        self.fields = get_fields("ambetter")
    
    def apply_logic(self, df):
        df_normalize = df.rename(columns={v: k for k, v in self.fields.items()})
        df.rename(columns={"Member ID": "memberID"}, inplace=True)
        return df_normalize