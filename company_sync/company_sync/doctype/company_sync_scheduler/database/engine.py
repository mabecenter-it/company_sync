# Import Frappe framework for configuration access
import frappe
# Import SQLAlchemy engine creation function
from sqlalchemy import create_engine

def get_engine():
    """
    Crea y devuelve un motor de SQLAlchemy basado en la configuración de Frappe.
    """
    # Obtener detalles de conexión a la base de datos desde la configuración de Frappe
    conf = frappe.get_doc("Company Sync Settings")
    db_user = conf.user
    db_password = conf.get_password("password")
    db_host = conf.host
    db_port = conf.port
    db_name = conf.name_db
    db_type = str(conf.type).lower()
    db_conn = str(conf.connector).lower()

    # Construir la cadena de conexión MySQL
    if all([db_user, db_password, db_host, db_port, db_name]):
        connection_string = f"{db_type}+{db_conn}://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    else:
        frappe.logger().error("Faltan detalles de conexión para VTigerCRM.")
        connection_string = None

    # Crear el motor de SQLAlchemy con configuraciones de pooling
    if connection_string:
        try:
            engine = create_engine(
                connection_string,
                pool_pre_ping=True,         # Verificar la conexión antes de usarla
                pool_timeout=30,            # Tiempo de espera de la conexión en segundos
                pool_recycle=3600,          # Reciclar conexiones después de 1 hora
                connect_args={
                    "connect_timeout": 10   # Tiempo de espera de conexión MySQL
                }
            )
            return engine
        except Exception as e:
            frappe.logger().error(f"Error al crear el motor de SQLAlchemy: {e}")
            return None
    else:
        frappe.logger().error("No se pudo construir la cadena de conexión. El motor no se creó.")
        return None
