-- =======================================
-- Crear base de datos, usuario y privilegios
-- =======================================

CREATE DATABASE IF NOT EXISTS SistemaReclutamiento
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'usuario_recludb'@'%' IDENTIFIED BY '666';
GRANT ALL PRIVILEGES ON SistemaReclutamiento.* TO 'usuario_recludb'@'%';
FLUSH PRIVILEGES;

USE SistemaReclutamiento;

-- ==========================
-- Tablas catálogos base
-- ==========================

CREATE TABLE fuentes (
  id_fuente BIGINT PRIMARY KEY AUTO_INCREMENT,
  nom_fuente VARCHAR(80) NOT NULL,
  desc_fuente VARCHAR(255)
);

CREATE TABLE roles (
  id_rol BIGINT PRIMARY KEY AUTO_INCREMENT,
  nom_rol VARCHAR(50) NOT NULL UNIQUE,
  desc_rol VARCHAR(255)
);

CREATE TABLE roles_sistema (
  id_rolsistema BIGINT PRIMARY KEY AUTO_INCREMENT,
  nom_rol VARCHAR(50) NOT NULL UNIQUE,
  desc_rol VARCHAR(255)
);

CREATE TABLE departamentos (
  id_departamento BIGINT PRIMARY KEY AUTO_INCREMENT,
  nom_departamento VARCHAR(80) NOT NULL
);

CREATE TABLE estados_vacantes (
  id_estadovacante BIGINT PRIMARY KEY AUTO_INCREMENT,
  nom_estado VARCHAR(50) NOT NULL UNIQUE,
  desc_estado VARCHAR(255)
);

CREATE TABLE estados_ofertas (
  id_estadoferta BIGINT PRIMARY KEY AUTO_INCREMENT,
  nom_estado VARCHAR(50) NOT NULL UNIQUE,
  desc_estado VARCHAR(255)
);

CREATE TABLE estados_entrevistas (
  id_estadoentrevista BIGINT PRIMARY KEY AUTO_INCREMENT,
  nom_estado VARCHAR(50) NOT NULL UNIQUE,
  desc_estado VARCHAR(255)
);

CREATE TABLE etapas (
  id_etapa BIGINT PRIMARY KEY AUTO_INCREMENT,
  nom_etapa VARCHAR(50) NOT NULL UNIQUE,
  desc_etapa VARCHAR(255)
);

-- ==========================
-- Entidades principales
-- ==========================

CREATE TABLE candidatos (
  id_candidato BIGINT PRIMARY KEY AUTO_INCREMENT,
  identificacion VARCHAR(20) NOT NULL UNIQUE,
  nom_candidato VARCHAR(120) NOT NULL,
  email VARCHAR(120) NOT NULL UNIQUE,
  telefono VARCHAR(15),
  fecha_aplicacion DATE NOT NULL,
  id_fuente BIGINT,
  FOREIGN KEY (id_fuente) REFERENCES fuentes(id_fuente)
);

-- Primero entrevistadores (porque usuarios depende de ellos)
CREATE TABLE entrevistadores (
  id_entrevistador BIGINT PRIMARY KEY AUTO_INCREMENT,
  nom_entrevistador VARCHAR(120) NOT NULL,
  id_rol BIGINT NOT NULL,
  telefono VARCHAR(15),
  email VARCHAR(120) NOT NULL UNIQUE,
  FOREIGN KEY (id_rol) REFERENCES roles(id_rol)
);

-- ================================
-- Tabla de usuarios del sistema
-- ================================
CREATE TABLE usuarios (
  id_usuario BIGINT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(80) NOT NULL UNIQUE,
  hashed_pass VARCHAR(255) NOT NULL,
  email VARCHAR(120) NOT NULL UNIQUE,
  id_rolsistema BIGINT NOT NULL,
  id_entrevistador BIGINT,
  activo TINYINT DEFAULT 1,
  creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (id_rolsistema) REFERENCES roles_sistema(id_rolsistema),
  FOREIGN KEY (id_entrevistador) REFERENCES entrevistadores(id_entrevistador)
);

