# =============================================
# MAIN.PY - Orquestador del Pipeline Completo
# Proyecto: Pipeline de Estadísticas Hospitalarias
# =============================================
# Este es el único script que Task Scheduler ejecutará.
# Llama a cada fase en orden y detiene el pipeline si
# alguna falla, registrando el error en un log de archivo.
# =============================================

import sys
import os
import traceback
from datetime import datetime

# Asegurar que la raíz del proyecto esté en el path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from config import CONNECTION_STRING, REPORTS_DIR, BASE_DIR

from etl.extract       import ejecutar_extraccion
from etl.transform     import ejecutar_transformacion
from etl.load          import ejecutar_carga
from data.reports.generate_report import ejecutar_reporte
from data.reports.send_email      import enviar_correo


# ---------------------------------------------
# LOG A ARCHIVO (además de consola)
# ---------------------------------------------
LOG_DIR  = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f"pipeline_{datetime.now().strftime('%Y%m%d')}.log")

class Logger:
    """Escribe simultáneamente en consola y en archivo de log."""
    def __init__(self, filepath):
        self.terminal = sys.stdout
        self.log      = open(filepath, "a", encoding="utf-8")

    def write(self, mensaje):
        self.terminal.write(mensaje)
        self.log.write(mensaje)

    def flush(self):
        self.terminal.flush()
        self.log.flush()

sys.stdout = Logger(LOG_FILE)


# ---------------------------------------------
# HELPERS
# ---------------------------------------------
def log(mensaje: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {mensaje}")

def separador():
    print("=" * 55)


# ---------------------------------------------
# PIPELINE PRINCIPAL
# ---------------------------------------------
def main():
    inicio = datetime.now()
    separador()
    log("PIPELINE DE ESTADÍSTICAS HOSPITALARIAS — INICIO")
    log(f"Fecha de ejecución: {inicio.strftime('%d/%m/%Y %H:%M:%S')}")
    separador()

    try:
        # ------------------------------------------
        # FASE 2: EXTRACCIÓN
        # ------------------------------------------
        log("▶ FASE 2: Extracción")
        engine = create_engine(CONNECTION_STRING)
        ejecutar_extraccion(engine)
        log("✓ Extracción completada.\n")

        # ------------------------------------------
        # FASE 3: TRANSFORMACIÓN
        # ------------------------------------------
        log("▶ FASE 3: Transformación")
        ejecutar_transformacion()
        log("✓ Transformación completada.\n")

        # ------------------------------------------
        # FASE 4: CARGA
        # ------------------------------------------
        log("▶ FASE 4: Carga")
        ruta_xlsx = ejecutar_carga()
        log("✓ Carga completada.\n")

        # ------------------------------------------
        # FASE 5: GENERACIÓN DE REPORTE PDF
        # ------------------------------------------
        log("▶ FASE 5: Generación de reporte PDF")
        ruta_pdf = ejecutar_reporte()
        log("✓ Reporte PDF generado.\n")

        # ------------------------------------------
        # FASE 6: ENVÍO DE CORREO
        # ------------------------------------------
        log("▶ FASE 6: Envío de correo")
        exito = enviar_correo([ruta_pdf, ruta_xlsx])
        if not exito:
            log("⚠ El correo no pudo enviarse, pero el pipeline completó las demás fases.")
        else:
            log("✓ Correo enviado.\n")

        # ------------------------------------------
        # RESUMEN FINAL
        # ------------------------------------------
        duracion = (datetime.now() - inicio).seconds
        separador()
        log("PIPELINE COMPLETADO EXITOSAMENTE")
        log(f"Duración total: {duracion} segundos")
        log(f"Archivos generados:")
        log(f"  → {os.path.basename(ruta_pdf)}")
        log(f"  → {os.path.basename(ruta_xlsx)}")
        log(f"Log guardado en: {LOG_FILE}")
        separador()

    except Exception as e:
        separador()
        log(f"✗ ERROR CRÍTICO EN EL PIPELINE: {e}")
        log("Traceback completo:")
        traceback.print_exc()
        separador()
        sys.exit(1)   # Código de salida 1 indica error a Task Scheduler


if __name__ == "__main__":
    main()