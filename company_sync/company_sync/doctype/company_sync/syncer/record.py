from typing import Dict, Any, Optional, List
import frappe
from frappe import _

from mabecenter.mabecenter.doctype.vtigercrm_sync.config.config import SyncConfig
from mabecenter.mabecenter.doctype.vtigercrm_sync.syncer.factory.factory import HandlerFactory

class RecordProcessor:
    def __init__(self, config: SyncConfig):
        self.handler_factory = HandlerFactory()
        self.handlers = {
            entity_type: {
                'handler': self.handler_factory.create_handler(config['doctype']),
                'links': config['links'] if 'links' in config else [],
                'depends_on': config['depends_on'] if 'depends_on' in config else []
            }
            for entity_type, config in config.handle_file.items()
        }
        self.processing_stack = set()

    def determine_processing_order(self) -> List[str]:
        """Determine order of entity processing based on dependencies"""
        order = []
        visited = set()
        
        def visit(entity_type):
            if entity_type in self.processing_stack:
                raise ValueError(f"Circular dependency detected for {entity_type}")
            
            if entity_type in visited:
                return
                
            self.processing_stack.add(entity_type)
            handler_info = self.handlers.get(entity_type, {})
            
            for dependency in handler_info.get('depends_on', []):
                visit(dependency)
                
            self.processing_stack.remove(entity_type)
            visited.add(entity_type)
            order.append(entity_type)
            
        for entity_type in self.handlers:
            visit(entity_type)
            
        return order

    def process_record(self, record, fields):
        # Get mapped data from VTiger record
        mapped_data = record.as_dict(fields)
        processed_results = {}
        processed_dependencies = {}

        # Process each entity type in order of dependencies
        processing_order = self.determine_processing_order()

        for entity_type in processing_order:
            if entity_type not in self.handlers:
                continue

            entity_data = mapped_data.get(entity_type)
            
            if not entity_data:
                continue

            if self.handlers[entity_type]['depends_on']:
                processed_dependencies = self._resolve_dependencies(self.handlers[entity_type]['depends_on'], {}, processed_results)

            # Special handling for contacts from owner/spouse/dependents
            if entity_type == 'Contact':
                self._process_contact_entities(entity_data, mapped_data, processed_results, processed_dependencies)
            else:
                # Normal entity processing
                result = self._create_entity(entity_type, entity_data, processed_dependencies)
                if result:
                    processed_results[entity_type] = result

        for entity_type in processed_results:
            if self.handlers[entity_type]['links']:
                self.handlers[entity_type]['handler'].attach_links(entity_type, processed_results, self.handlers)

        return processed_results

    def _process_contact_entities(self, entity_data, mapped_data, processed_results, processed_dependencies):
        contact_info = mapped_data.get('Contact', {})

        # Procesar owner como contacto principal
        if 'owner' in contact_info:
            owner_data = contact_info['owner']
            owner_data['is_primary_contact'] = 1
            contact = self._create_entity('Contact', owner_data, processed_dependencies)
            customer = self._create_entity('Customer', owner_data, processed_dependencies)
            if contact:
                processed_results.setdefault('Contact', []).append(contact)
                customer = self._create_entity('Customer', owner_data, processed_dependencies)
                if customer:
                    processed_results['Customer'] = customer

        # Procesar contacto de spouse
        if 'spouse' in contact_info:
            spouse_data = contact_info['spouse']
            spouse_data['is_primary_contact'] = 0
            contact = self._create_entity('Contact', spouse_data, processed_dependencies)
            if contact:
                processed_results.setdefault('Contact', []).append(contact)

        # Procesar contacto de dependent
        if 'dependent_1' in contact_info:
            dependent_data = contact_info['dependent_1']
            dependent_data['is_primary_contact'] = 0
            contact = self._create_entity('Contact', dependent_data, processed_dependencies)
            if contact:
                processed_results.setdefault('Contact', []).append(contact)

    def _create_entity(self, entity_type: str, data: Dict[str, Any], processed_dependencies) -> Optional[Any]:
        """Crea un nuevo documento sin dependencias"""
        if not data:
            return None

        processed_data = self._preprocess_data(data)
        handler_info = self.handlers[entity_type]

        try:
            return handler_info['handler'].process(processed_data, processed_dependencies)
        except Exception as e:
            frappe.logger().error(f"Error en _create_entity para {entity_type}: {str(e)}")
            raise

    def _update_dependencies(self, entity_type: str, doc: Any, results: Dict[str, Any]):
        """Actualiza el documento con sus dependencias"""
        handler_info = self.handlers[entity_type]

        if not handler_info.get('depends_on'):
            return

        dependencies = {}
        for dependency in handler_info['depends_on']:
            if dependency in results and results[dependency]:
                dependencies[dependency] = results[dependency].name

        if dependencies:
            try:
                handler_info['handler'].update(doc, {}, **dependencies)
            except Exception as e:
                frappe.logger().error(f"Error actualizando dependencias para {entity_type}: {str(e)}")
                raise

    def _resolve_dependencies(self, depends_on: List[str], results: Dict[str, Any], kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resuelve las dependencias para un handler basado en resultados previos y kwargs adicionales.
        
        Args:
            depends_on: Lista de nombres de dependencias
            results: Diccionario con resultados previamente procesados
            kwargs: Argumentos adicionales
            
        Returns:
            Diccionario con dependencias resueltas
        """
        dependencies = {}

        if not depends_on:
            return dependencies

        for dependency in depends_on:
            if dependency in results:
                dependencies[dependency] = results[dependency]
            elif dependency in kwargs:
                dependencies[dependency] = kwargs[dependency]

        return dependencies

    def _preprocess_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preprocesa los datos de entrada eliminando valores None y cadenas vacías.
        
        Args:
            data: Diccionario con los datos a procesar
            
        Returns:
            Diccionario con datos limpios
        """
        return {
            k: v for k, v in data.items() 
            if v is not None and v != ''
        }
