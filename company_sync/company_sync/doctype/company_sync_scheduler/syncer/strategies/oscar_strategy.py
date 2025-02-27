# File: company_sync/strategies/oscar_strategy.py
from company_sync.company_sync.doctype.company_sync_scheduler.syncer.strategies.base_strategy import BaseStrategy
from company_sync.company_sync.doctype.company_sync_scheduler.syncer.utils import calculate_paid_through_date, get_fields

class OscarStrategy(BaseStrategy):
    def __init__(self):
        self.fields = get_fields("oscar")
    
    def apply_logic(self, df):
        df['Paid Through Date'] = df['Policy status'].apply(
            lambda s: calculate_paid_through_date(s, self.fields['format'])
        )
        df_normalize = df.rename(columns={v: k for k, v in self.fields.items()})

        return df_normalize[df_normalize['policyStatus']!= 'Inactive']