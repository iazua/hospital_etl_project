# =============================================
# TRANSFORM.PY - Capa de Transformación (T)
# Proyecto: Pipeline de Estadísticas Hospitalarias
# =============================================

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime

from config import RAW_DIR, PROCESSED_DIR


# ---------------------------------------------
# HELPERS
# ---------------------------------------------
def log(mensaje: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {mensaje}")

def guardar_csv(df: pd.DataFrame, nombre: str):
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    ruta = os.path.join(PROCESSED_DIR, f"{nombre}.csv")
    df.to_csv(ruta, index=False, encoding="utf-8-sig")
    log(f"  ✓ {nombre}.csv guardado → {len(df):,} registros.")

def leer_raw(nombre: str) -> pd.DataFrame:
    ruta = os.path.join(RAW_DIR, f"{nombre}.csv")
    return pd.read_csv(ruta, encoding="utf-8-sig")


# ---------------------------------------------
# PASO 1: LIMPIEZA Y VALIDACIÓN
# ---------------------------------------------
def limpiar_hospitalizaciones(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia y valida el DataFrame principal de hospitalizaciones_detalle.
    Registra en consola cualquier inconsistencia encontrada.
    """
    log("Limpiando hospitalizaciones_detalle...")
    total_original = len(df)

    # Convertir fechas desde string a datetime
    df["fecha_ingreso"]      = pd.to_datetime(df["fecha_ingreso"],      errors="coerce")
    df["fecha_egreso"]       = pd.to_datetime(df["fecha_egreso"],       errors="coerce")
    df["fecha_nacimiento"]   = pd.to_datetime(df["fecha_nacimiento"],   errors="coerce")

    # Detectar y reportar fechas inválidas (coerce las convierte a NaT)
    fechas_invalidas = df["fecha_ingreso"].isna().sum()
    if fechas_invalidas > 0:
        log(f"  ⚠ {fechas_invalidas} registros con fecha_ingreso inválida → eliminados.")
    df = df.dropna(subset=["fecha_ingreso"])

    # Detectar inconsistencia lógica: egreso antes que ingreso
    mask_inconsistente = df["fecha_egreso"] < df["fecha_ingreso"]
    inconsistentes = mask_inconsistente.sum()
    if inconsistentes > 0:
        log(f"  ⚠ {inconsistentes} registros con fecha_egreso < fecha_ingreso → eliminados.")
    df = df[~mask_inconsistente]

    # Estandarizar columnas de texto a Title Case
    df["nombre_completo"] = df["nombre_completo"].str.strip().str.title()
    df["comuna"]          = df["comuna"].str.strip().str.title()
    df["servicio"]        = df["servicio"].str.strip()

    # Rellenar nulos en motivo_egreso (pacientes aún hospitalizados)
    df["motivo_egreso"] = df["motivo_egreso"].fillna("En curso")

    # Calcular edad al momento del ingreso
    df["edad_ingreso"] = (
        (df["fecha_ingreso"] - df["fecha_nacimiento"]).dt.days // 365
    ).astype("Int64")   # Int64 (nullable) para manejar posibles NaT

    # Grupo etario para segmentación en reportes
    bins   = [0, 14, 29, 44, 59, 74, 200]
    labels = ["0-14", "15-29", "30-44", "45-59", "60-74", "75+"]
    df["grupo_etario"] = pd.cut(df["edad_ingreso"], bins=bins, labels=labels, right=True)

    # Recalcular dias_estadia en pandas para mayor control
    # (complementa el DATEDIFF que ya venía desde SQL)
    df["dias_estadia"] = (df["fecha_egreso"] - df["fecha_ingreso"]).dt.days

    eliminados = total_original - len(df)
    log(f"  → Limpieza completada: {eliminados} registros eliminados de {total_original:,} originales.")
    return df


def limpiar_atenciones(df: pd.DataFrame) -> pd.DataFrame:
    log("Limpiando atenciones ambulatorias...")

    df["fecha_atencion"] = pd.to_datetime(df["fecha_atencion"], errors="coerce")
    df = df.dropna(subset=["fecha_atencion"])

    df["especialidad"]        = df["especialidad"].str.strip().str.title()
    df["medico_responsable"]  = df["medico_responsable"].str.strip().str.title()

    log(f"  → {len(df):,} atenciones válidas.")
    return df


# ---------------------------------------------
# PASO 2: CÁLCULO DE INDICADORES
# ---------------------------------------------

def calcular_estadia_por_servicio(df: pd.DataFrame) -> pd.DataFrame:
    """
    Promedio, mínimo y máximo de días de estadía por servicio.
    Solo considera hospitalizaciones con egreso (dias_estadia no nulo).
    """
    log("Calculando estadía por servicio...")
    resultado = (
        df.dropna(subset=["dias_estadia"])
        .groupby("servicio")["dias_estadia"]
        .agg(
            total_egresos="count",
            promedio_dias=lambda x: round(x.mean(), 1),
            min_dias="min",
            max_dias="max"
        )
        .reset_index()
        .sort_values("promedio_dias", ascending=False)
    )
    return resultado


def calcular_estadia_por_diagnostico(df: pd.DataFrame) -> pd.DataFrame:
    """Promedio de días de estadía por categoría diagnóstica."""
    log("Calculando estadía por diagnóstico...")
    resultado = (
        df.dropna(subset=["dias_estadia"])
        .groupby(["categoria_diagnostico", "diagnostico"])["dias_estadia"]
        .agg(
            total_casos="count",
            promedio_dias=lambda x: round(x.mean(), 1)
        )
        .reset_index()
        .sort_values("promedio_dias", ascending=False)
    )
    return resultado


def calcular_ocupacion_camas(df: pd.DataFrame, total_camas_por_servicio: pd.Series) -> pd.DataFrame:
    """
    Tasa de ocupación de camas por servicio.
    Fórmula: (camas ocupadas actualmente / total camas del servicio) * 100
    Considera 'ocupadas' las hospitalizaciones sin fecha de egreso (En curso).
    """
    log("Calculando ocupación de camas...")
    ocupadas = (
        df[df["motivo_egreso"] == "En curso"]
        .groupby("servicio")
        .size()
        .reset_index(name="camas_ocupadas")
    )
    resultado = ocupadas.merge(
        total_camas_por_servicio.reset_index(),
        on="servicio",
        how="left"
    )
    resultado.columns = ["servicio", "camas_ocupadas", "total_camas"]
    resultado["tasa_ocupacion_pct"] = (
        (resultado["camas_ocupadas"] / resultado["total_camas"]) * 100
    ).round(1)
    resultado = resultado.sort_values("tasa_ocupacion_pct", ascending=False)
    return resultado


def calcular_egresos_mensuales(df: pd.DataFrame) -> pd.DataFrame:
    """Egresos por mes, servicio y motivo de egreso."""
    log("Calculando egresos mensuales...")
    df_egreso = df[df["motivo_egreso"] != "En curso"].copy()
    df_egreso["anio_mes"] = df_egreso["fecha_egreso"].dt.to_period("M").astype(str)
    resultado = (
        df_egreso.groupby(["anio_mes", "servicio", "motivo_egreso"])
        .size()
        .reset_index(name="total_egresos")
        .sort_values(["anio_mes", "servicio"])
    )
    return resultado


def calcular_atenciones_por_mes(df: pd.DataFrame) -> pd.DataFrame:
    """Atenciones ambulatorias por mes y tipo."""
    log("Calculando atenciones ambulatorias por mes...")
    df["anio_mes"] = df["fecha_atencion"].dt.to_period("M").astype(str)
    resultado = (
        df.groupby(["anio_mes", "tipo_atencion"])
        .size()
        .reset_index(name="total_atenciones")
        .sort_values("anio_mes")
    )
    return resultado


def calcular_atenciones_por_especialidad(df: pd.DataFrame) -> pd.DataFrame:
    """Total de atenciones por especialidad."""
    log("Calculando atenciones por especialidad...")
    resultado = (
        df.groupby("especialidad")
        .size()
        .reset_index(name="total_atenciones")
        .sort_values("total_atenciones", ascending=False)
    )
    return resultado


def calcular_distribucion_pacientes(df: pd.DataFrame) -> pd.DataFrame:
    """Distribución de hospitalizaciones por previsión, sexo y grupo etario."""
    log("Calculando distribución de pacientes...")
    resultado = (
        df.groupby(["prevision", "sexo", "grupo_etario"], observed=True)
        .size()
        .reset_index(name="total")
        .sort_values(["prevision", "sexo", "grupo_etario"])
    )
    return resultado


# ---------------------------------------------
# ORQUESTADOR DE TRANSFORMACIONES
# ---------------------------------------------
def ejecutar_transformacion() -> dict:
    log("=" * 50)
    log("Iniciando transformación de datos (Capa T)")
    log("=" * 50)

    # Leer datos crudos
    df_hosp     = leer_raw("hospitalizaciones_detalle")
    df_atenc    = leer_raw("atenciones")
    df_camas    = leer_raw("camas")

    # Limpieza
    df_hosp  = limpiar_hospitalizaciones(df_hosp)
    df_atenc = limpiar_atenciones(df_atenc)

    # Total de camas por servicio (necesario para tasa de ocupación)
    camas_por_servicio = df_camas.groupby("servicio").size()

    # Calcular todos los indicadores
    indicadores = {
        "ind_estadia_servicio":       calcular_estadia_por_servicio(df_hosp),
        "ind_estadia_diagnostico":    calcular_estadia_por_diagnostico(df_hosp),
        "ind_ocupacion_camas":        calcular_ocupacion_camas(df_hosp, camas_por_servicio),
        "ind_egresos_mensuales":      calcular_egresos_mensuales(df_hosp),
        "ind_atenciones_mes":         calcular_atenciones_por_mes(df_atenc),
        "ind_atenciones_especialidad":calcular_atenciones_por_especialidad(df_atenc),
        "ind_distribucion_pacientes": calcular_distribucion_pacientes(df_hosp),
    }

    # Guardar cada indicador como CSV en data/processed/
    log("-" * 50)
    log("Guardando indicadores en data/processed/...")
    for nombre, df in indicadores.items():
        guardar_csv(df, nombre)

    # También guardar el detalle limpio completo
    guardar_csv(df_hosp,  "hospitalizaciones_limpio")
    guardar_csv(df_atenc, "atenciones_limpio")

    log("=" * 50)
    log(f"Transformación completada → {len(indicadores) + 2} archivos en data/processed/")
    log("=" * 50)

    return indicadores


# ---------------------------------------------
# MAIN
# ---------------------------------------------
def main():
    ejecutar_transformacion()


if __name__ == "__main__":
    main()