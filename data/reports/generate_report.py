# =============================================
# GENERATE_REPORT.PY - Generación de Reporte PDF
# Proyecto: Pipeline de Estadísticas Hospitalarias
# =============================================

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import matplotlib
matplotlib.use("Agg")   # Backend sin interfaz gráfica, necesario para generar PDF sin ventanas
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image,
    Table, TableStyle, PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from config import PROCESSED_DIR, REPORTS_DIR


# ---------------------------------------------
# HELPERS
# ---------------------------------------------
def log(mensaje: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {mensaje}")

def leer_processed(nombre: str) -> pd.DataFrame:
    ruta = os.path.join(PROCESSED_DIR, f"{nombre}.csv")
    return pd.read_csv(ruta, encoding="utf-8-sig")

def fig_to_image(fig, width_cm=16) -> Image:
    """Convierte una figura matplotlib a objeto Image de ReportLab via buffer en memoria."""
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)
    plt.close(fig)
    ancho = width_cm * cm
    # Calcular alto proporcional leyendo dimensiones de la figura
    fig_w, fig_h = fig.get_size_inches()
    alto = ancho * (fig_h / fig_w)
    return Image(buf, width=ancho, height=alto)


# ---------------------------------------------
# PALETA Y ESTILO GLOBAL
# ---------------------------------------------
AZUL_OSCURO  = "#1F4E79"
AZUL_MEDIO   = "#2E75B6"
AZUL_CLARO   = "#BDD7EE"
VERDE        = "#375623"
GRISES       = ["#1F4E79", "#2E75B6", "#4472C4", "#70AD47", "#ED7D31", "#FFC000"]

sns.set_theme(style="whitegrid", font="DejaVu Sans")
plt.rcParams.update({
    "axes.titlesize":  12,
    "axes.labelsize":  10,
    "xtick.labelsize":  9,
    "ytick.labelsize":  9,
    "legend.fontsize":  9,
})


# ---------------------------------------------
# GRÁFICOS
# ---------------------------------------------

def grafico_ocupacion_camas(df: pd.DataFrame) -> Image:
    """Barras horizontales: tasa de ocupación por servicio."""
    df = df.sort_values("tasa_ocupacion_pct")
    fig, ax = plt.subplots(figsize=(10, 4))

    bars = ax.barh(df["servicio"], df["tasa_ocupacion_pct"], color=AZUL_MEDIO, edgecolor="white")

    # Línea de referencia al 85% (estándar OMS de ocupación óptima)
    ax.axvline(x=85, color="red", linestyle="--", linewidth=1.2, label="Referencia OMS (85%)")

    # Etiquetas de valor al final de cada barra
    for bar, val in zip(bars, df["tasa_ocupacion_pct"]):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{val}%", va="center", fontsize=9, fontweight="bold")

    ax.set_xlabel("Tasa de Ocupación (%)")
    ax.set_xlim(0, 115)
    ax.set_title("Tasa de Ocupación de Camas por Servicio", fontweight="bold", pad=12)
    ax.legend(loc="lower right")
    fig.tight_layout()
    return fig_to_image(fig)