CREATE TABLE vacantes (
  id_vacante BIGINT PRIMARY KEY AUTO_INCREMENT,
  titulo_vacante VARCHAR(150) NOT NULL,
  desc_vacante TEXT,
  id_departamento BIGINT,
  fecha_creacion DATE NOT NULL,
  id_estadovacante BIGINT,
  FOREIGN KEY (id_departamento) REFERENCES departamentos(id_departamento),
  FOREIGN KEY (id_estadovacante) REFERENCES estados_vacantes(id_estadovacante),
  UNIQUE KEY uk_vacante_departamento (titulo_vacante, id_departamento)
);

CREATE TABLE postulaciones (
  id_postulacion BIGINT PRIMARY KEY AUTO_INCREMENT,
  id_candidato BIGINT NOT NULL,
  id_vacante BIGINT NOT NULL,
  fecha_postula DATE NOT NULL,
  id_etapa BIGINT NOT NULL,
  FOREIGN KEY (id_candidato) REFERENCES candidatos(id_candidato),
  FOREIGN KEY (id_vacante) REFERENCES vacantes(id_vacante),
  FOREIGN KEY (id_etapa) REFERENCES etapas(id_etapa),
  UNIQUE KEY uq_postulacion (id_candidato, id_vacante)
);

CREATE TABLE entrevistas (
  id_entrevista BIGINT PRIMARY KEY AUTO_INCREMENT,
  id_postulacion BIGINT NOT NULL,
  fecha_entrevista DATE NOT NULL,
  puntaje DECIMAL(4,1) NULL,
  notas TEXT,
  id_estadoentrevista BIGINT,
  id_entrevistador BIGINT,
  FOREIGN KEY (id_postulacion) REFERENCES postulaciones(id_postulacion),
  FOREIGN KEY (id_estadoentrevista) REFERENCES estados_entrevistas(id_estadoentrevista),
  FOREIGN KEY (id_entrevistador) REFERENCES entrevistadores(id_entrevistador),
  UNIQUE KEY uq_entrevista (id_postulacion, fecha_entrevista)
);

CREATE TABLE ofertas (
  id_oferta BIGINT PRIMARY KEY AUTO_INCREMENT,
  id_postulacion BIGINT NOT NULL,
  monto_oferta DECIMAL(12,2) NOT NULL,
  id_estadoferta BIGINT NOT NULL,
  fecha_decision DATE,
  FOREIGN KEY (id_postulacion) REFERENCES postulaciones(id_postulacion),
  FOREIGN KEY (id_estadoferta) REFERENCES estados_ofertas(id_estadoferta),
  UNIQUE KEY uq_oferta_postulacion (id_postulacion)
);

-- ==========================
-- Auditoría
-- ==========================

CREATE TABLE audit_candidatos (
  id_audit BIGINT PRIMARY KEY AUTO_INCREMENT,
  id_candidato BIGINT,
  op CHAR(1),
  changed_by VARCHAR(120),
  changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  payload JSON
);

CREATE TABLE audit_vacantes (
  id_audit BIGINT PRIMARY KEY AUTO_INCREMENT,
  id_vacante BIGINT,
  op CHAR(1),
  changed_by VARCHAR(120),
  changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  payload JSON
);

CREATE TABLE audit_postulaciones (
  id_audit BIGINT PRIMARY KEY AUTO_INCREMENT,
  id_postulacion BIGINT,
  op CHAR(1),
  changed_by VARCHAR(120),
  changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  payload JSON
);

CREATE TABLE audit_entrevistas (
  id_audit BIGINT PRIMARY KEY AUTO_INCREMENT,
  id_entrevista BIGINT,
  op CHAR(1),
  changed_by VARCHAR(120),
  changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  payload JSON
);

CREATE TABLE audit_ofertas (
  id_audit BIGINT PRIMARY KEY AUTO_INCREMENT,
  id_oferta BIGINT,
  op CHAR(1),
  changed_by VARCHAR(120),
  changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  payload JSON
);


-- Stored Procedures
-- 1) vacante Crear Actualizar  ABM de vacantes:



DELIMITER $$

