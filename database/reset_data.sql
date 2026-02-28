-- Resetear datos manteniendo estructura y catálogos
DELETE FROM dbo.atenciones_ambulatorias;
DELETE FROM dbo.hospitalizaciones;

-- Si también quieres resetear camas y pacientes
DELETE FROM dbo.camas;
DELETE FROM dbo.pacientes;

-- Reiniciar contadores IDENTITY
DBCC CHECKIDENT ('dbo.atenciones_ambulatorias', RESEED, 0);
DBCC CHECKIDENT ('dbo.hospitalizaciones', RESEED, 0);
DBCC CHECKIDENT ('dbo.camas', RESEED, 0);
DBCC CHECKIDENT ('dbo.pacientes', RESEED, 0);