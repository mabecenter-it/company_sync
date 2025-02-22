import frappe
from sqlalchemy.orm import sessionmaker

from mabecenter.mabecenter.doctype.vtigercrm_sync.database.engine import get_engine
from mabecenter.mabecenter.doctype.vtigercrm_sync.config.config import SyncConfig
from mabecenter.mabecenter.doctype.vtigercrm_sync.syncer.observer.frappe import FrappeProgressObserver
from mabecenter.overrides.exception.sync_error import SyncError

from mabecenter.mabecenter.doctype.vtigercrm_sync.database.unit_of_work import UnitOfWork
from mabecenter.mabecenter.doctype.vtigercrm_sync.syncer.record import RecordProcessor

# Main Syncer class that orchestrates the VTiger CRM synchronization
class Syncer:
    def __init__(self, doc_name):
        if not get_engine():
            frappe.logger().error("Database engine not initialized")
            return False
        
        from mabecenter.mabecenter.doctype.vtigercrm_sync.syncer.services.query import QueryService
        
        # Initialize syncer with document name and required components
        self.doc_name = doc_name
        self.vtigercrm_sync = frappe.get_doc("VTigerCRM Sync", doc_name)
        self.progress_observer = FrappeProgressObserver()
        self.unit_of_work = UnitOfWork(lambda: sessionmaker(bind=get_engine())())
        self.config = SyncConfig()
  
        # Initialize services
        self.query_service = QueryService(self.config)
        self.record_processor = RecordProcessor(self.config)

    def sync(self):        
        try:
            logger = setup_logging()
            
            # Selecciona la estrategia adecuada según la compañía
            if args.company.lower() == 'aetna':
                strategy = AetnaStrategy()
            elif args.company.lower() == 'oscar':
                strategy = OscarStrategy()
            else:
                # Estrategia por defecto (sin lógica especial)
                class DefaultStrategy(BaseStrategy):
                    def apply_logic(self, df):
                        return df
                    def get_fields(self):
                        from company_sync.utils import get_fields
                        return get_fields(args.company)
                strategy = DefaultStrategy()
            
            vtiger_client = VTigerWSClient(config.VTIGER_HOST)
            vtiger_client.doLogin(config.VTIGER_USERNAME, config.VTIGER_TOKEN)
            
            service = SOService(args.csv, args.company, args.broker, strategy, vtiger_client, logger)
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