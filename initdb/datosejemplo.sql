-- Insertar etapas del proceso de reclutamiento
INSERT INTO etapas (id_etapa, nom_etapa, desc_etapa) VALUES
(1, 'Postulación', 'El candidato aplica a la vacante'),
(2, 'Revisión Inicial', 'Validación básica del perfil'),
(3, 'Entrevista Telefónica', 'Primer contacto por teléfono'),
(4, 'Entrevista Técnica', 'Evaluación de habilidades técnicas'),
(5, 'Entrevista Final', 'Última entrevista con gerente o RRHH'),
(6, 'Oferta', 'Se emite una oferta al candidato'),
(7, 'Contratado', 'El candidato acepta la oferta'),
(8, 'Rechazado', 'El candidato sale del proceso');

-- Insertar fuentes de reclutamiento
INSERT INTO fuentes (id_fuente, nom_fuente, desc_fuente) VALUES
(1, 'Prueba', NULL),
(2, 'LinkedIn', 'Fuente profesional de empleo'),
(3, 'Indeed', 'Plataforma de búsqueda de empleo'),
(4, 'Facebook', 'Red social'),
(5, 'Twitter', 'Red social'),
(6, 'Amigos/Familia', 'Recomendación personal'),
(7, 'Bolsa de Trabajo Escolar', 'Fuente escolar o universitaria'),
(8, 'Portal Web', 'Nuestra página web'),
(9, 'Otro', 'Otra fuente no especificada');

-- Insertar estados de ofertas
INSERT INTO estados_ofertas (id_estadoferta, nom_estado, desc_estado) VALUES
(1, 'Emitida', NULL),
(2, 'Aceptada', NULL),
(3, 'Rechazada', NULL);

-- Insertar estados de entrevistas
INSERT INTO estados_entrevistas (id_estadoentrevista, nom_estado, desc_estado) VALUES
(1, 'Programada', NULL),
(2, 'En Progreso', 'Entrevista en curso'),
(3, 'Evaluada', 'Entrevista evaluada con feedback'),
(4, 'Cancelada', 'Entrevista cancelada'),
(5, 'Reprogramada', 'Entrevista reprogramada para otra fecha');

-- Insertar roles del sistema
INSERT INTO roles_sistema (id_rolsistema, nom_rol, desc_rol) VALUES
(1, 'Admin', NULL),
(2, 'Reclutador', NULL),
(3, 'Entrevistador', NULL),
(9, 'Recruiter', 'Acceso a vacantes, candidatos y reportes'),
(10, 'Hiring Manager', 'Acceso a vacantes y candidatos de su departamento'),
(11, 'Auditor', 'Acceso solo a vistas de control y reportes');

-- Insertar roles de entrevistadores
INSERT INTO roles (id_rol, nom_rol, desc_rol) VALUES
(2, 'Entrevistador Senior', 'Entrevistador con más experiencia y responsabilidades'),
(3, 'Entrevistador Junior', 'Entrevistador con menos experiencia, bajo supervisión');

INSERT INTO roles (id_rol, nom_rol, desc_rol) VALUES
(1, 'Entrevistador', 'Entrevistador principal');

-- Insertar entrevistadores
INSERT INTO entrevistadores (id_entrevistador, nom_entrevistador, id_rol, telefono, email) VALUES
(1, 'Juan Pérez', 1, '555-1234', 'juan.perez@example.com'),
(2, 'María García', 1, '555-5678', 'maria.garcia@example.com'),
(3, 'Carlos López', 2, '555-9012', 'carlos.lopez@example.com');

-- Insertar usuarios
INSERT INTO usuarios (id_usuario, username, hashed_pass, email, id_rolsistema, id_entrevistador, activo, creado_en) VALUES
(1, 'admin', 'hashed_pass_example_1', 'admin@example.com', 1, NULL, 1, NOW()),
(2, 'reclutador', 'hashed_pass_example_2', 'reclutador@example.com', 2, NULL, 1, NOW()),
(3, 'entrevistador', 'hashed_pass_example_3', 'entrevistador@example.com', 3, 1, 1, NOW()),
(4, 'recruiter', 'hashed_pass_example_4', 'recruiter@example.com', 9, NULL, 1, NOW()),
(5, 'hiring_manager', 'hashed_pass_example_5', 'hiring_manager@example.com', 10, NULL, 1, NOW()),
(6, 'auditor', 'hashed_pass_example_6', 'auditor@example.com', 11, NULL, 1, NOW()),
(7, 'usuario7', 'hashed_pass_example_7', 'usuario7@example.com', 2, NULL, 1, NOW()),
(8, 'usuario8', 'hashed_pass_example_8', 'usuario8@example.com', 9, NULL, 1, NOW()),
(9, 'usuario9', 'hashed_pass_example_9', 'usuario9@example.com', 2, NULL, 1, NOW()),
(10, 'usuario10', 'hashed_pass_example_10', 'usuario10@example.com', 3, 2, 1, NOW());

