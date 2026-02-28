# =============================================
# SEED_DATA.PY - Población de datos ficticios
# Proyecto: Pipeline de Estadísticas Hospitalarias
# =============================================

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
from datetime import datetime, timedelta
from faker import Faker
from faker.providers import person, address
from sqlalchemy import create_engine, text
from config import CONNECTION_STRING

# ---------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------
fake = Faker("es_CL")   # Locale chileno: RUTs, nombres y comunas locales
random.seed(42)          # Semilla fija para reproducibilidad

N_PACIENTES    = 3000
N_CAMAS        = 600
N_HOSPITALIZACIONES  = 5000
N_ATENCIONES         = 12000
FECHA_INICIO   = datetime.now() - timedelta(days=365)  # Último año


# ---------------------------------------------
# CATÁLOGO CIE-10 SIMPLIFICADO
# ---------------------------------------------
DIAGNOSTICOS = [
    ("J18.9", "Neumonía, no especificada",                      "Respiratorio"),
    ("J06.9", "Infección aguda vías respiratorias superiores",  "Respiratorio"),
    ("J44.1", "EPOC con exacerbación aguda",                    "Respiratorio"),
    ("I21.9", "Infarto agudo al miocardio, no especificado",    "Cardiovascular"),
    ("I10.X", "Hipertensión esencial primaria",                 "Cardiovascular"),
    ("I50.9", "Insuficiencia cardíaca, no especificada",        "Cardiovascular"),
    ("E11.9", "Diabetes mellitus tipo 2 sin complicaciones",    "Metabólico"),
    ("E86.0", "Deshidratación",                                 "Metabólico"),
    ("K35.9", "Apendicitis aguda, no especificada",             "Digestivo"),
    ("K92.1", "Melena",                                         "Digestivo"),
    ("N39.0", "Infección urinaria, sitio no especificado",      "Urológico"),
    ("S72.0", "Fractura de cuello de fémur",                    "Traumatológico"),
    ("S06.9", "Traumatismo intracraneal, no especificado",      "Neurológico"),
    ("G40.9", "Epilepsia, no especificada",                     "Neurológico"),
    ("A09.9", "Gastroenteritis infecciosa",                     "Infectológico"),
    ("B34.9", "Infección viral, no especificada",               "Infectológico"),
]

SERVICIOS = ["UCI", "Medicina Interna", "Cirugía", "Traumatología", "Neurología", "Cardiología"]
TIPOS_CAMA = ["Básica", "Media", "Alta Complejidad"]
PREVISIONES = ["FONASA", "ISAPRE", "NINGUNA"]
MOTIVOS_EGRESO = ["Alta médica", "Traslado", "Fallecimiento", "Alta voluntaria"]
TIPOS_ATENCION = ["Consulta", "Control", "Urgencia", "Procedimiento"]
ESPECIALIDADES = ["Medicina General", "Cardiología", "Neurología", "Traumatología",
                  "Cirugía", "Urología", "Gastroenterología", "Endocrinología"]


# ---------------------------------------------
# HELPERS
# ---------------------------------------------
def random_date(start: datetime, end: datetime) -> datetime:
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))

def generar_rut() -> str:
    """Genera un RUT chileno ficticio con formato XX.XXX.XXX-X"""
    numero = random.randint(5_000_000, 25_000_000)
    digits = [int(d) for d in str(numero)]
    factor = [2, 3, 4, 5, 6, 7]
    total = sum(d * factor[i % 6] for i, d in enumerate(reversed(digits)))
    resto = 11 - (total % 11)
    dv = "0" if resto == 11 else ("K" if resto == 10 else str(resto))
    num_fmt = f"{numero:,}".replace(",", ".")
    return f"{num_fmt}-{dv}"


# ---------------------------------------------
# FUNCIONES DE INSERCIÓN
# ---------------------------------------------
def insertar_diagnosticos(conn):
    print("  → Insertando diagnósticos CIE-10...")
    for codigo, descripcion, categoria in DIAGNOSTICOS:
        conn.execute(text("""
            IF NOT EXISTS (SELECT 1 FROM dbo.diagnosticos WHERE codigo_cie10 = :codigo)
            INSERT INTO dbo.diagnosticos (codigo_cie10, descripcion, categoria)
            VALUES (:codigo, :descripcion, :categoria)
        """), {"codigo": codigo, "descripcion": descripcion, "categoria": categoria})
    print(f"     {len(DIAGNOSTICOS)} diagnósticos insertados.")


def insertar_camas(conn):
    print("  → Insertando camas...")
    for i in range(1, N_CAMAS + 1):
        servicio = random.choice(SERVICIOS)
        tipo     = random.choice(TIPOS_CAMA)
        numero   = f"{servicio[:3].upper()}-{i:03d}"
        conn.execute(text("""
            IF NOT EXISTS (SELECT 1 FROM dbo.camas WHERE numero_cama = :numero)
            INSERT INTO dbo.camas (numero_cama, servicio, tipo, estado)
            VALUES (:numero, :servicio, :tipo, 'Disponible')
        """), {"numero": numero, "servicio": servicio, "tipo": tipo})
    print(f"     {N_CAMAS} camas insertadas.")