def grafico_estadia_servicio(df: pd.DataFrame) -> Image:
    """Barras verticales: promedio días de estadía por servicio."""
    df = df.sort_values("promedio_dias", ascending=False)
    fig, ax = plt.subplots(figsize=(10, 4))

    bars = ax.bar(df["servicio"], df["promedio_dias"], color=GRISES[:len(df)], edgecolor="white")

    for bar, val in zip(bars, df["promedio_dias"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                f"{val}d", ha="center", fontsize=9, fontweight="bold")

    ax.set_ylabel("Promedio días")
    ax.set_title("Promedio de Días de Estadía por Servicio", fontweight="bold", pad=12)
    ax.set_ylim(0, df["promedio_dias"].max() * 1.2)
    plt.xticks(rotation=15, ha="right")
    fig.tight_layout()
    return fig_to_image(fig)


def grafico_egresos_mensuales(df: pd.DataFrame) -> Image:
    """Líneas: evolución mensual de egresos totales."""
    df_total = (
        df.groupby("anio_mes")["total_egresos"]
        .sum()
        .reset_index()
        .sort_values("anio_mes")
    )

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(df_total["anio_mes"], df_total["total_egresos"],
            marker="o", color=AZUL_OSCURO, linewidth=2, markersize=5)
    ax.fill_between(df_total["anio_mes"], df_total["total_egresos"],
                    alpha=0.15, color=AZUL_MEDIO)

    ax.set_ylabel("Total egresos")
    ax.set_title("Evolución Mensual de Egresos Hospitalarios", fontweight="bold", pad=12)
    plt.xticks(rotation=45, ha="right")
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    fig.tight_layout()
    return fig_to_image(fig, width_cm=17)


def grafico_atenciones_mensuales(df: pd.DataFrame) -> Image:
    """Líneas múltiples: atenciones ambulatorias por tipo y mes."""
    df_pivot = (
        df.pivot_table(index="anio_mes", columns="tipo_atencion",
                       values="total_atenciones", aggfunc="sum")
        .fillna(0)
        .sort_index()
    )

    fig, ax = plt.subplots(figsize=(12, 4))
    for i, col in enumerate(df_pivot.columns):
        ax.plot(df_pivot.index, df_pivot[col],
                marker="o", linewidth=2, markersize=4,
                label=col, color=GRISES[i % len(GRISES)])

    ax.set_ylabel("Total atenciones")
    ax.set_title("Atenciones Ambulatorias Mensuales por Tipo", fontweight="bold", pad=12)
    ax.legend(loc="upper left", framealpha=0.8)
    plt.xticks(rotation=45, ha="right")
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    fig.tight_layout()
    return fig_to_image(fig, width_cm=17)


def grafico_atenciones_especialidad(df: pd.DataFrame) -> Image:
    """Torta: distribución de atenciones por especialidad."""
    fig, ax = plt.subplots(figsize=(8, 6))

    wedges, texts, autotexts = ax.pie(
        df["total_atenciones"],
        labels=df["especialidad"],
        autopct="%1.1f%%",
        colors=sns.color_palette("Blues_d", len(df)),
        startangle=140,
        pctdistance=0.82
    )
    for at in autotexts:
        at.set_fontsize(8)
        at.set_fontweight("bold")

    ax.set_title("Distribución de Atenciones por Especialidad", fontweight="bold", pad=16)
    fig.tight_layout()
    return fig_to_image(fig, width_cm=13)


def grafico_distribucion_prevision(df: pd.DataFrame) -> Image:
    """Barras apiladas: distribución por previsión y sexo."""
    df_pivot = (
        df.groupby(["prevision", "sexo"])["total"]
        .sum()
        .unstack(fill_value=0)
        .reset_index()
    )

    fig, ax = plt.subplots(figsize=(8, 4))
    bottom = None
    colores_sexo = {"M": AZUL_MEDIO, "F": "#ED7D31"}

    for sexo in [c for c in df_pivot.columns if c != "prevision"]:
        vals = df_pivot[sexo].values
        ax.bar(df_pivot["prevision"], vals,
               bottom=bottom, label=f"Sexo: {sexo}",
               color=colores_sexo.get(sexo, AZUL_CLARO),
               edgecolor="white")
        bottom = vals if bottom is None else bottom + vals

    ax.set_ylabel("Total hospitalizaciones")
    ax.set_title("Hospitalizaciones por Previsión y Sexo", fontweight="bold", pad=12)
    ax.legend()
    fig.tight_layout()
    return fig_to_image(fig, width_cm=12)


# ---------------------------------------------
# ESTILOS REPORTLAB
# ---------------------------------------------
def build_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        "TituloPortada",
        parent=styles["Title"],
        fontSize=22, textColor=colors.HexColor(AZUL_OSCURO),
        spaceAfter=6, alignment=TA_CENTER, fontName="Helvetica-Bold"
    ))
    styles.add(ParagraphStyle(
        "SubtituloPortada",
        parent=styles["Normal"],
        fontSize=13, textColor=colors.HexColor(AZUL_MEDIO),
        spaceAfter=4, alignment=TA_CENTER
    ))
    styles.add(ParagraphStyle(
        "FechaPortada",
        parent=styles["Normal"],
        fontSize=10, textColor=colors.grey,
        alignment=TA_CENTER, spaceAfter=20
    ))
    styles.add(ParagraphStyle(
        "TituloSeccion",
        parent=styles["Heading1"],
        fontSize=13, textColor=colors.HexColor(AZUL_OSCURO),
        spaceBefore=14, spaceAfter=6, fontName="Helvetica-Bold"
    ))
    styles.add(ParagraphStyle(
        "Descripcion",
        parent=styles["Normal"],
        fontSize=9, textColor=colors.HexColor("#444444"),
        spaceAfter=8, leading=13
    ))
    return styles


