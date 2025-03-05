# File: company_sync/strategies/aetna_strategy.py
from company_sync.company_sync.doctype.company_sync_scheduler.syncer.strategies.base_strategy import BaseStrategy
from company_sync.company_sync.doctype.company_sync_scheduler.syncer.utils import calculate_term_date, get_fields

class AetnaStrategy(BaseStrategy):
    def __init__(self):
        self.fields = get_fields("aetna")
    
    def apply_logic(self, df):
        df_normalize = df.rename(columns={v: k for k, v in self.fields.items()})

        return df_normalize[(df_normalize['policyStatus'] == 'Active') & (df_normalize['Relationship'] == 'Self')]
