# =============================================
# SEND_EMAIL.PY - Envío Automático de Correo
# Proyecto: Pipeline de Estadísticas Hospitalarias
# =============================================

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

from config import (
    EMAIL_SENDER, EMAIL_PASSWORD,
    EMAIL_RECIPIENTS, EMAIL_SUBJECT
)


# ---------------------------------------------
# HELPERS
# ---------------------------------------------
def log(mensaje: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {mensaje}")


# ---------------------------------------------
# CUERPO DEL CORREO EN HTML
# ---------------------------------------------
def construir_cuerpo_html(fecha: str, archivos_adjuntos: list) -> str:
    nombres = "".join(f"<li>📎 {os.path.basename(a)}</li>" for a in archivos_adjuntos)
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333333; max-width: 600px; margin: auto;">

        <div style="background-color: #1F4E79; padding: 20px; border-radius: 6px 6px 0 0;">
            <h2 style="color: white; margin: 0;">🏥 Hospital Metropolitano de Santiago</h2>
            <p style="color: #BDD7EE; margin: 4px 0 0 0;">
                Unidad de Estadísticas — Depto. Información Sanitaria
            </p>
        </div>

        <div style="background-color: #f9f9f9; padding: 24px; border: 1px solid #dddddd;">
            <p>Estimado/a equipo,</p>
            <p>
                Se adjunta el <strong>Reporte Diario de Estadísticas Hospitalarias</strong>
                generado automáticamente el <strong>{fecha}</strong>.
            </p>

            <p><strong>Archivos adjuntos:</strong></p>
            <ul>{nombres}</ul>

            <p>El reporte incluye los siguientes indicadores de gestión:</p>
            <ul>
                <li>Tasa de ocupación de camas por servicio</li>
                <li>Promedio de días de estadía</li>
                <li>Evolución mensual de egresos hospitalarios</li>
                <li>Atenciones ambulatorias por tipo y especialidad</li>
                <li>Perfil de pacientes hospitalizados</li>
            </ul>

            <div style="background-color: #EBF3FB; border-left: 4px solid #2E75B6;
                        padding: 12px; margin: 16px 0; border-radius: 3px;">
                <p style="margin: 0; font-size: 13px; color: #1F4E79;">
                    ⚙️ Este correo fue generado y enviado automáticamente
                    por el pipeline de estadísticas. No responder a este mensaje.
                </p>
            </div>
        </div>

        <div style="background-color: #eeeeee; padding: 10px 24px;
                    border-radius: 0 0 6px 6px; font-size: 11px; color: #888888;">
            Hospital Metropolitano de Santiago &nbsp;|&nbsp;
            Servicio de Salud Metropolitano Oriente &nbsp;|&nbsp;
            {fecha}
        </div>

    </body>
    </html>
    """


# ---------------------------------------------
# FUNCIÓN PRINCIPAL DE ENVÍO
# ---------------------------------------------
def enviar_correo(archivos_adjuntos: list) -> bool:
    """
    Envía un correo con los archivos indicados como adjuntos.

    Parámetros:
        archivos_adjuntos: lista de rutas absolutas a los archivos a adjuntar.

    Retorna:
        True si el envío fue exitoso, False si ocurrió algún error.
    """
    log("=" * 50)
    log("Iniciando envío de correo (Fase 6)")
    log("=" * 50)

    fecha_legible = datetime.now().strftime("%d/%m/%Y %H:%M hrs")

    # -- Construir mensaje MIME --
    msg = MIMEMultipart("alternative")
    msg["From"]    = EMAIL_SENDER
    msg["To"]      = ", ".join(EMAIL_RECIPIENTS)
    msg["Subject"] = f"{EMAIL_SUBJECT} — {datetime.now().strftime('%d/%m/%Y')}"

    # Versión texto plano (fallback para clientes que no renderizan HTML)
    cuerpo_texto = (
        f"Reporte Diario de Estadísticas Hospitalarias\n"
        f"Generado el {fecha_legible}\n\n"
        f"Se adjuntan {len(archivos_adjuntos)} archivo(s) con los indicadores del día.\n"
        f"Este correo fue generado automáticamente. No responder."
    )
    msg.attach(MIMEText(cuerpo_texto, "plain", "utf-8"))

    # Versión HTML
    cuerpo_html = construir_cuerpo_html(fecha_legible, archivos_adjuntos)
    msg.attach(MIMEText(cuerpo_html, "html", "utf-8"))

    # -- Adjuntar archivos --
    for ruta in archivos_adjuntos:
        if not os.path.exists(ruta):
            log(f"  ⚠ Archivo no encontrado, se omite: {ruta}")
            continue
        with open(ruta, "rb") as f:
            parte = MIMEBase("application", "octet-stream")
            parte.set_payload(f.read())
        encoders.encode_base64(parte)
        parte.add_header(
            "Content-Disposition",
            f"attachment; filename={os.path.basename(ruta)}"
        )
        msg.attach(parte)
        log(f"  📎 Adjunto: {os.path.basename(ruta)}")

    # -- Enviar vía Gmail SMTP --
    try:
        log(f"  Conectando a smtp.gmail.com:587...")
        with smtplib.SMTP("smtp.gmail.com", 587) as servidor:
            servidor.ehlo()
            servidor.starttls()          # Cifrado TLS
            servidor.ehlo()
            servidor.login(EMAIL_SENDER, EMAIL_PASSWORD)
            servidor.sendmail(
                EMAIL_SENDER,
                EMAIL_RECIPIENTS,
                msg.as_bytes()
            )
        log(f"  ✓ Correo enviado exitosamente a: {', '.join(EMAIL_RECIPIENTS)}")
        log("=" * 50)
        return True

    except smtplib.SMTPAuthenticationError:
        log("  ✗ Error de autenticación. Verifica EMAIL_SENDER y EMAIL_PASSWORD en config.py")
        log("    Recuerda usar una Contraseña de Aplicación de Gmail, no tu contraseña personal.")
        return False
    except smtplib.SMTPException as e:
        log(f"  ✗ Error SMTP: {e}")
        return False
    except Exception as e:
        log(f"  ✗ Error inesperado: {e}")
        return False


# ---------------------------------------------
# MAIN (para probar envío de forma aislada)
# ---------------------------------------------
def main():
    from config import REPORTS_DIR
    fecha_str = datetime.now().strftime("%Y%m%d")
    adjuntos = [
        os.path.join(REPORTS_DIR, f"reporte_estadisticas_{fecha_str}.pdf"),
        os.path.join(REPORTS_DIR, f"reporte_estadisticas_{fecha_str}.xlsx"),
    ]
    enviar_correo(adjuntos)


if __name__ == "__main__":
    main()