CREATE PROCEDURE svacanteCrearActualizar(
  IN p_id_vacante       BIGINT,
  IN p_titulo_vacante   VARCHAR(150),
  IN p_desc_vacante     TEXT,
  IN p_id_departamento  BIGINT,
  IN p_id_estadovacante BIGINT
)
BEGIN
  IF p_id_vacante IS NULL OR p_id_vacante = 0 THEN
    -- Alta de vacante
    INSERT INTO vacantes(
      titulo_vacante,
      desc_vacante,
      id_departamento,
      fecha_creacion,
      id_estadovacante
    )
    VALUES(
      p_titulo_vacante,
      p_desc_vacante,
      p_id_departamento,
      CURRENT_DATE,
      p_id_estadovacante
    );
  ELSE
    -- Actualización de vacante
    UPDATE vacantes
    SET titulo_vacante   = p_titulo_vacante,
        desc_vacante     = p_desc_vacante,
        id_departamento  = p_id_departamento,
        id_estadovacante = p_id_estadovacante
    WHERE id_vacante = p_id_vacante;
  END IF;
END $$
DELIMITER ;

-- 2) candidatoCrearActualizar  ABM + deduplicación por email:



DELIMITER $$

CREATE PROCEDURE candidatoCrearActualizar(
  IN p_id_candidato   BIGINT,
  IN p_identificacion VARCHAR(20),
  IN p_nom_candidato  VARCHAR(120),
  IN p_email          VARCHAR(120),
  IN p_telefono       VARCHAR(15),
  IN p_id_fuente      BIGINT
)
BEGIN
  -- Validación básica de email
  IF p_email IS NULL OR p_email = '' THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Email del candidato requerido';
  END IF;

  IF p_id_candidato IS NULL OR p_id_candidato = 0 THEN
    -- Alta de candidato
    IF EXISTS (SELECT 1 FROM candidatos WHERE email = p_email) THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Ya existe un candidato con ese email';
    END IF;

    INSERT INTO candidatos(
      identificacion,
      nom_candidato,
      email,
      telefono,
      fecha_aplicacion,
      id_fuente
    )
    VALUES(
      p_identificacion,
      p_nom_candidato,
      p_email,
      p_telefono,
      CURRENT_DATE,
      p_id_fuente
    );
  ELSE
    -- Actualización de candidato
    IF EXISTS (
      SELECT 1
      FROM candidatos
      WHERE email = p_email
        AND id_candidato <> p_id_candidato
    ) THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Otro candidato ya usa ese email';
    END IF;

    UPDATE candidatos
    SET identificacion = p_identificacion,
        nom_candidato  = p_nom_candidato,
        email          = p_email,
        telefono       = p_telefono,
        id_fuente      = p_id_fuente
    WHERE id_candidato = p_id_candidato;
  END IF;
END $$
DELIMITER ;

-- 3) postular  crea postulación si no existe:



DELIMITER $$

CREATE PROCEDURE postular(
  IN p_id_candidato BIGINT,
  IN p_id_vacante   BIGINT
)
BEGIN
  DECLARE v_id_etapa BIGINT;

  -- Validar que exista el candidato
  IF NOT EXISTS (
    SELECT 1
    FROM candidatos
    WHERE id_candidato = p_id_candidato
  ) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Candidato no encontrado';
  END IF;

  -- Validar que exista la vacante
  IF NOT EXISTS (
    SELECT 1
    FROM vacantes
    WHERE id_vacante = p_id_vacante
  ) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Vacante no encontrada';
  END IF;

  -- Evitar postulación duplicada
  IF EXISTS (
    SELECT 1
    FROM postulaciones
    WHERE id_candidato = p_id_candidato
      AND id_vacante   = p_id_vacante
  ) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Ya existe una postulación para ese candidato y vacante';
  END IF;

  -- Buscar etapa inicial del pipeline
  SELECT id_etapa
  INTO v_id_etapa
  FROM etapas
  WHERE nom_etapa = 'Postulacion'
  LIMIT 1;

  IF v_id_etapa IS NULL THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'No se encontró la etapa inicial';
  END IF;

  -- Insertar la nueva postulación
  INSERT INTO postulaciones(
    id_candidato,
    id_vacante,
    fecha_postula,
    id_etapa
  )
  VALUES(
    p_id_candidato,
    p_id_vacante,
    CURRENT_DATE,
    v_id_etapa
  );
END $$
DELIMITER ;

-- 4) moverEtapa  IF/CASE + transacción:



DELIMITER $$

CREATE PROCEDURE moverEtapa(
  IN p_id_postulacion BIGINT,
  IN p_id_etapa_nueva BIGINT
)
BEGIN
  DECLARE v_id_etapa_actual BIGINT;
  DECLARE v_valida TINYINT DEFAULT 0;

  -- Etapa actual de la postulación
  SELECT id_etapa
  INTO v_id_etapa_actual
  FROM postulaciones
  WHERE id_postulacion = p_id_postulacion;

  IF v_id_etapa_actual IS NULL THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Postulación no encontrada';
  END IF;

  -- Validar que exista la nueva etapa
  IF NOT EXISTS (
    SELECT 1
    FROM etapas
    WHERE id_etapa = p_id_etapa_nueva
  ) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Nueva etapa no encontrada';
  END IF;

  -- Reglas de transición (usa tus IDs actuales: 1..5)
  CASE v_id_etapa_actual
    WHEN 1 THEN
      -- Postulacion -> Entrevista o Rechazado
      IF p_id_etapa_nueva IN (2, 5) THEN
        SET v_valida = 1;
      END IF;
    WHEN 2 THEN
      -- Entrevista -> Oferta o Rechazado
      IF p_id_etapa_nueva IN (3, 5) THEN
        SET v_valida = 1;
      END IF;
    WHEN 3 THEN
      -- Oferta -> Contratado o Rechazado
      IF p_id_etapa_nueva IN (4, 5) THEN
        SET v_valida = 1;
      END IF;
    WHEN 4 THEN
      -- Contratado -> (normalmente ya no debería moverse)
      SET v_valida = 0;
    ELSE
      SET v_valida = 0;
  END CASE;

  IF v_valida = 0 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Transición de etapa no permitida';
  END IF;

  -- Transacción simple para actualizar la etapa
  START TRANSACTION;
    UPDATE postulaciones
    SET id_etapa = p_id_etapa_nueva
    WHERE id_postulacion = p_id_postulacion;
  COMMIT;
END $$
DELIMITER ;

-- 5) programarEntrevista  agenda entrevista:



DELIMITER $$

CREATE PROCEDURE programarEntrevista(
  IN p_id_postulacion   BIGINT,
  IN p_id_entrevistador BIGINT,
  IN p_fecha_entrevista DATE
)
BEGIN
  DECLARE v_id_estado_prog BIGINT;

  -- Validar fecha
  IF p_fecha_entrevista IS NULL THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Fecha de entrevista requerida';
  END IF;

  -- Validar postulación
  IF NOT EXISTS (
    SELECT 1
    FROM postulaciones
    WHERE id_postulacion = p_id_postulacion
  ) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Postulación no encontrada';
  END IF;

  -- Validar entrevistador
  IF NOT EXISTS (
    SELECT 1
    FROM entrevistadores
    WHERE id_entrevistador = p_id_entrevistador
  ) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Entrevistador no encontrado';
  END IF;

  -- Buscar estado "Programada"
  SELECT id_estadoentrevista
  INTO v_id_estado_prog
  FROM estados_entrevistas
  WHERE nom_estado = 'Programada'
  LIMIT 1;

  IF v_id_estado_prog IS NULL THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Estado Programada no configurado';
  END IF;

  -- Evitar entrevista duplicada misma fecha para la misma postulación
  IF EXISTS (
    SELECT 1
    FROM entrevistas
    WHERE id_postulacion   = p_id_postulacion
      AND fecha_entrevista = p_fecha_entrevista
  ) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Ya existe una entrevista para esa fecha';
  END IF;

  -- Insertar entrevista
  INSERT INTO entrevistas(
    id_postulacion,
    fecha_entrevista,
    puntaje,
    notas,
    id_estadoentrevista,
    id_entrevistador
  )
  VALUES (
    p_id_postulacion,
    p_fecha_entrevista,
    NULL,
    NULL,
    v_id_estado_prog,
    p_id_entrevistador
  );
END $$
DELIMITER ;

-- 6) registrarFeedback  evalúa entrevista:



DELIMITER $$

