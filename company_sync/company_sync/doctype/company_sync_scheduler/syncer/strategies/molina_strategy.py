# File: company_sync/strategies/molina_strategy.py
from company_sync.company_sync.doctype.company_sync_scheduler.syncer.strategies.base_strategy import BaseStrategy
from company_sync.company_sync.doctype.company_sync_scheduler.syncer.utils import get_fields

class MolinaStrategy(BaseStrategy):
    def __init__(self):
        self.fields = get_fields("molina")
    
    def apply_logic(self, df):
        df_normalize = df.rename(columns={v: k for k, v in self.fields.items()})

        return df_normalize[df_normalize['policyStatus'] == 'Active']