import frappe
from company_sync.company_sync.overrides.exception.sync_error import SyncError
from sqlalchemy.orm import sessionmaker

from company_sync.company_sync.doctype.company_sync_scheduler.database.engine import get_engine
from company_sync.company_sync.doctype.company_sync_scheduler.database.client import get_client
from company_sync.company_sync.doctype.company_sync_scheduler.config.config import SyncConfig
from company_sync.company_sync.doctype.company_sync_scheduler.syncer.observer.frappe import FrappeProgressObserver
from company_sync.company_sync.doctype.company_sync_scheduler.syncer.strategies.base_strategy import BaseStrategy
from company_sync.company_sync.doctype.company_sync_scheduler.syncer.strategies.aetna_strategy import AetnaStrategy
from company_sync.company_sync.doctype.company_sync_scheduler.syncer.strategies.oscar_strategy import OscarStrategy
from company_sync.company_sync.doctype.company_sync_scheduler.syncer.strategies.ambetter_strategy import AmbetterStrategy
from company_sync.company_sync.doctype.company_sync_scheduler.syncer.strategies.molina_strategy import MolinaStrategy

from company_sync.company_sync.doctype.company_sync_scheduler.syncer.utils import get_fields
from company_sync.company_sync.doctype.company_sync_scheduler.syncer.services.so_service import SOService

#from company_sync.overrides.exception.sync_error import SyncError
from company_sync.company_sync.doctype.company_sync_scheduler.config.logging import setup_logging

from company_sync.company_sync.doctype.company_sync_scheduler.database.unit_of_work import UnitOfWork

# Main Syncer class that orchestrates the VTiger CRM synchronization
class Syncer:
    def __init__(self, doc_name):
        if not get_engine():
            frappe.logger().error("Database engine not initialized")
            return False
        
        
        # Initialize syncer with document name and required components
        self.doc_name = doc_name
        self.vtigercrm_sync = frappe.get_doc("Company Sync Scheduler", doc_name)
        self.progress_observer = FrappeProgressObserver()
        self.unit_of_work = UnitOfWork(lambda: sessionmaker(bind=get_engine())())
        self.config = SyncConfig()

    def sync(self):        
        try:
            logger = setup_logging()
            company = self.vtigercrm_sync.company
            broker = self.vtigercrm_sync.broker
            csv = self.vtigercrm_sync.company_file
            
            # Selecciona la estrategia adecuada según la compañía
            if company == 'Aetna':
                strategy = AetnaStrategy()
            elif company == 'Oscar':
                strategy = OscarStrategy()
            elif company == 'Ambetter':
                strategy = AmbetterStrategy()
            elif company == 'Molina':
                strategy = MolinaStrategy()   
            else:
                # Estrategia por defecto (sin lógica especial)
                class DefaultStrategy(BaseStrategy):
                    def apply_logic(self, df):
                        return df
                    def get_fields(self):
                        return get_fields(company)
                strategy = DefaultStrategy()
            
            vtiger_client = get_client()
            
            service = SOService(csv, company, broker, strategy, vtiger_client, self.doc_name, logger)
            service.process()                
        except Exception as e:
            frappe.logger().error(f"Sync error: {str(e)}")
            
            self.progress_observer.updateError(f"Sync error: {str(e)}", {'doc_name': self.doc_name})
            raise

    def _process_records(self, results):
        # Process each record and update progress
        total_records = len(results)
        frappe.logger().info(f"Found {total_records} records to sync")
        
        for idx, record in enumerate(results, start=1):
            try:
                frappe.db.begin()
                # Update progress through observer
                self.progress_observer.update(idx/total_records, {'doc_name': self.doc_name})
                # Process individual record using RecordProcessor
                self.record_processor.process_record(record, self.config.mapping_file)
                frappe.db.commit()
            except Exception as e:
                frappe.logger().error(f"Error processing record {idx}: {str(e)}")
                self.progress_observer.updateError(f"Error processing record {idx}: {str(e)}", {'doc_name': self.doc_name})
                raise SyncError(f"Failed to process record {idx}") from e