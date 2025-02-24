class BaseDocumentExist(Exception):
    def __init__(self, message, doctype_name):
        super().__init__(message)
        self.doctype_name = doctype_name