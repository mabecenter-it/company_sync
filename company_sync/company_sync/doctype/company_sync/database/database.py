from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import company_sync.company_sync.company_sync.doctype.company_sync.config.config as config

# Crear la conexión utilizando la URI definida en config
engine = create_engine(config.SQLALCHEMY_DATABASE_URI, echo=False)
Session = sessionmaker(bind=engine)

def get_session():
    """
    Retorna una nueva sesión de base de datos.
    """
    return Session()