def tabla_kpis(indicadores: dict, styles) -> Table:
    """Tabla de KPIs para la portada."""
    df_ocup    = indicadores["ind_ocupacion_camas"]
    df_estadia = indicadores["ind_estadia_servicio"]
    df_egresos = indicadores["ind_egresos_mensuales"]
    df_atenc   = indicadores["ind_atenciones_mes"]

    kpis = [
        ["Indicador", "Valor"],
        ["Tasa de ocupación promedio",       f"{df_ocup['tasa_ocupacion_pct'].mean():.1f}%"],
        ["Promedio días de estadía",         f"{df_estadia['promedio_dias'].mean():.1f} días"],
        ["Total egresos (período)",          f"{df_egresos['total_egresos'].sum():,}"],
        ["Total atenciones ambulatorias",    f"{df_atenc['total_atenciones'].sum():,}"],
    ]

    t = Table(kpis, colWidths=[10 * cm, 5 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0),  colors.HexColor(AZUL_OSCURO)),
        ("TEXTCOLOR",    (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",     (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, 0),  11),
        ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS",(0, 1),(-1, -1), [colors.HexColor("#EBF3FB"), colors.white]),
        ("FONTSIZE",     (0, 1), (-1, -1), 10),
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.HexColor("#BBBBBB")),
        ("ROWHEIGHT",    (0, 0), (-1, -1), 22),
    ]))
    return t


