# =============================================
# CONFIG.PY - Configuración global del proyecto
# Proyecto: Pipeline de Estadísticas Hospitalarias
# =============================================

import os

# ---------------------------------------------
# BASE DE DATOS
# ---------------------------------------------
DB_SERVER   = r".\SQLEXPRESS"
DB_NAME     = "hospital_db"
DB_DRIVER   = "ODBC Driver 17 for SQL Server"  # Cambiar a 18 si corresponde

CONNECTION_STRING = (
    f"mssql+pyodbc://{DB_SERVER}/{DB_NAME}"
    f"?driver={DB_DRIVER.replace(' ', '+')}"
    f"&trusted_connection=yes"
)

# ---------------------------------------------
# RUTAS DEL PROYECTO
# ---------------------------------------------
BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
RAW_DIR         = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR   = os.path.join(BASE_DIR, "data", "processed")
REPORTS_DIR     = os.path.join(BASE_DIR, "data", "reports")

# ---------------------------------------------
# CORREO (se usará en Fase 6)
# ---------------------------------------------
EMAIL_SENDER        = "tu_correo@gmail.com"
EMAIL_PASSWORD      = "tu_app_password"       # Contraseña de aplicación Gmail
EMAIL_RECIPIENTS    = ["destinatario@gmail.com"]
EMAIL_SUBJECT       = "Reporte Diario - Estadísticas Hospital Metropolitano"