def insertar_pacientes(conn):
    print("  → Insertando pacientes...")
    for _ in range(N_PACIENTES):
        sexo     = random.choice(["M", "F"])
        nombre   = fake.first_name_male() if sexo == "M" else fake.first_name_female()
        apellido = fake.last_name()
        rut      = generar_rut()
        fnac     = random_date(datetime(1940, 1, 1), datetime(2005, 12, 31)).date()
        comuna   = fake.city()
        prevision = random.choice(PREVISIONES)

        # Si el RUT ya existe (colisión), simplemente se omite
        conn.execute(text("""
            IF NOT EXISTS (SELECT 1 FROM dbo.pacientes WHERE rut = :rut)
            INSERT INTO dbo.pacientes (rut, nombre, apellido, fecha_nacimiento, sexo, comuna, prevision)
            VALUES (:rut, :nombre, :apellido, :fnac, :sexo, :comuna, :prevision)
        """), {"rut": rut, "nombre": nombre, "apellido": apellido,
               "fnac": fnac, "sexo": sexo, "comuna": comuna, "prevision": prevision})
    print(f"     ~{N_PACIENTES} pacientes insertados.")


def insertar_hospitalizaciones(conn):
    print("  → Insertando hospitalizaciones...")

    paciente_ids    = [row[0] for row in conn.execute(text("SELECT paciente_id FROM dbo.pacientes"))]
    cama_ids        = [row[0] for row in conn.execute(text("SELECT cama_id FROM dbo.camas"))]
    diagnostico_ids = [row[0] for row in conn.execute(text("SELECT diagnostico_id FROM dbo.diagnosticos"))]
    medicos         = [fake.name() for _ in range(20)]  # Pool de médicos ficticios

    for _ in range(N_HOSPITALIZACIONES):
        ingreso = random_date(FECHA_INICIO, datetime.now() - timedelta(days=2))
        # 85% de los casos tienen egreso; 15% siguen hospitalizados
        tiene_egreso = random.random() < 0.85
        egreso  = ingreso + timedelta(days=random.randint(1, 20)) if tiene_egreso else None
        motivo  = random.choice(MOTIVOS_EGRESO) if tiene_egreso else None

        conn.execute(text("""
            INSERT INTO dbo.hospitalizaciones
                (paciente_id, cama_id, diagnostico_id, fecha_ingreso, fecha_egreso, motivo_egreso, medico_responsable)
            VALUES
                (:pid, :cid, :did, :ingreso, :egreso, :motivo, :medico)
        """), {
            "pid":    random.choice(paciente_ids),
            "cid":    random.choice(cama_ids),
            "did":    random.choice(diagnostico_ids),
            "ingreso": ingreso,
            "egreso":  egreso,
            "motivo":  motivo,
            "medico":  random.choice(medicos)
        })
    print(f"     {N_HOSPITALIZACIONES} hospitalizaciones insertadas.")


def insertar_atenciones(conn):
    print("  → Insertando atenciones ambulatorias...")

    paciente_ids    = [row[0] for row in conn.execute(text("SELECT paciente_id FROM dbo.pacientes"))]
    diagnostico_ids = [row[0] for row in conn.execute(text("SELECT diagnostico_id FROM dbo.diagnosticos"))]
    medicos         = [fake.name() for _ in range(20)]

    for _ in range(N_ATENCIONES):
        fecha = random_date(FECHA_INICIO, datetime.now())
        conn.execute(text("""
            INSERT INTO dbo.atenciones_ambulatorias
                (paciente_id, diagnostico_id, fecha_atencion, tipo_atencion, especialidad, medico_responsable)
            VALUES
                (:pid, :did, :fecha, :tipo, :especialidad, :medico)
        """), {
            "pid":         random.choice(paciente_ids),
            "did":         random.choice(diagnostico_ids),
            "fecha":       fecha,
            "tipo":        random.choice(TIPOS_ATENCION),
            "especialidad": random.choice(ESPECIALIDADES),
            "medico":      random.choice(medicos)
        })
    print(f"     {N_ATENCIONES} atenciones ambulatorias insertadas.")


# ---------------------------------------------
# MAIN
# ---------------------------------------------
def main():
    print("=" * 50)
    print("  SEED DATA - hospital_db")
    print("=" * 50)

    engine = create_engine(CONNECTION_STRING, fast_executemany=True)

    with engine.begin() as conn:   # begin() hace commit automático al salir sin errores
        insertar_diagnosticos(conn)
        insertar_camas(conn)
        insertar_pacientes(conn)
        insertar_hospitalizaciones(conn)
        insertar_atenciones(conn)

    print("=" * 50)
    print("  ✓ Base de datos poblada exitosamente.")
    print("=" * 50)


if __name__ == "__main__":
    main()