# ---------------------------------------------
# NUMERACIÓN DE PÁGINAS
# ---------------------------------------------
def numerar_paginas(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawRightString(
        A4[0] - 1.5 * cm,
        1 * cm,
        f"Página {doc.page}  |  Hospital Metropolitano de Santiago  |  Unidad de Estadísticas"
    )
    canvas.restoreState()


# ---------------------------------------------
# ENSAMBLAJE DEL PDF
# ---------------------------------------------
def generar_pdf(indicadores: dict) -> str:
    os.makedirs(REPORTS_DIR, exist_ok=True)
    fecha_str  = datetime.now().strftime("%Y%m%d")
    nombre_pdf = f"reporte_estadisticas_{fecha_str}.pdf"
    ruta_pdf   = os.path.join(REPORTS_DIR, nombre_pdf)

    doc = SimpleDocTemplate(
        ruta_pdf,
        pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2.5 * cm, bottomMargin=2.5 * cm,
        title="Reporte Estadísticas Hospitalarias",
        author="Unidad de Estadísticas — HOSMET"
    )

    styles  = build_styles()
    story   = []
    fecha_legible = datetime.now().strftime("%d de %B de %Y, %H:%M hrs")

    # ------------------------------------------
    # PORTADA
    # ------------------------------------------
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph("Hospital Metropolitano de Santiago", styles["TituloPortada"]))
    story.append(Paragraph("Reporte de Estadísticas Hospitalarias", styles["SubtituloPortada"]))
    story.append(Paragraph(f"Generado el {fecha_legible}", styles["FechaPortada"]))
    story.append(Paragraph("Unidad de Estadísticas — Depto. Información Sanitaria", styles["FechaPortada"]))
    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor(AZUL_MEDIO)))
    story.append(Spacer(1, 0.8 * cm))
    story.append(tabla_kpis(indicadores, styles))
    story.append(PageBreak())

    # ------------------------------------------
    # SECCIÓN 1: OCUPACIÓN Y ESTADÍA
    # ------------------------------------------
    story.append(Paragraph("1. Ocupación de Camas y Días de Estadía", styles["TituloSeccion"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor(AZUL_CLARO)))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph(
        "La tasa de ocupación de camas mide el porcentaje de camas ocupadas respecto al total disponible "
        "por servicio. La línea roja indica el umbral de referencia del 85% recomendado por la OMS.",
        styles["Descripcion"]
    ))
    story.append(grafico_ocupacion_camas(indicadores["ind_ocupacion_camas"]))
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph(
        "El promedio de días de estadía refleja la complejidad de las patologías atendidas por servicio "
        "y es un indicador clave de eficiencia en la gestión de camas.",
        styles["Descripcion"]
    ))
    story.append(grafico_estadia_servicio(indicadores["ind_estadia_servicio"]))
    story.append(PageBreak())

    # ------------------------------------------
    # SECCIÓN 2: EGRESOS HOSPITALARIOS
    # ------------------------------------------
    story.append(Paragraph("2. Egresos Hospitalarios", styles["TituloSeccion"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor(AZUL_CLARO)))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph(
        "La evolución mensual de egresos permite identificar estacionalidad, peaks de demanda "
        "y tendencias en la utilización hospitalaria a lo largo del período analizado.",
        styles["Descripcion"]
    ))
    story.append(grafico_egresos_mensuales(indicadores["ind_egresos_mensuales"]))
    story.append(PageBreak())

    # ------------------------------------------
    # SECCIÓN 3: ATENCIONES AMBULATORIAS
    # ------------------------------------------
    story.append(Paragraph("3. Atenciones Ambulatorias", styles["TituloSeccion"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor(AZUL_CLARO)))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph(
        "Las atenciones ambulatorias se clasifican en Consulta, Control, Urgencia y Procedimiento. "
        "El análisis mensual por tipo permite evaluar la carga asistencial y planificar recursos.",
        styles["Descripcion"]
    ))
    story.append(grafico_atenciones_mensuales(indicadores["ind_atenciones_mes"]))
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph(
        "La distribución por especialidad identifica las áreas de mayor demanda ambulatoria "
        "para orientar la asignación de horas médicas.",
        styles["Descripcion"]
    ))
    story.append(grafico_atenciones_especialidad(indicadores["ind_atenciones_especialidad"]))
    story.append(PageBreak())

    # ------------------------------------------
    # SECCIÓN 4: PERFIL DE PACIENTES
    # ------------------------------------------
    story.append(Paragraph("4. Perfil de Pacientes Hospitalizados", styles["TituloSeccion"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor(AZUL_CLARO)))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph(
        "La distribución por previsión y sexo permite caracterizar la población usuaria del hospital "
        "y apoya la planificación de políticas de salud y gestión de recursos.",
        styles["Descripcion"]
    ))
    story.append(grafico_distribucion_prevision(indicadores["ind_distribucion_pacientes"]))

    # ------------------------------------------
    # CONSTRUIR PDF
    # ------------------------------------------
    doc.build(story, onFirstPage=numerar_paginas, onLaterPages=numerar_paginas)
    return ruta_pdf


# ---------------------------------------------
# ORQUESTADOR
# ---------------------------------------------
def ejecutar_reporte() -> str:
    log("=" * 50)
    log("Iniciando generación de reporte PDF (Fase 5)")
    log("=" * 50)

    indicadores = {
        "ind_ocupacion_camas":          leer_processed("ind_ocupacion_camas"),
        "ind_estadia_servicio":         leer_processed("ind_estadia_servicio"),
        "ind_estadia_diagnostico":      leer_processed("ind_estadia_diagnostico"),
        "ind_egresos_mensuales":        leer_processed("ind_egresos_mensuales"),
        "ind_atenciones_mes":           leer_processed("ind_atenciones_mes"),
        "ind_atenciones_especialidad":  leer_processed("ind_atenciones_especialidad"),
        "ind_distribucion_pacientes":   leer_processed("ind_distribucion_pacientes"),
    }

    log("Generando gráficos y ensamblando PDF...")
    ruta_pdf = generar_pdf(indicadores)

    log("=" * 50)
    log(f"  ✓ PDF generado → {os.path.basename(ruta_pdf)}")
    log(f"  Ruta: {ruta_pdf}")
    log("=" * 50)

    return ruta_pdf


# ---------------------------------------------
# MAIN
# ---------------------------------------------
def main():
    ejecutar_reporte()


if __name__ == "__main__":
    main()