CREATE PROCEDURE registrarFeedback(
  IN p_id_entrevista BIGINT,
  IN p_puntaje       DECIMAL(4,1),
  IN p_notas         TEXT
)
BEGIN
  DECLARE v_id_estado_eval BIGINT;

  IF p_puntaje IS NULL THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Puntaje requerido';
  END IF;

  IF p_puntaje < 0 OR p_puntaje > 100 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Puntaje fuera de rango (0-100)';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM entrevistas
    WHERE id_entrevista = p_id_entrevista
  ) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Entrevista no encontrada';
  END IF;

  SELECT id_estadoentrevista
  INTO v_id_estado_eval
  FROM estados_entrevistas
  WHERE nom_estado = 'Evaluada'
  LIMIT 1;

  UPDATE entrevistas
  SET puntaje             = p_puntaje,
      notas               = p_notas,
      id_estadoentrevista = v_id_estado_eval
  WHERE id_entrevista = p_id_entrevista;
END $$
DELIMITER ;

-- 7) ofertaEmitir  solo si etapa = Oferta:



DELIMITER $$

CREATE PROCEDURE ofertaEmitir(
  IN p_id_postulacion BIGINT,
  IN p_monto_oferta   DECIMAL(12,2)
)
BEGIN
  DECLARE v_nom_etapa      VARCHAR(50);
  DECLARE v_id_estado_emit BIGINT;

  -- Validar monto
  IF p_monto_oferta IS NULL OR p_monto_oferta <= 0 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Monto de oferta invalido';
  END IF;

  -- Obtener etapa actual de la postulacion
  SELECT e.nom_etapa
  INTO v_nom_etapa
  FROM postulaciones p
  INNER JOIN etapas e ON p.id_etapa = e.id_etapa
  WHERE p.id_postulacion = p_id_postulacion;

  IF v_nom_etapa IS NULL THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Postulacion no encontrada';
  END IF;

  -- Solo se permite oferta cuando la etapa es 'Oferta'
  IF v_nom_etapa <> 'Oferta' THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Solo se puede emitir oferta en etapa Oferta';
  END IF;

  -- No permitir 2 ofertas para la misma postulacion
  IF EXISTS (
    SELECT 1
    FROM ofertas
    WHERE id_postulacion = p_id_postulacion
  ) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Ya existe una oferta para esa postulacion';
  END IF;

  -- Estado "Emitida"
  SELECT id_estadoferta
  INTO v_id_estado_emit
  FROM estados_ofertas
  WHERE nom_estado = 'Emitida'
  LIMIT 1;

  -- Crear la oferta
  INSERT INTO ofertas(id_postulacion, monto_oferta, id_estadoferta, fecha_decision)
  VALUES (p_id_postulacion, p_monto_oferta, v_id_estado_emit, NULL);
END $$
DELIMITER ;

-- 8) ofertaDecidir  acepta / rechaza; actualiza etapas:



DELIMITER $$

