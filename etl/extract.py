# =============================================
# EXTRACT.PY - Capa de Extracción (E)
# Proyecto: Pipeline de Estadísticas Hospitalarias
# =============================================

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime

from config import CONNECTION_STRING, RAW_DIR


# ---------------------------------------------
# HELPERS
# ---------------------------------------------
def log(mensaje: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {mensaje}")

def guardar_csv(df: pd.DataFrame, nombre: str):
    """Guarda un DataFrame como CSV en data/raw/ e imprime resumen."""
    os.makedirs(RAW_DIR, exist_ok=True)
    ruta = os.path.join(RAW_DIR, f"{nombre}.csv")
    df.to_csv(ruta, index=False, encoding="utf-8-sig")  # utf-8-sig para compatibilidad con Excel
    log(f"  ✓ {nombre}.csv guardado → {len(df):,} registros, {len(df.columns)} columnas.")


# ---------------------------------------------
# QUERIES DE EXTRACCIÓN
# ---------------------------------------------

# Tablas base completas
QUERY_PACIENTES = """
    SELECT
        paciente_id,
        rut,
        nombre,
        apellido,
        fecha_nacimiento,
        sexo,
        comuna,
        prevision,
        fecha_registro
    FROM dbo.pacientes
"""

QUERY_CAMAS = """
    SELECT
        cama_id,
        numero_cama,
        servicio,
        tipo,
        estado
    FROM dbo.camas
"""

QUERY_DIAGNOSTICOS = """
    SELECT
        diagnostico_id,
        codigo_cie10,
        descripcion,
        categoria
    FROM dbo.diagnosticos
"""

QUERY_ATENCIONES = """
    SELECT
        a.atencion_id,
        a.paciente_id,
        a.diagnostico_id,
        a.fecha_atencion,
        a.tipo_atencion,
        a.especialidad,
        a.medico_responsable,
        a.created_at
    FROM dbo.atenciones_ambulatorias a
"""

QUERY_HOSPITALIZACIONES = """
    SELECT
        h.hospitalizacion_id,
        h.paciente_id,
        h.cama_id,
        h.diagnostico_id,
        h.fecha_ingreso,
        h.fecha_egreso,
        h.motivo_egreso,
        h.medico_responsable,
        h.created_at
    FROM dbo.hospitalizaciones h
"""

# Query consolidada con JOINs para indicadores de gestión
# Esta es la más importante del pipeline: une toda la info relevante
# de una hospitalización en una sola fila lista para analizar
QUERY_HOSPITALIZACIONES_DETALLE = """
    SELECT
        h.hospitalizacion_id,
        -- Datos del paciente
        p.rut,
        p.nombre + ' ' + p.apellido        AS nombre_completo,
        p.fecha_nacimiento,
        p.sexo,
        p.comuna,
        p.prevision,
        -- Datos de la hospitalización
        h.fecha_ingreso,
        h.fecha_egreso,
        h.motivo_egreso,
        h.medico_responsable,
        -- Días de estadía calculados en SQL
        -- DATEDIFF devuelve NULL si fecha_egreso es NULL (aún hospitalizados)
        DATEDIFF(DAY, h.fecha_ingreso, h.fecha_egreso)  AS dias_estadia,
        -- Datos de la cama
        c.numero_cama,
        c.servicio,
        c.tipo                              AS tipo_cama,
        -- Datos del diagnóstico
        d.codigo_cie10,
        d.descripcion                       AS diagnostico,
        d.categoria                         AS categoria_diagnostico
    FROM dbo.hospitalizaciones h
        INNER JOIN dbo.pacientes    p ON h.paciente_id    = p.paciente_id
        INNER JOIN dbo.camas        c ON h.cama_id        = c.cama_id
        INNER JOIN dbo.diagnosticos d ON h.diagnostico_id = d.diagnostico_id
"""


# ---------------------------------------------
# FUNCIONES DE EXTRACCIÓN
# ---------------------------------------------
def extraer_tabla(engine, query: str, nombre: str) -> pd.DataFrame:
    """Ejecuta una query y retorna el resultado como DataFrame."""
    log(f"Extrayendo {nombre}...")
    df = pd.read_sql(query, engine)
    guardar_csv(df, nombre)
    return df


def ejecutar_extraccion(engine) -> dict:
    """
    Ejecuta todas las extracciones y retorna un diccionario
    con todos los DataFrames crudos.
    """
    log("=" * 50)
    log("Iniciando extracción de datos (Capa E)")
    log("=" * 50)

    dataframes = {
        "pacientes":                  extraer_tabla(engine, QUERY_PACIENTES,                 "pacientes"),
        "camas":                      extraer_tabla(engine, QUERY_CAMAS,                     "camas"),
        "diagnosticos":               extraer_tabla(engine, QUERY_DIAGNOSTICOS,              "diagnosticos"),
        "atenciones":                 extraer_tabla(engine, QUERY_ATENCIONES,                "atenciones"),
        "hospitalizaciones":          extraer_tabla(engine, QUERY_HOSPITALIZACIONES,         "hospitalizaciones"),
        "hospitalizaciones_detalle":  extraer_tabla(engine, QUERY_HOSPITALIZACIONES_DETALLE, "hospitalizaciones_detalle"),
    }

    log("=" * 50)
    log(f"Extracción completada → {len(dataframes)} archivos en data/raw/")
    log("=" * 50)

    return dataframes


# ---------------------------------------------
# MAIN (para probar esta capa de forma aislada)
# ---------------------------------------------
def main():
    engine = create_engine(CONNECTION_STRING)
    ejecutar_extraccion(engine)


if __name__ == "__main__":
    main()