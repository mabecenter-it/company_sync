import frappe
from datetime import date
import json
from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class SyncConfig:
    status_values: list = field(default_factory=lambda: ['Active', 'Initial Enrollment', 'Sin Digitar'])
    effective_date: date = field(default_factory=lambda: date(2025, 1, 1))
    sell_date: date = field(default_factory=lambda: date(2024, 10, 28))
    
    def __post_init__(self):
        self.mapping_file = self._load_mapping('salesorder')
        self.handle_file = self._load_mapping('handler')

    def _load_mapping(self, filename: str) -> Dict[str, Any]:
        filename = frappe.get_app_path(
            'company_sync', 'company_sync', 'doctype', 
            'company_sync_scheduler', 'config', 'mapping', f'{filename}.json'
        )
        with open(filename, 'r', encoding='utf-8') as file:
            return json.load(file) 