CREATE PROCEDURE ofertaDecidir(
  IN p_id_oferta BIGINT,
  IN p_decision  VARCHAR(20)
)
BEGIN
  DECLARE v_id_postulacion    BIGINT;
  DECLARE v_id_vacante        BIGINT;
  DECLARE v_nom_estado_actual VARCHAR(50);
  DECLARE v_id_estado_nuevo   BIGINT;
  DECLARE v_decision_up       VARCHAR(20);

  -- Normalizar decisión
  SET v_decision_up = UPPER(TRIM(p_decision));

  -- Datos de la oferta + estado actual
  SELECT o.id_postulacion,
         p.id_vacante,
         eo.nom_estado
  INTO   v_id_postulacion,
         v_id_vacante,
         v_nom_estado_actual
  FROM ofertas o
  INNER JOIN postulaciones p   ON o.id_postulacion = p.id_postulacion
  INNER JOIN estados_ofertas eo ON o.id_estadoferta = eo.id_estadoferta
  WHERE o.id_oferta = p_id_oferta;

  IF v_id_postulacion IS NULL THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Oferta no encontrada';
  END IF;

  -- Solo decidir ofertas emitidas
  IF v_nom_estado_actual <> 'Emitida' THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Solo se pueden decidir ofertas emitidas';
  END IF;

  -- Resolver nuevo estado según decisión
  IF v_decision_up = 'ACEPTADA' THEN
    SELECT id_estadoferta
    INTO v_id_estado_nuevo
    FROM estados_ofertas
    WHERE nom_estado = 'Aceptada'
    LIMIT 1;
  ELSEIF v_decision_up = 'RECHAZADA' THEN
    SELECT id_estadoferta
    INTO v_id_estado_nuevo
    FROM estados_ofertas
    WHERE nom_estado = 'Rechazada'
    LIMIT 1;
  ELSE
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Decisión inválida (use Aceptada / Rechazada)';
  END IF;

  -- Actualizar oferta
  UPDATE ofertas
  SET id_estadoferta = v_id_estado_nuevo,
      fecha_decision = CURRENT_DATE
  WHERE id_oferta = p_id_oferta;

  -- Actualizar etapa de la postulación y, si aplica, la vacante
  IF v_decision_up = 'ACEPTADA' THEN
    UPDATE postulaciones
    SET id_etapa = (
      SELECT id_etapa
      FROM etapas
      WHERE nom_etapa = 'Contratado'
      LIMIT 1
    )
    WHERE id_postulacion = v_id_postulacion;

    UPDATE vacantes
    SET id_estadovacante = (
      SELECT id_estadovacante
      FROM estados_vacantes
      WHERE nom_estado = 'Cerrada'
      LIMIT 1
    )
    WHERE id_vacante = v_id_vacante;

  ELSEIF v_decision_up = 'RECHAZADA' THEN
    UPDATE postulaciones
    SET id_etapa = (
      SELECT id_etapa
      FROM etapas
      WHERE nom_etapa = 'Rechazado'
      LIMIT 1
    )
    WHERE id_postulacion = v_id_postulacion;
  END IF;
END $$
DELIMITER ;

-- 9) funnelVacante(vacante):


DELIMITER $$

CREATE PROCEDURE funnelVacante(
  IN p_id_vacante BIGINT
)
BEGIN
  -- limpiar la tabla temporal si ya existía en esta sesión
  DROP TEMPORARY TABLE IF EXISTS tmpFunnel;

  -- crear tabla temporal para el funnel
  CREATE TEMPORARY TABLE tmpFunnel (
    etapa VARCHAR(50),
    total INT
  );

  -- llenar el funnel: conteo de postulaciones por etapa
  INSERT INTO tmpFunnel(etapa, total)
  SELECT e.nom_etapa AS etapa,
         COUNT(*)    AS total
  FROM postulaciones p
  INNER JOIN etapas e ON p.id_etapa = e.id_etapa
  WHERE p.id_vacante = p_id_vacante
  GROUP BY e.nom_etapa
  ORDER BY e.nom_etapa;

  -- resultado que va a ver Flask / MariaDB
  SELECT * FROM tmpFunnel;
END $$
DELIMITER ;

-- 10) tiempoPorEtapa(desde, hasta): promedios en días

DELIMITER $$

CREATE PROCEDURE tiempoPorEtapa(
  IN p_desde DATE,
  IN p_hasta DATE
)
BEGIN
  DROP TEMPORARY TABLE IF EXISTS tmpTiempoEtapa;

  CREATE TEMPORARY TABLE tmpTiempoEtapa (
    etapa        VARCHAR(50),
    dias_promedio DECIMAL(10,2)
  );

  INSERT INTO tmpTiempoEtapa(etapa, dias_promedio)
  SELECT e.nom_etapa AS etapa,
         AVG(DATEDIFF(p_hasta, p.fecha_postula)) AS dias_promedio
  FROM postulaciones p
  INNER JOIN etapas e ON p.id_etapa = e.id_etapa
  WHERE p.fecha_postula BETWEEN p_desde AND p_hasta
  GROUP BY e.nom_etapa
  ORDER BY e.nom_etapa;

  SELECT * FROM tmpTiempoEtapa;
END $$
DELIMITER ;

-- 11) conversionFuentes(desde, hasta): tasa por fuente:

DELIMITER $$

