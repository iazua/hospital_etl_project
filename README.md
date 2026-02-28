# 🏥 Pipeline de Estadísticas Hospitalarias

Pipeline ETL automatizado que extrae, transforma, carga y reporta indicadores de gestión hospitalaria desde una base de datos SQL Server, generando un reporte PDF y Excel enviado automáticamente por correo cada día.

Proyecto desarrollado como práctica personal orientada al cargo de **Profesional de Apoyo de Análisis de Datos** en unidades de estadística del sector salud público.

---

## 📋 Descripción

El sistema simula el flujo de trabajo de una Unidad de Estadísticas hospitalaria real, procesando datos de la Ficha Clínica Electrónica (FCE) para generar indicadores de gestión diarios de forma completamente automatizada.

Cada ejecución del pipeline realiza el ciclo completo en menos de 15 segundos:

```
SQL Server → Extracción → Transformación → Carga Excel → Reporte PDF → Correo automático
```

---

## 🛠️ Stack Tecnológico

| Tecnología | Uso |
|---|---|
| **SQL Server Express 2022** | Base de datos principal (motor OLTP) |
| **Python 3.13** | Lenguaje del pipeline ETL |
| **SQLAlchemy + pyodbc** | Conexión y extracción desde SQL Server |
| **pandas** | Transformación y cálculo de indicadores |
| **openpyxl** | Generación de reporte Excel con formato |
| **matplotlib + seaborn** | Visualización de indicadores |
| **reportlab** | Ensamblaje del reporte PDF |
| **smtplib** | Envío automático de correo |
| **Task Scheduler (Windows)** | Automatización de ejecución diaria |

---

## 📁 Estructura del Proyecto

```
hospital_etl_project/
│
├── data/
│   ├── raw/                          # CSVs extraídos desde SQL Server
│   ├── processed/                    # Indicadores calculados y datos limpios
│   └── reports/                      # Reporte PDF y Excel generados
│
├── database/
│   ├── schema.sql                    # Definición de tablas T-SQL
│   ├── seed_data.py                  # Población de datos ficticios (Faker)
│   └── reset_data.sql                # Script para limpiar y reiniciar datos
│
├── etl/
│   ├── extract.py                    # Capa E: extracción desde SQL Server
│   ├── transform.py                  # Capa T: limpieza, validación e indicadores
│   └── load.py                       # Capa L: consolidación en Excel formateado
│
├── reports/
│   ├── generate_report.py            # Generación de reporte PDF con gráficos
│   └── send_email.py                 # Envío automático por correo
│
├── logs/                             # Logs de ejecución diarios (auto-generado)
├── main.py                           # Orquestador: ejecuta el pipeline completo
├── config.py                         # Configuración global (excluido de Git)
├── requirements.txt                  # Dependencias del proyecto
└── README.md
```

---

## 📊 Indicadores de Gestión Generados

El pipeline calcula y reporta los siguientes indicadores en cada ejecución:

- **Tasa de ocupación de camas** por servicio (con referencia OMS 85%)
- **Promedio de días de estadía** por servicio y por categoría diagnóstica
- **Evolución mensual de egresos** hospitalarios por motivo y servicio
- **Atenciones ambulatorias** por tipo y especialidad médica
- **Perfil de pacientes** hospitalizados por previsión, sexo y grupo etario

---

## ⚙️ Instalación y Configuración

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu_usuario/hospital_etl_project.git
cd hospital_etl_project
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar credenciales

Copia la plantilla de configuración y completa los valores:

```bash
cp config_template.py config.py
```

Edita `config.py` con tu instancia de SQL Server y credenciales de correo:

```python
DB_SERVER  = r".\SQLEXPRESS"      # Tu instancia SQL Server
DB_NAME    = "hospital_db"

EMAIL_SENDER     = "tu_correo@gmail.com"
EMAIL_PASSWORD   = "tu_app_password"    # Contraseña de aplicación Gmail
EMAIL_RECIPIENTS = ["destinatario@correo.com"]
```

### 4. Crear la base de datos

Ejecuta el schema en SSMS contra tu instancia SQL Server:

```sql
-- Ejecutar en SSMS:
-- database/schema.sql
```

### 5. Poblar con datos ficticios

```bash
python database/seed_data.py
```

### 6. Ejecutar el pipeline completo

```bash
python main.py
```

---

## 🔁 Automatización con Task Scheduler

Para ejecutar el pipeline automáticamente cada día configura una tarea en el Programador de tareas de Windows con los siguientes parámetros:

```
Programa:    C:\ruta\a\python.exe
Argumentos:  main.py
Iniciar en:  C:\ruta\al\proyecto\hospital_etl_project
Frecuencia:  Diaria — 07:00 AM
```

Cada ejecución genera un log en `logs/pipeline_YYYYMMDD.log` con el detalle completo del proceso.

---

## 📦 Dependencias

```
sqlalchemy
pyodbc
pandas
faker
openpyxl
matplotlib
seaborn
reportlab
```

Instalar con:

```bash
pip install -r requirements.txt
```

---

## 🗃️ Modelo de Datos

El schema replica la estructura simplificada de una Ficha Clínica Electrónica (FCE) hospitalaria:

```
pacientes ──┐
            ├──→ hospitalizaciones ←── camas
diagnosticos┤
            └──→ atenciones_ambulatorias
```

| Tabla | Descripción |
|---|---|
| `pacientes` | Datos demográficos y previsión |
| `camas` | Inventario de camas por servicio y tipo |
| `diagnosticos` | Catálogo CIE-10 simplificado (16 diagnósticos) |
| `hospitalizaciones` | Ingresos, egresos y estadías |
| `atenciones_ambulatorias` | Consultas, controles, urgencias y procedimientos |

---

## 📄 Licencia

Proyecto personal de práctica. Los datos generados son completamente ficticios mediante la librería Faker y no corresponden a pacientes reales.
