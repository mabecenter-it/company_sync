from company_sync.company_sync.doctype.company_sync.syncer.WSClient import VTigerWSClient
import frappe
from company_sync.company_sync.overrides.exception.sync_error import SyncError
from sqlalchemy.orm import sessionmaker

from company_sync.company_sync.doctype.company_sync.database.engine import get_engine
from company_sync.company_sync.doctype.company_sync.config.config import SyncConfig
from company_sync.company_sync.doctype.company_sync.syncer.observer.frappe import FrappeProgressObserver
from company_sync.company_sync.doctype.company_sync.syncer.strategies.base_strategy import BaseStrategy
from company_sync.company_sync.doctype.company_sync.syncer.strategies.aetna_strategy import AetnaStrategy
from company_sync.company_sync.doctype.company_sync.syncer.strategies.oscar_strategy import OscarStrategy

from company_sync.company_sync.doctype.company_sync.syncer.utils import get_fields
from company_sync.company_sync.doctype.company_sync.syncer.services.so_service import SOService

#from mabecenter.overrides.exception.sync_error import SyncError
from company_sync.company_sync.doctype.company_sync.config.logging import setup_logging

from company_sync.company_sync.doctype.company_sync.database.unit_of_work import UnitOfWork
from company_sync.company_sync.doctype.company_sync.syncer.record import RecordProcessor

# Main Syncer class that orchestrates the VTiger CRM synchronization
class Syncer:
    def __init__(self, doc_name):
        if not get_engine():
            frappe.logger().error("Database engine not initialized")
            return False
        
        from mabecenter.mabecenter.doctype.vtigercrm_sync.syncer.services.query import QueryService
        
        # Initialize syncer with document name and required components
        self.doc_name = doc_name
        self.vtigercrm_sync = frappe.get_doc("Company Sync", doc_name)
        self.progress_observer = FrappeProgressObserver()
        self.unit_of_work = UnitOfWork(lambda: sessionmaker(bind=get_engine())())
        self.config = SyncConfig()
  
        # Initialize services
        self.query_service = QueryService(self.config)
        self.record_processor = RecordProcessor(self.config)

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
            else:
                # Estrategia por defecto (sin lógica especial)
                class DefaultStrategy(BaseStrategy):
                    def apply_logic(self, df):
                        return df
                    def get_fields(self):
                        return get_fields(company)
                strategy = DefaultStrategy()
            
            vtiger_client = VTigerWSClient(frappe.conf.vt_api_root_endpoint)
            vtiger_client.doLogin(frappe.conf.vt_api_user, frappe.conf.vt_api_token)
            
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