CREATE PROCEDURE conversionFuentes(
  IN p_desde DATE,
  IN p_hasta DATE
)
BEGIN
  DROP TEMPORARY TABLE IF EXISTS tmpConversionFuentes;

  CREATE TEMPORARY TABLE tmpConversionFuentes (
    fuente              VARCHAR(80),
    total_postulaciones INT,
    total_aceptadas     INT,
    tasa_conversion     DECIMAL(10,2)
  );

  INSERT INTO tmpConversionFuentes(fuente, total_postulaciones, total_aceptadas, tasa_conversion)
  SELECT f.nom_fuente AS fuente,
         COUNT(DISTINCT p.id_postulacion) AS total_postulaciones,
         COUNT(DISTINCT CASE
                          WHEN eo.nom_estado = 'Aceptada'
                          THEN o.id_oferta
                        END) AS total_aceptadas,
         CASE
           WHEN COUNT(DISTINCT p.id_postulacion) = 0 THEN 0
           ELSE ROUND(
             COUNT(DISTINCT CASE
                              WHEN eo.nom_estado = 'Aceptada'
                              THEN o.id_oferta
                            END) * 100.0
             / COUNT(DISTINCT p.id_postulacion),
             2
           )
         END AS tasa_conversion
  FROM fuentes f
  LEFT JOIN candidatos c
    ON c.id_fuente = f.id_fuente
  LEFT JOIN postulaciones p
    ON p.id_candidato = c.id_candidato
   AND p.fecha_postula BETWEEN p_desde AND p_hasta
  LEFT JOIN ofertas o
    ON o.id_postulacion = p.id_postulacion
  LEFT JOIN estados_ofertas eo
    ON o.id_estadoferta = eo.id_estadoferta
  GROUP BY f.nom_fuente
  ORDER BY tasa_conversion DESC;

  SELECT * FROM tmpConversionFuentes;
END $$
DELIMITER ;


-- 12) productividadEntrevistador(desde, hasta)

DELIMITER $$

CREATE PROCEDURE productividadEntrevistador(
  IN p_desde DATE,
  IN p_hasta DATE
)
BEGIN
  DROP TEMPORARY TABLE IF EXISTS tmpProductividadEntrevistador;

  CREATE TEMPORARY TABLE tmpProductividadEntrevistador (
    entrevistador      VARCHAR(120),
    total_entrevistas  INT,
    promedio_puntaje   DECIMAL(5,2)
  );

  INSERT INTO tmpProductividadEntrevistador(entrevistador, total_entrevistas, promedio_puntaje)
  SELECT
    e.nom_entrevistador,
    COUNT(et.id_entrevista) AS total_entrevistas,
    AVG(et.puntaje)         AS promedio_puntaje
  FROM entrevistadores e
  LEFT JOIN entrevistas et
    ON et.id_entrevistador = e.id_entrevistador
   AND et.fecha_entrevista BETWEEN p_desde AND p_hasta
  GROUP BY e.nom_entrevistador
  ORDER BY total_entrevistas DESC;

  SELECT * FROM tmpProductividadEntrevistador;
END $$

DELIMITER ;

-- 13) usuarioLogin (login + rol):

DELIMITER $$

CREATE PROCEDURE usuarioLogin(
  IN p_username VARCHAR(80),
  IN p_password VARCHAR(255)
)
BEGIN
  SELECT
    u.id_usuario,
    u.username,
    u.email,
    u.id_rolsistema,
    u.activo,
    rs.nom_rol AS rol_sistema
  FROM usuarios u
  INNER JOIN roles_sistema rs
    ON u.id_rolsistema = rs.id_rolsistema
  WHERE u.username    = p_username
    AND u.hashed_pass = p_password
    AND u.activo      = 1;
END $$

DELIMITER ;

-- 14) auditoriaPostulacion(desde, hasta): cambios en pipeline

DELIMITER $$

CREATE PROCEDURE auditoriaPostulacion(
  IN p_desde DATETIME,
  IN p_hasta DATETIME
)
BEGIN
  IF p_desde IS NULL OR p_hasta IS NULL OR p_desde > p_hasta THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Rango de fechas invalido';
  END IF;

  SELECT
    a.id_audit,
    a.id_postulacion,
    a.op,
    a.changed_by,
    a.changed_at,
    a.payload
  FROM audit_postulaciones a
  WHERE a.changed_at BETWEEN p_desde AND p_hasta
  ORDER BY a.changed_at DESC;
END $$

DELIMITER ;


