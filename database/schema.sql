-- =============================================
-- HOSPITAL_DB - SCHEMA T-SQL
-- Proyecto: Pipeline de Estadísticas Hospitalarias
-- =============================================

USE hospital_db;
GO

-- ---------------------------------------------
-- TABLA: pacientes
-- ---------------------------------------------
CREATE TABLE dbo.pacientes (
    paciente_id     INT IDENTITY(1,1) PRIMARY KEY,
    rut             VARCHAR(12)     NOT NULL UNIQUE,
    nombre          VARCHAR(100)    NOT NULL,
    apellido        VARCHAR(100)    NOT NULL,
    fecha_nacimiento DATE           NOT NULL,
    sexo            CHAR(1)         NOT NULL CHECK (sexo IN ('M', 'F')),
    comuna          VARCHAR(100),
    prevision       VARCHAR(50)     CHECK (prevision IN ('FONASA', 'ISAPRE', 'NINGUNA')),
    fecha_registro  DATETIME2       NOT NULL DEFAULT GETDATE()
);
GO

-- ---------------------------------------------
-- TABLA: camas
-- ---------------------------------------------
CREATE TABLE dbo.camas (
    cama_id         INT IDENTITY(1,1) PRIMARY KEY,
    numero_cama     VARCHAR(10)     NOT NULL UNIQUE,
    servicio        VARCHAR(100)    NOT NULL,  -- Ej: 'UCI', 'Medicina', 'Cirugía'
    tipo            VARCHAR(50)     NOT NULL CHECK (tipo IN ('Básica', 'Media', 'Alta Complejidad')),
    estado          VARCHAR(20)     NOT NULL DEFAULT 'Disponible' CHECK (estado IN ('Disponible', 'Ocupada', 'En mantención'))
);
GO

-- ---------------------------------------------
-- TABLA: diagnosticos
-- Catálogo simplificado CIE-10
-- ---------------------------------------------
CREATE TABLE dbo.diagnosticos (
    diagnostico_id  INT IDENTITY(1,1) PRIMARY KEY,
    codigo_cie10    VARCHAR(10)     NOT NULL UNIQUE,
    descripcion     VARCHAR(200)    NOT NULL,
    categoria       VARCHAR(100)    NOT NULL  -- Ej: 'Respiratorio', 'Cardiovascular'
);
GO

-- ---------------------------------------------
-- TABLA: hospitalizaciones
-- ---------------------------------------------
CREATE TABLE dbo.hospitalizaciones (
    hospitalizacion_id  INT IDENTITY(1,1) PRIMARY KEY,
    paciente_id         INT             NOT NULL,
    cama_id             INT             NOT NULL,
    diagnostico_id      INT             NOT NULL,
    fecha_ingreso       DATETIME2       NOT NULL,
    fecha_egreso        DATETIME2,                  -- NULL si aún hospitalizado
    motivo_egreso       VARCHAR(50)     CHECK (motivo_egreso IN ('Alta médica', 'Traslado', 'Fallecimiento', 'Alta voluntaria')),
    medico_responsable  VARCHAR(150),
    created_at          DATETIME2       NOT NULL DEFAULT GETDATE(),

    CONSTRAINT FK_hosp_paciente     FOREIGN KEY (paciente_id)    REFERENCES dbo.pacientes(paciente_id),
    CONSTRAINT FK_hosp_cama         FOREIGN KEY (cama_id)        REFERENCES dbo.camas(cama_id),
    CONSTRAINT FK_hosp_diagnostico  FOREIGN KEY (diagnostico_id) REFERENCES dbo.diagnosticos(diagnostico_id)
);
GO

-- ---------------------------------------------
-- TABLA: atenciones_ambulatorias
-- ---------------------------------------------
CREATE TABLE dbo.atenciones_ambulatorias (
    atencion_id         INT IDENTITY(1,1) PRIMARY KEY,
    paciente_id         INT             NOT NULL,
    diagnostico_id      INT             NOT NULL,
    fecha_atencion      DATETIME2       NOT NULL,
    tipo_atencion       VARCHAR(50)     NOT NULL CHECK (tipo_atencion IN ('Consulta', 'Control', 'Urgencia', 'Procedimiento')),
    especialidad        VARCHAR(100),
    medico_responsable  VARCHAR(150),
    created_at          DATETIME2       NOT NULL DEFAULT GETDATE(),

    CONSTRAINT FK_amb_paciente      FOREIGN KEY (paciente_id)    REFERENCES dbo.pacientes(paciente_id),
    CONSTRAINT FK_amb_diagnostico   FOREIGN KEY (diagnostico_id) REFERENCES dbo.diagnosticos(diagnostico_id)
);
GO

-- ---------------------------------------------
-- ÍNDICES para mejorar performance en queries ETL
-- ---------------------------------------------
CREATE INDEX IX_hosp_fecha_ingreso   ON dbo.hospitalizaciones(fecha_ingreso);
CREATE INDEX IX_hosp_fecha_egreso    ON dbo.hospitalizaciones(fecha_egreso);
CREATE INDEX IX_amb_fecha_atencion   ON dbo.atenciones_ambulatorias(fecha_atencion);
CREATE INDEX IX_amb_tipo             ON dbo.atenciones_ambulatorias(tipo_atencion);
GO