-- Insertar departamentos
INSERT INTO departamentos (id_departamento, nom_departamento) VALUES
(1, 'Recursos Humanos'),
(2, 'Tecnología'),
(3, 'Ventas'),
(4, 'Marketing'),
(5, 'Finanzas'),
(6, 'Operaciones'),
(7, 'Legal'),
(8, 'Soporte Técnico'),
(9, 'Desarrollo'),
(10, 'Administración');

-- Insertar estados de vacantes
INSERT INTO estados_vacantes (id_estadovacante, nom_estado, desc_estado) VALUES 
(1, 'Abierta', 'Vacante activa y recibiendo postulaciones'),
(2, 'Cerrada', 'Vacante cerrada, no recibe más postulaciones'),
(3, 'En Pausa', 'Vacante temporalmente pausada'),
(4, 'Cancelada', 'Vacante cancelada');

-- Insertar vacantes iniciales
INSERT INTO vacantes (id_vacante, titulo_vacante, desc_vacante, id_departamento, fecha_creacion, id_estadovacante, time_to_fill) VALUES
(1, 'Desarrollador Frontend Senior', 'Desarrollador con experiencia en React y TypeScript', 2, '2024-01-15', 1, NULL),
(2, 'Gerente de Ventas', 'Responsable del equipo comercial norte', 3, '2024-01-20', 1, NULL),
(3, 'Diseñador UX/UI', 'Diseñador de experiencias de usuario', 4, '2024-02-01', 1, NULL),
(4, 'Contador Senior', 'Contador con experiencia en impuestos corporativos', 5, '2024-02-10', 2, 45),
(5, 'Soporte Técnico N2', 'Soporte técnico especializado', 8, '2024-02-15', 1, NULL),
(6, 'Abogado Corporativo', 'Especialista en derecho laboral y corporativo', 7, '2024-02-20', 3, NULL),
(7, 'Analista de Marketing Digital', 'Especialista en campañas digitales', 4, '2024-03-01', 1, NULL),
(8, 'DevOps Engineer', 'Ingeniero de infraestructura y despliegues', 2, '2024-03-05', 1, NULL),
(9, 'Asistente Administrativo', 'Apoyo en labores administrativas', 10, '2024-03-10', 2, 30),
(10, 'Scrum Master', 'Facilitador de metodologías ágiles', 9, '2024-03-15', 1, NULL);

-- Insertar candidatos iniciales
INSERT INTO candidatos (id_candidato, identificacion, nom_candidato, email, telefono, fecha_aplicacion, id_fuente) VALUES
(1, 'A123456789', 'Ana Rodríguez Pérez', 'ana.rodriguez@email.com', '555-1001', '2024-03-01', 2),
(2, 'B987654321', 'Carlos Mendoza López', 'carlos.mendoza@email.com', '555-1002', '2024-03-02', 3),
(3, 'C456789123', 'María González Silva', 'maria.gonzalez@email.com', '555-1003', '2024-03-03', 8),
(4, 'D789123456', 'Roberto Jiménez Cruz', 'roberto.jimenez@email.com', '555-1004', '2024-03-04', 6),
(5, 'E321654987', 'Laura Torres Méndez', 'laura.torres@email.com', '555-1005', '2024-03-05', 2),
(6, 'F654987321', 'Diego Herrera Ruiz', 'diego.herrera@email.com', '555-1006', '2024-03-06', 3),
(7, 'G147258369', 'Sofia Castro Díaz', 'sofia.castro@email.com', '555-1007', '2024-03-07', 4),
(8, 'H258369147', 'Javier Morales Vega', 'javier.morales@email.com', '555-1008', '2024-03-08', 8),
(9, 'I369147258', 'Elena Navarro Ortega', 'elena.navarro@email.com', '555-1009', '2024-03-09', 2),
(10, 'J741852963', 'Miguel Ángel Santos', 'miguel.santos@email.com', '555-1010', '2024-03-10', 6);

-- Insertar postulaciones iniciales
INSERT INTO postulaciones (id_postulacion, id_candidato, id_vacante, fecha_postula, id_etapa) VALUES
(1, 1, 1, '2024-03-01', 3),
(2, 2, 1, '2024-03-02', 4),
(3, 3, 2, '2024-03-03', 2),
(4, 4, 3, '2024-03-04', 5),
(5, 5, 4, '2024-03-05', 7),
(6, 6, 5, '2024-03-06', 3),
(7, 7, 6, '2024-03-07', 8),
(8, 8, 7, '2024-03-08', 4),
(9, 9, 8, '2024-03-09', 6),
(10, 10, 9, '2024-03-10', 7);

-- Insertar entrevistas iniciales
INSERT INTO entrevistas (id_entrevista, id_postulacion, fecha_entrevista, puntaje, notas, id_estadoentrevista, id_entrevistador) VALUES
(1, 1, '2024-03-05 10:00:00', 8.5, 'Buen conocimiento en React, necesita mejorar en TypeScript', 3, 1),
(2, 2, '2024-03-06 11:00:00', 9.2, 'Excelente desempeño técnico, muy buen fit cultural', 3, 2),
(3, 4, '2024-03-07 14:00:00', 8.8, 'Portafolio sólido, buena comunicación', 3, 1),
(4, 6, '2024-03-08 09:30:00', 7.5, 'Conocimientos básicos sólidos, necesita experiencia', 3, 3),
(5, 8, '2024-03-09 15:00:00', 8.0, 'Buen manejo de herramientas de analytics', 3, 2),
(6, 1, '2024-03-12 10:00:00', NULL, 'Segunda entrevista técnica programada', 1, 2),
(7, 2, '2024-03-13 11:00:00', NULL, 'Entrevista final con gerente', 1, 1),
(8, 3, '2024-03-10 16:00:00', 7.0, 'Cumple requisitos mínimos', 3, 3),
(9, 9, '2024-03-11 13:00:00', 9.5, 'Excelente conocimiento en CI/CD y cloud', 3, 1),
(10, 6, '2024-03-14 10:30:00', NULL, 'Segunda entrevista con el equipo', 1, 2);

-- Insertar vacantes adicionales
INSERT INTO vacantes (id_vacante, titulo_vacante, desc_vacante, id_departamento, fecha_creacion, id_estadovacante, time_to_fill) VALUES
(11, 'Product Manager', 'Gestión de productos digitales', 3, '2025-11-24', 1, NULL),
(12, 'Desarrollador Backend', 'Desarrollador con experiencia en Java y Spring', 2, '2025-11-24', 1, NULL),
(13, 'Analista de Datos', 'Análisis de grandes volúmenes de datos', 9, '2025-11-24', 1, NULL);

-- Insertar candidatos adicionales
INSERT INTO candidatos (id_candidato, identificacion, nom_candidato, email, telefono, fecha_aplicacion, id_fuente) VALUES
(11, 'K987654321', 'Elena Ramírez Gómez', 'elena.ramirez@email.com', '555-1011', '2025-11-24', 4),
(12, 'L123456789', 'Juan Pérez Sánchez', 'juan.perez@email.com', '555-1012', '2025-11-24', 2),
(13, 'M987654123', 'Carlos Fernández López', 'carlos.fernandez@email.com', '555-1013', '2025-11-24', 7);

-- Insertar postulaciones adicionales
INSERT INTO postulaciones (id_postulacion, id_candidato, id_vacante, fecha_postula, id_etapa) VALUES
(11, 11, 11, '2025-11-24', 3),
(12, 12, 12, '2025-11-24', 4),
(13, 13, 13, '2025-11-24', 2);

-- Insertar entrevistas adicionales
INSERT INTO entrevistas (id_entrevista, id_postulacion, fecha_entrevista, puntaje, notas, id_estadoentrevista, id_entrevistador) VALUES
(11, 11, '2025-11-24 10:00:00', NULL, 'Entrevista técnica programada para Product Manager', 1, 1),
(12, 12, '2025-11-24 11:30:00', NULL, 'Entrevista técnica programada para Backend', 1, 2),
(13, 13, '2025-11-24 14:00:00', NULL, 'Entrevista inicial para Analista de Datos', 1, 3);