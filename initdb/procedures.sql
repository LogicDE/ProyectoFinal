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

-- =============================================
-- STORED PROCEDURES PARA DASHBOARD ADMIN
-- =============================================

DELIMITER //

-- Total de candidatos
CREATE PROCEDURE sp_total_candidatos()
BEGIN
    SELECT COUNT(*) as total FROM candidatos;
END //

-- Vacantes activas
CREATE PROCEDURE sp_vacantes_activas()
BEGIN
    SELECT COUNT(*) as total FROM vacantes WHERE id_estadovacante = 1;
END //

-- Usuarios activos
CREATE PROCEDURE sp_usuarios_activos()
BEGIN
    SELECT COUNT(*) as total FROM usuarios WHERE activo = 1;
END //

-- Postulaciones del día
CREATE PROCEDURE sp_postulaciones_hoy()
BEGIN
    SELECT COUNT(*) as total FROM postulaciones WHERE DATE(fecha_postula) = CURDATE();
END //

-- Actividad reciente
CREATE PROCEDURE sp_actividad_reciente()
BEGIN
    SELECT 'Candidato' as tipo, nom_candidato as nombre, fecha_creacion as fecha
    FROM candidatos 
    ORDER BY fecha_creacion DESC 
    LIMIT 5;
END //

-- Próximas entrevistas
CREATE PROCEDURE sp_proximas_entrevistas()
BEGIN
    SELECT e.fecha_entrevista, c.nom_candidato, v.titulo_vacante, ent.nom_entrevistador
    FROM entrevistas e
    JOIN postulaciones p ON e.id_postulacion = p.id_postulacion
    JOIN candidatos c ON p.id_candidato = c.id_candidato
    JOIN vacantes v ON p.id_vacante = v.id_vacante
    JOIN entrevistadores ent ON e.id_entrevistador = ent.id_entrevistador
    WHERE e.fecha_entrevista >= CURDATE()
    ORDER BY e.fecha_entrevista ASC
    LIMIT 5;
END //

-- =============================================
-- STORED PROCEDURES PARA DASHBOARD RECLUTADOR
-- =============================================

-- Candidatos en proceso
CREATE PROCEDURE sp_candidatos_en_proceso()
BEGIN
    SELECT COUNT(*) as total FROM postulaciones WHERE id_etapa IN (2,3,4,5);
END //

-- Candidatos recientes
CREATE PROCEDURE sp_candidatos_recientes()
BEGIN
    SELECT nom_candidato, email, fecha_creacion 
    FROM candidatos 
    ORDER BY fecha_creacion DESC 
    LIMIT 5;
END //

-- Postulaciones pendientes
CREATE PROCEDURE sp_postulaciones_pendientes()
BEGIN
    SELECT p.id_postulacion, c.nom_candidato, v.titulo_vacante, e.nom_etapa
    FROM postulaciones p
    JOIN candidatos c ON p.id_candidato = c.id_candidato
    JOIN vacantes v ON p.id_vacante = v.id_vacante
    JOIN etapas e ON p.id_etapa = e.id_etapa
    WHERE p.id_etapa IN (1,2)
    ORDER BY p.fecha_postula DESC
    LIMIT 5;
END //

-- =============================================
-- STORED PROCEDURES PARA HIRING MANAGER
-- =============================================

-- Ofertas pendientes
CREATE PROCEDURE sp_ofertas_pendientes()
BEGIN
    SELECT COUNT(*) as total FROM ofertas WHERE id_estadoferta = 1;
END //

-- Ofertas aceptadas
CREATE PROCEDURE sp_ofertas_aceptadas()
BEGIN
    SELECT COUNT(*) as total FROM ofertas WHERE id_estadoferta = 2;
END //

-- Candidatos en selección
CREATE PROCEDURE sp_candidatos_en_seleccion()
BEGIN
    SELECT COUNT(DISTINCT p.id_candidato) as total 
    FROM postulaciones p
    JOIN vacantes v ON p.id_vacante = v.id_vacante
    WHERE p.id_etapa IN (4,5,6);
END //

-- Vacantes populares
CREATE PROCEDURE sp_vacantes_populares()
BEGIN
    SELECT v.titulo_vacante, COUNT(p.id_postulacion) as postulaciones
    FROM vacantes v
    LEFT JOIN postulaciones p ON v.id_vacante = p.id_vacante
    WHERE v.id_estadovacante = 1
    GROUP BY v.id_vacante, v.titulo_vacante
    ORDER BY postulaciones DESC
    LIMIT 5;
END //

-- Candidatos finalistas
CREATE PROCEDURE sp_candidatos_finalistas()
BEGIN
    SELECT c.nom_candidato, v.titulo_vacante, e.nom_etapa
    FROM postulaciones p
    JOIN candidatos c ON p.id_candidato = c.id_candidato
    JOIN vacantes v ON p.id_vacante = v.id_vacante
    JOIN etapas e ON p.id_etapa = e.id_etapa
    WHERE p.id_etapa = 5
    ORDER BY p.fecha_postula DESC
    LIMIT 5;
END //

-- =============================================
-- STORED PROCEDURES PARA ENTREVISTADOR
-- =============================================

-- Entrevistas del día para entrevistador específico
CREATE PROCEDURE sp_entrevistas_hoy(IN p_id_entrevistador INT)
BEGIN
    SELECT COUNT(*) as total 
    FROM entrevistas 
    WHERE id_entrevistador = p_id_entrevistador 
    AND DATE(fecha_entrevista) = CURDATE();
END //

-- Pendientes de feedback
CREATE PROCEDURE sp_pendientes_feedback(IN p_id_entrevistador INT)
BEGIN
    SELECT COUNT(*) as total 
    FROM entrevistas 
    WHERE id_entrevistador = p_id_entrevistador 
    AND id_estadoentrevista = 2
    AND puntaje IS NULL;
END //

-- Próximas entrevistas para entrevistador
CREATE PROCEDURE sp_proximas_entrevistas_entrevistador(IN p_id_entrevistador INT)
BEGIN
    SELECT e.id_entrevista, e.fecha_entrevista, c.nom_candidato, v.titulo_vacante, 
           es.nom_estado as estado
    FROM entrevistas e
    JOIN postulaciones p ON e.id_postulacion = p.id_postulacion
    JOIN candidatos c ON p.id_candidato = c.id_candidato
    JOIN vacantes v ON p.id_vacante = v.id_vacante
    JOIN estados_entrevistas es ON e.id_estadoentrevista = es.id_estadoentrevista
    WHERE e.id_entrevistador = p_id_entrevistador 
    AND e.fecha_entrevista >= CURDATE()
    ORDER BY e.fecha_entrevista ASC
    LIMIT 10;
END //

-- Historial de entrevistas
CREATE PROCEDURE sp_historial_entrevistas(IN p_id_entrevistador INT)
BEGIN
    SELECT e.fecha_entrevista, c.nom_candidato, v.titulo_vacante, e.puntaje
    FROM entrevistas e
    JOIN postulaciones p ON e.id_postulacion = p.id_postulacion
    JOIN candidatos c ON p.id_candidato = c.id_candidato
    JOIN vacantes v ON p.id_vacante = v.id_vacante
    WHERE e.id_entrevistador = p_id_entrevistador 
    AND e.fecha_entrevista < CURDATE()
    ORDER BY e.fecha_entrevista DESC
    LIMIT 5;
END //

-- =============================================
-- STORED PROCEDURES PARA AUDITOR
-- =============================================

-- Totales generales
CREATE PROCEDURE sp_totales_generales()
BEGIN
    SELECT 
        (SELECT COUNT(*) FROM candidatos) as total_candidatos,
        (SELECT COUNT(*) FROM vacantes) as total_vacantes,
        (SELECT COUNT(*) FROM postulaciones) as total_postulaciones,
        (SELECT COUNT(*) FROM entrevistas) as total_entrevistas,
        (SELECT COUNT(*) FROM ofertas) as total_ofertas,
        (SELECT COUNT(*) FROM postulaciones WHERE id_etapa = 11) as total_contratados;
END //

-- Fuentes de candidatos
CREATE PROCEDURE sp_fuentes_candidatos()
BEGIN
    SELECT f.nom_fuente, COUNT(c.id_candidato) as cantidad
    FROM fuentes f
    LEFT JOIN candidatos c ON f.id_fuente = c.id_fuente
    GROUP BY f.id_fuente, f.nom_fuente
    ORDER BY cantidad DESC
    LIMIT 5;
END //

-- Tiempo promedio de proceso
CREATE PROCEDURE sp_tiempo_promedio_proceso()
BEGIN
    SELECT AVG(TIMESTAMPDIFF(DAY, p.fecha_postula, 
                COALESCE((SELECT MIN(e.fecha_entrevista) 
                         FROM entrevistas e 
                         WHERE e.id_postulacion = p.id_postulacion), 
                        CURDATE()))) as tiempo_promedio
    FROM postulaciones p
    WHERE p.id_etapa >= 3;
END //

DELIMITER ;

DELIMITER //

-- =============================================
-- STORED PROCEDURES PARA CANDIDATOS
-- =============================================

-- Obtener todos los candidatos con información de fuente
CREATE PROCEDURE sp_obtener_candidatos()
BEGIN
    SELECT c.*, f.nom_fuente 
    FROM candidatos c 
    LEFT JOIN fuentes f ON c.id_fuente = f.id_fuente
    ORDER BY c.fecha_creacion DESC;
END //

-- Obtener todas las fuentes
CREATE PROCEDURE sp_obtener_fuentes()
BEGIN
    SELECT * FROM fuentes ORDER BY nom_fuente;
END //

-- Obtener vacantes activas para registro público
CREATE PROCEDURE sp_obtener_vacantes_activas()
BEGIN
    SELECT 
        v.*, 
        d.nom_departamento,
        (SELECT COUNT(*) FROM postulaciones p WHERE p.id_vacante = v.id_vacante) as num_postulaciones
    FROM vacantes v 
    LEFT JOIN departamentos d ON v.id_departamento = d.id_departamento 
    WHERE v.id_estadovacante = 1 
    ORDER BY v.fecha_creacion DESC 
    LIMIT 10;
END //

-- Obtener candidato por ID
CREATE PROCEDURE sp_obtener_candidato_por_id(IN p_id_candidato INT)
BEGIN
    SELECT c.*, f.nom_fuente 
    FROM candidatos c 
    LEFT JOIN fuentes f ON c.id_fuente = f.id_fuente 
    WHERE c.id_candidato = p_id_candidato;
END //

-- Verificar postulaciones de candidato
CREATE PROCEDURE sp_verificar_postulaciones_candidato(IN p_id_candidato INT)
BEGIN
    SELECT COUNT(*) as total FROM postulaciones WHERE id_candidato = p_id_candidato;
END //

-- Eliminar candidato (si no tiene postulaciones)
CREATE PROCEDURE sp_eliminar_candidato(IN p_id_candidato INT, OUT p_resultado VARCHAR(500))
BEGIN
    DECLARE v_total_postulaciones INT DEFAULT 0;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_resultado = 'Error al eliminar candidato';
    END;
    
    START TRANSACTION;
    
    -- Verificar si tiene postulaciones
    SELECT COUNT(*) INTO v_total_postulaciones 
    FROM postulaciones 
    WHERE id_candidato = p_id_candidato;
    
    IF v_total_postulaciones > 0 THEN
        SET p_resultado = 'No se puede eliminar el candidato porque tiene postulaciones activas';
    ELSE
        DELETE FROM candidatos WHERE id_candidato = p_id_candidato;
        SET p_resultado = 'Candidato eliminado exitosamente';
        COMMIT;
    END IF;
END //

-- Obtener candidatos descartados (vista)
CREATE PROCEDURE sp_obtener_candidatos_descartados()
BEGIN
    SELECT * FROM vCandidatosDescartados;
END //

DELIMITER ;

DELIMITER //

-- =============================================
-- STORED PROCEDURES PARA VACANTES
-- =============================================

-- Obtener todas las vacantes con información completa
CREATE PROCEDURE sp_obtener_vacantes()
BEGIN
    SELECT 
        v.*, 
        d.nom_departamento, 
        ev.nom_estado,
        (SELECT COUNT(*) FROM postulaciones p WHERE p.id_vacante = v.id_vacante) as num_postulaciones
    FROM vacantes v 
    LEFT JOIN departamentos d ON v.id_departamento = d.id_departamento 
    LEFT JOIN estados_vacantes ev ON v.id_estadovacante = ev.id_estadovacante
    ORDER BY v.fecha_creacion DESC;
END //

-- Obtener todos los departamentos
CREATE PROCEDURE sp_obtener_departamentos()
BEGIN
    SELECT * FROM departamentos ORDER BY nom_departamento;
END //

-- Obtener todos los estados de vacantes
CREATE PROCEDURE sp_obtener_estados_vacantes()
BEGIN
    SELECT * FROM estados_vacantes ORDER BY id_estadovacante;
END //

-- Obtener vacante por ID con información completa
CREATE PROCEDURE sp_obtener_vacante_por_id(IN p_id_vacante INT)
BEGIN
    SELECT 
        v.*, 
        d.nom_departamento, 
        ev.nom_estado,
        (SELECT COUNT(*) FROM postulaciones p WHERE p.id_vacante = v.id_vacante) as num_postulaciones
    FROM vacantes v 
    LEFT JOIN departamentos d ON v.id_departamento = d.id_departamento 
    LEFT JOIN estados_vacantes ev ON v.id_estadovacante = ev.id_estadovacante
    WHERE v.id_vacante = p_id_vacante;
END //

-- Verificar postulaciones de vacante
CREATE PROCEDURE sp_verificar_postulaciones_vacante(IN p_id_vacante INT)
BEGIN
    SELECT COUNT(*) as total FROM postulaciones WHERE id_vacante = p_id_vacante;
END //

-- Eliminar vacante (si no tiene postulaciones)
CREATE PROCEDURE sp_eliminar_vacante(IN p_id_vacante INT, OUT p_resultado VARCHAR(500))
BEGIN
    DECLARE v_total_postulaciones INT DEFAULT 0;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_resultado = 'Error al eliminar vacante';
    END;
    
    START TRANSACTION;
    
    -- Verificar si tiene postulaciones
    SELECT COUNT(*) INTO v_total_postulaciones 
    FROM postulaciones 
    WHERE id_vacante = p_id_vacante;
    
    IF v_total_postulaciones > 0 THEN
        SET p_resultado = 'No se puede eliminar la vacante porque tiene postulaciones activas';
    ELSE
        DELETE FROM vacantes WHERE id_vacante = p_id_vacante;
        SET p_resultado = 'Vacante eliminada exitosamente';
        COMMIT;
    END IF;
END //

-- Obtener estadísticas detalladas de vacante
CREATE PROCEDURE sp_obtener_estadisticas_vacante(IN p_id_vacante INT)
BEGIN
    SELECT 
        v.*, 
        d.nom_departamento, 
        ev.nom_estado,
        (SELECT COUNT(*) FROM postulaciones p WHERE p.id_vacante = v.id_vacante) as num_postulaciones,
        (SELECT COUNT(*) FROM entrevistas e 
         JOIN postulaciones p ON e.id_postulacion = p.id_postulacion 
         WHERE p.id_vacante = v.id_vacante) as num_entrevistas,
        (SELECT COUNT(*) FROM ofertas o 
         JOIN postulaciones p ON o.id_postulacion = p.id_postulacion 
         WHERE p.id_vacante = v.id_vacante) as num_ofertas,
        (SELECT COUNT(*) FROM postulaciones p 
         WHERE p.id_vacante = v.id_vacante AND p.id_etapa = 11) as num_contratados
    FROM vacantes v 
    LEFT JOIN departamentos d ON v.id_departamento = d.id_departamento 
    LEFT JOIN estados_vacantes ev ON v.id_estadovacante = ev.id_estadovacante 
    WHERE v.id_vacante = p_id_vacante;
END //

DELIMITER ;

DELIMITER //

-- =============================================
-- STORED PROCEDURES PARA POSTULACIONES
-- =============================================

-- Obtener todas las postulaciones con información completa
CREATE PROCEDURE sp_obtener_postulaciones()
BEGIN
    SELECT p.*, c.nom_candidato, c.email, c.telefono, 
           v.titulo_vacante, d.nom_departamento, ev.nom_estado, e.nom_etapa
    FROM postulaciones p 
    JOIN candidatos c ON p.id_candidato = c.id_candidato 
    JOIN vacantes v ON p.id_vacante = v.id_vacante 
    LEFT JOIN departamentos d ON v.id_departamento = d.id_departamento 
    LEFT JOIN estados_vacantes ev ON v.id_estadovacante = ev.id_estadovacante 
    JOIN etapas e ON p.id_etapa = e.id_etapa
    ORDER BY p.fecha_postula DESC;
END //

-- Obtener candidatos activos para postulaciones
CREATE PROCEDURE sp_obtener_candidatos_postulaciones()
BEGIN
    SELECT id_candidato, nom_candidato, email FROM candidatos ORDER BY nom_candidato;
END //

-- Obtener vacantes activas para postulaciones
CREATE PROCEDURE sp_obtener_vacantes_postulaciones()
BEGIN
    SELECT id_vacante, titulo_vacante FROM vacantes ORDER BY titulo_vacante;
END //

-- Obtener todas las etapas
CREATE PROCEDURE sp_obtener_etapas()
BEGIN
    SELECT id_etapa, nom_etapa FROM etapas ORDER BY id_etapa;
END //

-- Crear postulación con etapa personalizada
CREATE PROCEDURE sp_crear_postulacion(
    IN p_id_candidato INT,
    IN p_id_vacante INT,
    IN p_id_etapa INT,
    OUT p_resultado VARCHAR(500)
)
BEGIN
    DECLARE v_existe_postulacion INT DEFAULT 0;
    DECLARE v_postulacion_id INT DEFAULT 0;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_resultado = 'Error al crear postulación';
    END;
    
    START TRANSACTION;
    
    -- Verificar si ya existe la postulación
    SELECT COUNT(*) INTO v_existe_postulacion 
    FROM postulaciones 
    WHERE id_candidato = p_id_candidato AND id_vacante = p_id_vacante;
    
    IF v_existe_postulacion > 0 THEN
        SET p_resultado = 'El candidato ya está postulado a esta vacante';
    ELSE
        -- Llamar al stored procedure existente para crear postulación
        CALL postular(p_id_candidato, p_id_vacante);
        
        -- Obtener el ID de la postulación recién creada
        SELECT LAST_INSERT_ID() INTO v_postulacion_id;
        
        -- Si se especificó una etapa diferente a la inicial, actualizarla
        IF p_id_etapa != 1 THEN
            UPDATE postulaciones SET id_etapa = p_id_etapa WHERE id_postulacion = v_postulacion_id;
        END IF;
        
        SET p_resultado = 'Postulación creada exitosamente';
        COMMIT;
    END IF;
END //

-- Actualizar etapa de postulación
CREATE PROCEDURE sp_actualizar_etapa_postulacion(
    IN p_id_postulacion INT,
    IN p_nueva_etapa INT,
    OUT p_resultado VARCHAR(500)
)
BEGIN
    DECLARE v_etapa_existe INT DEFAULT 0;
    DECLARE v_postulacion_existe INT DEFAULT 0;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_resultado = 'Error al actualizar etapa';
    END;
    
    START TRANSACTION;
    
    -- Verificar que la postulación existe
    SELECT COUNT(*) INTO v_postulacion_existe 
    FROM postulaciones 
    WHERE id_postulacion = p_id_postulacion;
    
    IF v_postulacion_existe = 0 THEN
        SET p_resultado = 'Postulación no encontrada';
    ELSE
        -- Verificar que la nueva etapa existe
        SELECT COUNT(*) INTO v_etapa_existe 
        FROM etapas 
        WHERE id_etapa = p_nueva_etapa;
        
        IF v_etapa_existe = 0 THEN
            SET p_resultado = 'Etapa no válida';
        ELSE
            -- Actualizar la etapa
            UPDATE postulaciones 
            SET id_etapa = p_nueva_etapa 
            WHERE id_postulacion = p_id_postulacion;
            
            SET p_resultado = 'Etapa actualizada exitosamente';
            COMMIT;
        END IF;
    END IF;
END //

-- Eliminar postulación y sus dependencias
CREATE PROCEDURE sp_eliminar_postulacion(
    IN p_id_postulacion INT,
    OUT p_resultado VARCHAR(500)
)
BEGIN
    DECLARE v_entrevistas_count INT DEFAULT 0;
    DECLARE v_ofertas_count INT DEFAULT 0;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_resultado = 'Error al eliminar postulación';
    END;
    
    START TRANSACTION;
    
    -- Verificar si existen entrevistas asociadas
    SELECT COUNT(*) INTO v_entrevistas_count 
    FROM entrevistas 
    WHERE id_postulacion = p_id_postulacion;
    
    -- Verificar si existen ofertas asociadas
    SELECT COUNT(*) INTO v_ofertas_count 
    FROM ofertas 
    WHERE id_postulacion = p_id_postulacion;
    
    -- Eliminar entrevistas asociadas si existen
    IF v_entrevistas_count > 0 THEN
        DELETE FROM entrevistas WHERE id_postulacion = p_id_postulacion;
    END IF;
    
    -- Eliminar ofertas asociadas si existen
    IF v_ofertas_count > 0 THEN
        DELETE FROM ofertas WHERE id_postulacion = p_id_postulacion;
    END IF;
    
    -- Eliminar la postulación
    DELETE FROM postulaciones WHERE id_postulacion = p_id_postulacion;
    
    -- Construir mensaje de resultado
    SET p_resultado = CONCAT(
        'Postulación eliminada exitosamente',
        CASE 
            WHEN v_entrevistas_count > 0 THEN CONCAT(' (Se eliminaron ', v_entrevistas_count, ' entrevistas)')
            ELSE ''
        END,
        CASE 
            WHEN v_ofertas_count > 0 THEN CONCAT(' (Se eliminaron ', v_ofertas_count, ' ofertas)')
            ELSE ''
        END
    );
    
    COMMIT;
END //

-- Obtener postulación por ID con información completa
CREATE PROCEDURE sp_obtener_postulacion_por_id(IN p_id_postulacion INT)
BEGIN
    SELECT p.*, c.nom_candidato, c.email, c.telefono, 
           v.titulo_vacante, d.nom_departamento, ev.nom_estado, e.nom_etapa
    FROM postulaciones p 
    JOIN candidatos c ON p.id_candidato = c.id_candidato 
    JOIN vacantes v ON p.id_vacante = v.id_vacante 
    LEFT JOIN departamentos d ON v.id_departamento = d.id_departamento 
    LEFT JOIN estados_vacantes ev ON v.id_estadovacante = ev.id_estadovacante 
    JOIN etapas e ON p.id_etapa = e.id_etapa
    WHERE p.id_postulacion = p_id_postulacion;
END //

DELIMITER ;

DELIMITER //

-- =============================================
-- STORED PROCEDURES PARA ENTREVISTAS
-- =============================================

-- Obtener todas las entrevistas con información completa
CREATE PROCEDURE sp_obtener_entrevistas()
BEGIN
    SELECT 
        e.*, 
        p.id_postulacion,
        c.id_candidato,
        c.nom_candidato, 
        c.email as email_candidato,
        c.telefono as telefono_candidato,
        v.id_vacante,
        v.titulo_vacante, 
        d.nom_departamento,
        ent.id_entrevistador,
        ent.nom_entrevistador,
        ent.email as email_entrevistador,
        es.id_estadoentrevista,
        es.nom_estado as estado_entrevista,
        CONCAT(c.nom_candidato, ' - ', v.titulo_vacante) as descripcion,
        CASE 
            WHEN e.fecha_entrevista < CURDATE() THEN 'Pasada'
            WHEN e.fecha_entrevista = CURDATE() THEN 'Hoy'
            ELSE 'Futura'
        END as tipo_fecha
    FROM entrevistas e
    JOIN postulaciones p ON e.id_postulacion = p.id_postulacion
    JOIN candidatos c ON p.id_candidato = c.id_candidato
    JOIN vacantes v ON p.id_vacante = v.id_vacante
    LEFT JOIN departamentos d ON v.id_departamento = d.id_departamento
    JOIN entrevistadores ent ON e.id_entrevistador = ent.id_entrevistador
    JOIN estados_entrevistas es ON e.id_estadoentrevista = es.id_estadoentrevista
    ORDER BY e.fecha_entrevista DESC, e.id_entrevista DESC;
END //

-- Obtener postulaciones disponibles para entrevistas
CREATE PROCEDURE sp_obtener_postulaciones_entrevistables()
BEGIN
    SELECT p.id_postulacion, c.nom_candidato, v.titulo_vacante,
           CONCAT(c.nom_candidato, ' - ', v.titulo_vacante) as descripcion
    FROM postulaciones p
    JOIN candidatos c ON p.id_candidato = c.id_candidato
    JOIN vacantes v ON p.id_vacante = v.id_vacante
    WHERE p.id_etapa NOT IN (11,12)  -- Excluir etapas finales
    ORDER BY c.nom_candidato;
END //

-- Obtener todos los entrevistadores
CREATE PROCEDURE sp_obtener_entrevistadores()
BEGIN
    SELECT * FROM entrevistadores ORDER BY nom_entrevistador;
END //

-- Obtener todos los estados de entrevista
CREATE PROCEDURE sp_obtener_estados_entrevista()
BEGIN
    SELECT * FROM estados_entrevistas ORDER BY id_estadoentrevista;
END //

-- Obtener entrevista por ID con información completa
CREATE PROCEDURE sp_obtener_entrevista_por_id(IN p_id_entrevista INT)
BEGIN
    SELECT e.*, p.id_postulacion, c.nom_candidato, v.titulo_vacante,
           ent.nom_entrevistador, es.nom_estado as estado_entrevista,
           DATE(e.fecha_entrevista) as fecha_sola,
           TIME(e.fecha_entrevista) as hora_sola
    FROM entrevistas e
    JOIN postulaciones p ON e.id_postulacion = p.id_postulacion
    JOIN candidatos c ON p.id_candidato = c.id_candidato
    JOIN vacantes v ON p.id_vacante = v.id_vacante
    JOIN entrevistadores ent ON e.id_entrevistador = ent.id_entrevistador
    JOIN estados_entrevistas es ON e.id_estadoentrevista = es.id_estadoentrevista
    WHERE e.id_entrevista = p_id_entrevista;
END //

-- Crear entrevista con validaciones
CREATE PROCEDURE sp_crear_entrevista(
    IN p_id_postulacion INT,
    IN p_fecha_entrevista DATETIME,
    IN p_id_entrevistador INT,
    IN p_id_estadoentrevista INT,
    IN p_notas TEXT,
    OUT p_resultado VARCHAR(500)
)
BEGIN
    DECLARE v_entrevista_existente INT DEFAULT 0;
    DECLARE v_entrevista_id INT DEFAULT 0;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_resultado = 'Error al programar entrevista';
    END;
    
    START TRANSACTION;
    
    -- Verificar si ya existe una entrevista para esta postulación
    SELECT COUNT(*) INTO v_entrevista_existente
    FROM entrevistas 
    WHERE id_postulacion = p_id_postulacion 
    AND id_estadoentrevista IN (1, 2);  -- Programada o en progreso
    
    IF v_entrevista_existente > 0 THEN
        SET p_resultado = 'Ya existe una entrevista programada para esta postulación';
    ELSE
        -- Insertar la nueva entrevista
        INSERT INTO entrevistas (
            id_postulacion, 
            fecha_entrevista, 
            id_entrevistador, 
            id_estadoentrevista, 
            notas
        ) VALUES (
            p_id_postulacion,
            p_fecha_entrevista,
            p_id_entrevistador,
            p_id_estadoentrevista,
            p_notas
        );
        
        SET v_entrevista_id = LAST_INSERT_ID();
        SET p_resultado = CONCAT('Entrevista programada exitosamente. ID: ', v_entrevista_id);
        COMMIT;
    END IF;
END //

-- Actualizar entrevista
CREATE PROCEDURE sp_actualizar_entrevista(
    IN p_id_entrevista INT,
    IN p_fecha_entrevista DATETIME,
    IN p_id_entrevistador INT,
    IN p_id_estadoentrevista INT,
    IN p_notas TEXT,
    OUT p_resultado VARCHAR(500)
)
BEGIN
    DECLARE v_entrevista_existe INT DEFAULT 0;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_resultado = 'Error al actualizar entrevista';
    END;
    
    START TRANSACTION;
    
    -- Verificar que la entrevista existe
    SELECT COUNT(*) INTO v_entrevista_existe
    FROM entrevistas 
    WHERE id_entrevista = p_id_entrevista;
    
    IF v_entrevista_existe = 0 THEN
        SET p_resultado = 'Entrevista no encontrada';
    ELSE
        -- Actualizar la entrevista
        UPDATE entrevistas 
        SET fecha_entrevista = p_fecha_entrevista,
            id_entrevistador = p_id_entrevistador,
            id_estadoentrevista = p_id_estadoentrevista,
            notas = p_notas
        WHERE id_entrevista = p_id_entrevista;
        
        SET p_resultado = 'Entrevista actualizada exitosamente';
        COMMIT;
    END IF;
END //

-- Eliminar entrevista
CREATE PROCEDURE sp_eliminar_entrevista(
    IN p_id_entrevista INT,
    OUT p_resultado VARCHAR(500)
)
BEGIN
    DECLARE v_entrevista_existe INT DEFAULT 0;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_resultado = 'Error al eliminar entrevista';
    END;
    
    START TRANSACTION;
    
    -- Verificar que la entrevista existe
    SELECT COUNT(*) INTO v_entrevista_existe
    FROM entrevistas 
    WHERE id_entrevista = p_id_entrevista;
    
    IF v_entrevista_existe = 0 THEN
        SET p_resultado = 'Entrevista no encontrada';
    ELSE
        -- Eliminar la entrevista
        DELETE FROM entrevistas WHERE id_entrevista = p_id_entrevista;
        SET p_resultado = 'Entrevista eliminada exitosamente';
        COMMIT;
    END IF;
END //

-- Obtener postulaciones para entrevistas (API)
CREATE PROCEDURE sp_obtener_postulaciones_entrevistables_api()
BEGIN
    SELECT p.id_postulacion, c.nom_candidato, v.titulo_vacante,
           CONCAT(c.nom_candidato, ' - ', v.titulo_vacante) as descripcion,
           e.nom_etapa as etapa_actual
    FROM postulaciones p
    JOIN candidatos c ON p.id_candidato = c.id_candidato
    JOIN vacantes v ON p.id_vacante = v.id_vacante
    JOIN etapas e ON p.id_etapa = e.id_etapa
    WHERE p.id_etapa NOT IN (11,12)  -- Excluir etapas finales
    AND NOT EXISTS (
        SELECT 1 FROM entrevistas ent 
        WHERE ent.id_postulacion = p.id_postulacion 
        AND ent.id_estadoentrevista IN (1, 2)  -- Excluir si ya tiene entrevista programada o en progreso
    )
    ORDER BY c.nom_candidato;
END //

-- Obtener entrevista detallada para API
CREATE PROCEDURE sp_obtener_entrevista_detallada(IN p_id_entrevista INT)
BEGIN
    SELECT 
        e.id_entrevista,
        e.fecha_entrevista,
        e.puntaje,
        e.notas,
        e.id_estadoentrevista,
        e.id_entrevistador,
        p.id_postulacion,
        c.nom_candidato, 
        c.email as email_candidato,
        c.telefono as telefono_candidato,
        v.titulo_vacante, 
        d.nom_departamento,
        ent.nom_entrevistador,
        ent.email as email_entrevistador,
        ent.telefono as telefono_entrevistador,
        es.nom_estado as estado_entrevista
    FROM entrevistas e
    LEFT JOIN postulaciones p ON e.id_postulacion = p.id_postulacion
    LEFT JOIN candidatos c ON p.id_candidato = c.id_candidato
    LEFT JOIN vacantes v ON p.id_vacante = v.id_vacante
    LEFT JOIN departamentos d ON v.id_departamento = d.id_departamento
    LEFT JOIN entrevistadores ent ON e.id_entrevistador = ent.id_entrevistador
    LEFT JOIN estados_entrevistas es ON e.id_estadoentrevista = es.id_estadoentrevista
    WHERE e.id_entrevista = p_id_entrevista;
END //

-- Obtener entrevistas de la semana (usando vista existente)
CREATE PROCEDURE sp_obtener_entrevistas_semana()
BEGIN
    SELECT * FROM vEntrevistasSemana;
END //

DELIMITER ;

DELIMITER //

-- =============================================
-- STORED PROCEDURES PARA OFERTAS
-- =============================================

-- Obtener todas las ofertas con información completa
CREATE PROCEDURE sp_obtener_ofertas()
BEGIN
    SELECT 
        o.*, 
        p.id_postulacion,
        c.id_candidato,
        c.nom_candidato, 
        c.email,
        c.telefono,
        v.id_vacante,
        v.titulo_vacante, 
        d.nom_departamento,
        eo.id_estadoferta,
        eo.nom_estado as estado_oferta,
        CONCAT(c.nom_candidato, ' - ', v.titulo_vacante) as descripcion,
        CASE 
            WHEN o.fecha_decision IS NULL THEN 'Pendiente de decisión'
            ELSE 'Decidida'
        END as estado_avance
    FROM ofertas o
    JOIN postulaciones p ON o.id_postulacion = p.id_postulacion
    JOIN candidatos c ON p.id_candidato = c.id_candidato
    JOIN vacantes v ON p.id_vacante = v.id_vacante
    LEFT JOIN departamentos d ON v.id_departamento = d.id_departamento
    JOIN estados_ofertas eo ON o.id_estadoferta = eo.id_estadoferta
    ORDER BY o.id_oferta DESC;
END //

-- Obtener postulaciones disponibles para ofertas
CREATE PROCEDURE sp_obtener_postulaciones_ofertables()
BEGIN
    SELECT p.id_postulacion, c.nom_candidato, v.titulo_vacante,
           CONCAT(c.nom_candidato, ' - ', v.titulo_vacante) as descripcion,
           e.nom_etapa as etapa_actual
    FROM postulaciones p
    JOIN candidatos c ON p.id_candidato = c.id_candidato
    JOIN vacantes v ON p.id_vacante = v.id_vacante
    JOIN etapas e ON p.id_etapa = e.id_etapa
    WHERE p.id_etapa >= 4  -- Incluir etapas finales
    AND NOT EXISTS (
        SELECT 1 FROM ofertas o 
        WHERE o.id_postulacion = p.id_postulacion 
        AND o.id_estadoferta IN (1)  -- Excluir si ya tiene oferta pendiente
    )
    ORDER BY c.nom_candidato;
END //

-- Obtener todos los estados de oferta
CREATE PROCEDURE sp_obtener_estados_oferta()
BEGIN
    SELECT * FROM estados_ofertas ORDER BY id_estadoferta;
END //

-- Obtener oferta por ID con información completa
CREATE PROCEDURE sp_obtener_oferta_por_id(IN p_id_oferta INT)
BEGIN
    SELECT o.*, p.id_postulacion, c.nom_candidato, v.titulo_vacante,
           eo.nom_estado as estado_oferta
    FROM ofertas o
    JOIN postulaciones p ON o.id_postulacion = p.id_postulacion
    JOIN candidatos c ON p.id_candidato = c.id_candidato
    JOIN vacantes v ON p.id_vacante = v.id_vacante
    JOIN estados_ofertas eo ON o.id_estadoferta = eo.id_estadoferta
    WHERE o.id_oferta = p_id_oferta;
END //

-- Crear oferta con validaciones
CREATE PROCEDURE sp_crear_oferta(
    IN p_id_postulacion INT,
    IN p_monto_oferta DECIMAL(10,2),
    IN p_id_estadoferta INT,
    IN p_notas TEXT,
    OUT p_resultado VARCHAR(500)
)
BEGIN
    DECLARE v_etapa_postulacion INT DEFAULT 0;
    DECLARE v_oferta_existente INT DEFAULT 0;
    DECLARE v_oferta_id INT DEFAULT 0;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_resultado = 'Error al emitir oferta';
    END;
    
    START TRANSACTION;
    
    -- Verificar la etapa de la postulación
    SELECT id_etapa INTO v_etapa_postulacion
    FROM postulaciones 
    WHERE id_postulacion = p_id_postulacion;
    
    -- Verificar si ya existe una oferta para esta postulación
    SELECT COUNT(*) INTO v_oferta_existente
    FROM ofertas 
    WHERE id_postulacion = p_id_postulacion 
    AND id_estadoferta IN (1);  -- Pendiente
    
    IF v_etapa_postulacion < 4 THEN
        SET p_resultado = 'Solo se pueden emitir ofertas a candidatos en etapas finales (Etapa 4 o superior)';
    ELSEIF v_oferta_existente > 0 THEN
        SET p_resultado = 'Ya existe una oferta pendiente para esta postulación';
    ELSE
        -- Insertar la nueva oferta
        INSERT INTO ofertas (
            id_postulacion, 
            monto_oferta, 
            id_estadoferta, 
            notas
        ) VALUES (
            p_id_postulacion,
            p_monto_oferta,
            p_id_estadoferta,
            p_notas
        );
        
        SET v_oferta_id = LAST_INSERT_ID();
        SET p_resultado = CONCAT('Oferta emitida exitosamente. ID: ', v_oferta_id);
        COMMIT;
    END IF;
END //

-- Actualizar oferta
CREATE PROCEDURE sp_actualizar_oferta(
    IN p_id_oferta INT,
    IN p_monto_oferta DECIMAL(10,2),
    IN p_id_estadoferta INT,
    IN p_notas TEXT,
    OUT p_resultado VARCHAR(500)
)
BEGIN
    DECLARE v_oferta_existe INT DEFAULT 0;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_resultado = 'Error al actualizar oferta';
    END;
    
    START TRANSACTION;
    
    -- Verificar que la oferta existe
    SELECT COUNT(*) INTO v_oferta_existe
    FROM ofertas 
    WHERE id_oferta = p_id_oferta;
    
    IF v_oferta_existe = 0 THEN
        SET p_resultado = 'Oferta no encontrada';
    ELSE
        -- Actualizar la oferta
        UPDATE ofertas 
        SET monto_oferta = p_monto_oferta,
            id_estadoferta = p_id_estadoferta,
            notas = p_notas
        WHERE id_oferta = p_id_oferta;
        
        SET p_resultado = 'Oferta actualizada exitosamente';
        COMMIT;
    END IF;
END //

-- Decidir oferta (aceptar/rechazar)
CREATE PROCEDURE sp_decidir_oferta(
    IN p_id_oferta INT,
    IN p_id_estadoferta INT,
    OUT p_resultado VARCHAR(500)
)
BEGIN
    DECLARE v_oferta_existe INT DEFAULT 0;
    DECLARE v_estado_actual INT DEFAULT 0;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_resultado = 'Error al registrar decisión de oferta';
    END;
    
    START TRANSACTION;
    
    -- Verificar que la oferta existe y obtener su estado actual
    SELECT COUNT(*), id_estadoferta INTO v_oferta_existe, v_estado_actual
    FROM ofertas 
    WHERE id_oferta = p_id_oferta;
    
    IF v_oferta_existe = 0 THEN
        SET p_resultado = 'Oferta no encontrada';
    ELSEIF v_estado_actual != 1 THEN
        SET p_resultado = 'Solo se pueden decidir ofertas en estado "Pendiente"';
    ELSEIF p_id_estadoferta NOT IN (2, 3) THEN
        SET p_resultado = 'Estado de oferta no válido. Use Aceptada (2) o Rechazada (3)';
    ELSE
        -- Actualizar la oferta con la decisión
        UPDATE ofertas 
        SET id_estadoferta = p_id_estadoferta, 
            fecha_decision = NOW()
        WHERE id_oferta = p_id_oferta;
        
        SET p_resultado = CONCAT('Oferta ', 
            CASE WHEN p_id_estadoferta = 2 THEN 'ACEPTADA' ELSE 'RECHAZADA' END,
            ' exitosamente');
        COMMIT;
    END IF;
END //

-- Eliminar oferta
CREATE PROCEDURE sp_eliminar_oferta(
    IN p_id_oferta INT,
    OUT p_resultado VARCHAR(500)
)
BEGIN
    DECLARE v_oferta_existe INT DEFAULT 0;
    DECLARE v_estado_actual INT DEFAULT 0;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_resultado = 'Error al eliminar oferta';
    END;
    
    START TRANSACTION;
    
    -- Verificar que la oferta existe y obtener su estado
    SELECT COUNT(*), id_estadoferta INTO v_oferta_existe, v_estado_actual
    FROM ofertas 
    WHERE id_oferta = p_id_oferta;
    
    IF v_oferta_existe = 0 THEN
        SET p_resultado = 'Oferta no encontrada';
    ELSEIF v_estado_actual IN (2, 3) THEN
        SET p_resultado = 'No se puede eliminar una oferta que ya ha sido decidida';
    ELSE
        -- Eliminar la oferta
        DELETE FROM ofertas WHERE id_oferta = p_id_oferta;
        SET p_resultado = 'Oferta eliminada exitosamente';
        COMMIT;
    END IF;
END //

-- Obtener postulaciones ofertables para API
CREATE PROCEDURE sp_obtener_postulaciones_ofertables_api()
BEGIN
    SELECT p.id_postulacion, c.nom_candidato, v.titulo_vacante,
           CONCAT(c.nom_candidato, ' - ', v.titulo_vacante) as descripcion,
           e.nom_etapa as etapa_actual,
           c.email,
           c.telefono
    FROM postulaciones p
    JOIN candidatos c ON p.id_candidato = c.id_candidato
    JOIN vacantes v ON p.id_vacante = v.id_vacante
    JOIN etapas e ON p.id_etapa = e.id_etapa
    WHERE p.id_etapa = 5  -- Solo etapa finalista
    AND NOT EXISTS (
        SELECT 1 FROM ofertas o 
        WHERE o.id_postulacion = p.id_postulacion 
        AND o.id_estadoferta IN (1)  -- Excluir si ya tiene oferta pendiente
    )
    ORDER BY c.nom_candidato;
END //

-- Obtener estadísticas de ofertas
CREATE PROCEDURE sp_obtener_estadisticas_ofertas()
BEGIN
    SELECT 
        COUNT(*) as total_ofertas,
        SUM(CASE WHEN id_estadoferta = 1 THEN 1 ELSE 0 END) as ofertas_pendientes,
        SUM(CASE WHEN id_estadoferta = 2 THEN 1 ELSE 0 END) as ofertas_aceptadas,
        SUM(CASE WHEN id_estadoferta = 3 THEN 1 ELSE 0 END) as ofertas_rechazadas,
        AVG(CASE WHEN id_estadoferta = 2 THEN monto_oferta ELSE NULL END) as monto_promedio
    FROM ofertas;
END //

-- Obtener ofertas recientes para dashboard
CREATE PROCEDURE sp_obtener_ofertas_recientes()
BEGIN
    SELECT o.*, c.nom_candidato, v.titulo_vacante, eo.nom_estado as estado_oferta
    FROM ofertas o
    JOIN postulaciones p ON o.id_postulacion = p.id_postulacion
    JOIN candidatos c ON p.id_candidato = c.id_candidato
    JOIN vacantes v ON p.id_vacante = v.id_vacante
    JOIN estados_ofertas eo ON o.id_estadoferta = eo.id_estadoferta
    ORDER BY o.id_oferta DESC
    LIMIT 10;
END //

-- =============================================
-- STORED PROCEDURES PARA REPORTES DE OFERTAS
-- =============================================

-- Distribución de ofertas por estado
CREATE PROCEDURE sp_reporte_ofertas_distribucion_estado()
BEGIN
    SELECT eo.nom_estado, COUNT(*) as cantidad
    FROM ofertas o
    JOIN estados_ofertas eo ON o.id_estadoferta = eo.id_estadoferta
    GROUP BY eo.nom_estado
    ORDER BY cantidad DESC;
END //

-- Tendencias mensuales de ofertas
CREATE PROCEDURE sp_reporte_ofertas_tendencias_mensuales()
BEGIN
    SELECT 
        DATE_FORMAT(fecha_cambio, '%Y-%m') as mes,
        COUNT(*) as cantidad,
        SUM(CASE WHEN JSON_EXTRACT(payload, '$.estado') = 2 THEN 1 ELSE 0 END) as aceptadas,
        SUM(CASE WHEN JSON_EXTRACT(payload, '$.estado') = 3 THEN 1 ELSE 0 END) as rechazadas
    FROM audit_ofertas
    WHERE op = 'U' AND JSON_EXTRACT(payload, '$.new_estado') IN (2, 3)
    GROUP BY DATE_FORMAT(fecha_cambio, '%Y-%m')
    ORDER BY mes
    LIMIT 12;
END //

-- Métricas clave de ofertas
CREATE PROCEDURE sp_reporte_ofertas_metricas_clave()
BEGIN
    DECLARE v_total_ofertas INT;
    DECLARE v_monto_promedio DECIMAL(10,2);
    DECLARE v_aceptadas INT;
    DECLARE v_tasa_aceptacion DECIMAL(5,2);
    DECLARE v_tiempo_promedio DECIMAL(10,2);
    
    SELECT COUNT(*) INTO v_total_ofertas FROM ofertas;
    SELECT AVG(monto_oferta) INTO v_monto_promedio FROM ofertas WHERE id_estadoferta = 2;
    SELECT COUNT(*) INTO v_aceptadas FROM ofertas WHERE id_estadoferta = 2;
    
    IF v_total_ofertas > 0 THEN
        SET v_tasa_aceptacion = (v_aceptadas / v_total_ofertas * 100);
    ELSE
        SET v_tasa_aceptacion = 0;
    END IF;
    
    SELECT AVG(DATEDIFF(fecha_cambio, 
                (SELECT MAX(fecha_cambio) 
                 FROM audit_ofertas a2 
                 WHERE a2.id_oferta = a1.id_oferta AND a2.fecha_cambio < a1.fecha_cambio)
            )) INTO v_tiempo_promedio
    FROM audit_ofertas a1
    WHERE op = 'U' AND JSON_EXTRACT(payload, '$.new_estado') IN (2, 3);
    
    SELECT 
        v_total_ofertas as total_ofertas,
        COALESCE(v_monto_promedio, 0) as monto_promedio,
        v_tasa_aceptacion as tasa_aceptacion,
        COALESCE(v_tiempo_promedio, 0) as tiempo_promedio_decision;
END //

-- Ofertas por vacante
CREATE PROCEDURE sp_reporte_ofertas_por_vacante()
BEGIN
    SELECT 
        v.id_vacante,
        v.titulo_vacante,
        COUNT(o.id_oferta) as total_ofertas,
        SUM(CASE WHEN o.id_estadoferta = 2 THEN 1 ELSE 0 END) as aceptadas,
        SUM(CASE WHEN o.id_estadoferta = 3 THEN 1 ELSE 0 END) as rechazadas,
        AVG(o.monto_oferta) as monto_promedio
    FROM vacantes v
    LEFT JOIN postulaciones p ON v.id_vacante = p.id_vacante
    LEFT JOIN ofertas o ON p.id_postulacion = o.id_postulacion
    GROUP BY v.id_vacante, v.titulo_vacante
    HAVING total_ofertas > 0
    ORDER BY total_ofertas DESC
    LIMIT 10;
END //

-- Reporte detallado de ofertas con filtros
CREATE PROCEDURE sp_reporte_ofertas_detallado(
    IN p_fecha_inicio DATE,
    IN p_fecha_fin DATE,
    IN p_estado VARCHAR(10)
)
BEGIN
    SET @query = '
        SELECT 
            o.id_oferta,
            c.nom_candidato,
            v.titulo_vacante,
            o.monto_oferta,
            eo.nom_estado,
            (SELECT MIN(fecha_cambio) 
             FROM audit_ofertas a 
             WHERE a.id_oferta = o.id_oferta AND a.op = "I") as fecha_emision_estimada,
            o.fecha_decision,
            DATEDIFF(o.fecha_decision, 
                (SELECT MIN(fecha_cambio) 
                 FROM audit_ofertas a 
                 WHERE a.id_oferta = o.id_oferta AND a.op = "I")
            ) as dias_pendiente
        FROM ofertas o
        JOIN postulaciones p ON o.id_postulacion = p.id_postulacion
        JOIN candidatos c ON p.id_candidato = c.id_candidato
        JOIN vacantes v ON p.id_vacante = v.id_vacante
        JOIN estados_ofertas eo ON o.id_estadoferta = eo.id_estadoferta
        WHERE 1=1';
    
    IF p_fecha_inicio IS NOT NULL AND p_fecha_inicio != '' THEN
        SET @query = CONCAT(@query, ' AND (SELECT MIN(fecha_cambio) FROM audit_ofertas a WHERE a.id_oferta = o.id_oferta AND a.op = "I") >= "', p_fecha_inicio, '"');
    END IF;
    
    IF p_fecha_fin IS NOT NULL AND p_fecha_fin != '' THEN
        SET @query = CONCAT(@query, ' AND (SELECT MIN(fecha_cambio) FROM audit_ofertas a WHERE a.id_oferta = o.id_oferta AND a.op = "I") <= "', p_fecha_fin, '"');
    END IF;
    
    IF p_estado IS NOT NULL AND p_estado != 'todos' THEN
        SET @query = CONCAT(@query, ' AND o.id_estadoferta = ', p_estado);
    END IF;
    
    SET @query = CONCAT(@query, ' ORDER BY o.id_oferta DESC');
    
    PREPARE stmt FROM @query;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
END //

DELIMITER ;

DELIMITER //

-- =============================================
-- STORED PROCEDURES PARA CALENDARIO
-- =============================================

-- Obtener todos los eventos del calendario para FullCalendar
CREATE PROCEDURE sp_obtener_eventos_calendario()
BEGIN
    SELECT 
        e.id_entrevista,
        e.fecha_entrevista,
        DATE_ADD(e.fecha_entrevista, INTERVAL 1 HOUR) as end,
        c.nom_candidato,
        v.titulo_vacante,
        ent.nom_entrevistador,
        es.nom_estado as estado_entrevista,
        es.id_estadoentrevista,
        CONCAT(c.nom_candidato, ' - ', v.titulo_vacante) as title,
        CASE 
            WHEN es.id_estadoentrevista = 1 THEN '#3498db'  -- Programada - Azul
            WHEN es.id_estadoentrevista = 2 THEN '#f39c12'  -- En progreso - Naranja
            WHEN es.id_estadoentrevista = 3 THEN '#27ae60'  -- Completada - Verde
            WHEN es.id_estadoentrevista = 4 THEN '#e74c3c'  -- Cancelada - Rojo
            ELSE '#95a5a6'  -- Otros - Gris
        END as color,
        CASE 
            WHEN es.id_estadoentrevista = 1 THEN '#2980b9'  -- Programada - Azul oscuro
            WHEN es.id_estadoentrevista = 2 THEN '#e67e22'  -- En progreso - Naranja oscuro
            WHEN es.id_estadoentrevista = 3 THEN '#229954'  -- Completada - Verde oscuro
            WHEN es.id_estadoentrevista = 4 THEN '#c0392b'  -- Cancelada - Rojo oscuro
            ELSE '#7f8c8d'  -- Otros - Gris oscuro
        END as textColor
    FROM entrevistas e
    JOIN postulaciones p ON e.id_postulacion = p.id_postulacion
    JOIN candidatos c ON p.id_candidato = c.id_candidato
    JOIN vacantes v ON p.id_vacante = v.id_vacante
    JOIN entrevistadores ent ON e.id_entrevistador = ent.id_entrevistador
    JOIN estados_entrevistas es ON e.id_estadoentrevista = es.id_estadoentrevista
    WHERE e.fecha_entrevista IS NOT NULL
    ORDER BY e.fecha_entrevista;
END //

-- Obtener entrevistas del día actual
CREATE PROCEDURE sp_obtener_entrevistas_hoy()
BEGIN
    SELECT 
        e.id_entrevista,
        e.fecha_entrevista,
        c.nom_candidato,
        v.titulo_vacante,
        ent.nom_entrevistador,
        es.nom_estado as estado_entrevista,
        TIME(e.fecha_entrevista) as hora
    FROM entrevistas e
    JOIN postulaciones p ON e.id_postulacion = p.id_postulacion
    JOIN candidatos c ON p.id_candidato = c.id_candidato
    JOIN vacantes v ON p.id_vacante = v.id_vacante
    JOIN entrevistadores ent ON e.id_entrevistador = ent.id_entrevistador
    JOIN estados_entrevistas es ON e.id_estadoentrevista = es.id_estadoentrevista
    WHERE DATE(e.fecha_entrevista) = CURDATE()
    ORDER BY e.fecha_entrevista;
END //

-- Obtener estadísticas del calendario (entrevistas por mes)
CREATE PROCEDURE sp_obtener_estadisticas_calendario()
BEGIN
    SELECT 
        YEAR(fecha_entrevista) as año,
        MONTH(fecha_entrevista) as mes,
        COUNT(*) as total_entrevistas,
        SUM(CASE WHEN id_estadoentrevista = 1 THEN 1 ELSE 0 END) as programadas,
        SUM(CASE WHEN id_estadoentrevista = 2 THEN 1 ELSE 0 END) as en_progreso,
        SUM(CASE WHEN id_estadoentrevista = 3 THEN 1 ELSE 0 END) as completadas,
        SUM(CASE WHEN id_estadoentrevista = 4 THEN 1 ELSE 0 END) as canceladas
    FROM entrevistas
    WHERE fecha_entrevista >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
    GROUP BY YEAR(fecha_entrevista), MONTH(fecha_entrevista)
    ORDER BY año DESC, mes DESC;
END //

-- Obtener próximas entrevistas (próximos 7 días)
CREATE PROCEDURE sp_obtener_proximas_entrevistas()
BEGIN
    SELECT 
        e.id_entrevista,
        e.fecha_entrevista,
        c.nom_candidato,
        v.titulo_vacante,
        ent.nom_entrevistador,
        es.nom_estado as estado_entrevista,
        DATEDIFF(e.fecha_entrevista, CURDATE()) as dias_restantes
    FROM entrevistas e
    JOIN postulaciones p ON e.id_postulacion = p.id_postulacion
    JOIN candidatos c ON p.id_candidato = c.id_candidato
    JOIN vacantes v ON p.id_vacante = v.id_vacante
    JOIN entrevistadores ent ON e.id_entrevistador = ent.id_entrevistador
    JOIN estados_entrevistas es ON e.id_estadoentrevista = es.id_estadoentrevista
    WHERE e.fecha_entrevista >= CURDATE()
    AND e.fecha_entrevista <= DATE_ADD(CURDATE(), INTERVAL 7 DAY)
    AND e.id_estadoentrevista IN (1, 2)  -- Programada o en progreso
    ORDER BY e.fecha_entrevista ASC
    LIMIT 10;
END //

-- Obtener disponibilidad de entrevistadores para una fecha específica
CREATE PROCEDURE sp_obtener_disponibilidad_entrevistadores(IN p_fecha DATE)
BEGIN
    SELECT 
        ent.id_entrevistador,
        ent.nom_entrevistador,
        COUNT(e.id_entrevista) as entrevistas_programadas,
        GROUP_CONCAT(TIME(e.fecha_entrevista) ORDER BY e.fecha_entrevista) as horarios_ocupados
    FROM entrevistadores ent
    LEFT JOIN entrevistas e ON ent.id_entrevistador = e.id_entrevistador 
        AND DATE(e.fecha_entrevista) = p_fecha
        AND e.id_estadoentrevista IN (1, 2)  -- Solo contar programadas y en progreso
    GROUP BY ent.id_entrevistador, ent.nom_entrevistador
    ORDER BY entrevistas_programadas ASC;
END //

DELIMITER ;


DELIMITER //

-- =============================================
-- STORED PROCEDURES PARA ENTREVISTADORES
-- =============================================

-- Obtener todos los entrevistadores con información completa
CREATE PROCEDURE sp_obtener_entrevistadores()
BEGIN
    SELECT e.*, r.nom_rol, 
           COUNT(ent.id_entrevista) as total_entrevistas,
           COUNT(CASE WHEN ent.fecha_entrevista >= CURDATE() THEN 1 END) as entrevistas_pendientes
    FROM entrevistadores e
    LEFT JOIN roles r ON e.id_rol = r.id_rol
    LEFT JOIN entrevistas ent ON e.id_entrevistador = ent.id_entrevistador
    GROUP BY e.id_entrevistador
    ORDER BY e.nom_entrevistador;
END //

-- Obtener todos los roles
CREATE PROCEDURE sp_obtener_roles()
BEGIN
    SELECT * FROM roles ORDER BY nom_rol;
END //

-- Crear entrevistador con validación de email
CREATE PROCEDURE sp_crear_entrevistador(
    IN p_nom_entrevistador VARCHAR(100),
    IN p_email VARCHAR(100),
    IN p_telefono VARCHAR(20),
    IN p_id_rol INT,
    OUT p_resultado VARCHAR(500)
)
BEGIN
    DECLARE v_email_existe INT DEFAULT 0;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_resultado = 'Error al crear entrevistador';
    END;
    
    START TRANSACTION;
    
    -- Verificar si el email ya existe
    SELECT COUNT(*) INTO v_email_existe 
    FROM entrevistadores 
    WHERE email = p_email;
    
    IF v_email_existe > 0 THEN
        SET p_resultado = 'El email ya existe para otro entrevistador';
    ELSE
        -- Insertar el nuevo entrevistador
        INSERT INTO entrevistadores (nom_entrevistador, email, telefono, id_rol)
        VALUES (p_nom_entrevistador, p_email, p_telefono, p_id_rol);
        
        SET p_resultado = 'Entrevistador creado exitosamente';
        COMMIT;
    END IF;
END //

-- Obtener entrevistador por ID con información completa
CREATE PROCEDURE sp_obtener_entrevistador_por_id(IN p_id_entrevistador INT)
BEGIN
    SELECT e.*, r.nom_rol
    FROM entrevistadores e
    LEFT JOIN roles r ON e.id_rol = r.id_rol
    WHERE e.id_entrevistador = p_id_entrevistador;
END //

-- Actualizar entrevistador con validación de email
CREATE PROCEDURE sp_actualizar_entrevistador(
    IN p_id_entrevistador INT,
    IN p_nom_entrevistador VARCHAR(100),
    IN p_email VARCHAR(100),
    IN p_telefono VARCHAR(20),
    IN p_id_rol INT,
    OUT p_resultado VARCHAR(500)
)
BEGIN
    DECLARE v_email_existe INT DEFAULT 0;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_resultado = 'Error al actualizar entrevistador';
    END;
    
    START TRANSACTION;
    
    -- Verificar si el email ya existe en otros entrevistadores
    SELECT COUNT(*) INTO v_email_existe 
    FROM entrevistadores 
    WHERE email = p_email AND id_entrevistador != p_id_entrevistador;
    
    IF v_email_existe > 0 THEN
        SET p_resultado = 'El email ya existe para otro entrevistador';
    ELSE
        -- Actualizar el entrevistador
        UPDATE entrevistadores 
        SET nom_entrevistador = p_nom_entrevistador, 
            email = p_email, 
            telefono = p_telefono, 
            id_rol = p_id_rol
        WHERE id_entrevistador = p_id_entrevistador;
        
        SET p_resultado = 'Entrevistador actualizado exitosamente';
        COMMIT;
    END IF;
END //

-- Eliminar entrevistador con validaciones
CREATE PROCEDURE sp_eliminar_entrevistador(
    IN p_id_entrevistador INT,
    OUT p_resultado VARCHAR(500)
)
BEGIN
    DECLARE v_entrevistas_count INT DEFAULT 0;
    DECLARE v_usuarios_count INT DEFAULT 0;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_resultado = 'Error al eliminar entrevistador';
    END;
    
    START TRANSACTION;
    
    -- Verificar si el entrevistador tiene entrevistas asignadas
    SELECT COUNT(*) INTO v_entrevistas_count 
    FROM entrevistas 
    WHERE id_entrevistador = p_id_entrevistador;
    
    -- Verificar si el entrevistador está asociado a algún usuario
    SELECT COUNT(*) INTO v_usuarios_count 
    FROM usuarios 
    WHERE id_entrevistador = p_id_entrevistador;
    
    IF v_entrevistas_count > 0 THEN
        SET p_resultado = 'No se puede eliminar el entrevistador porque tiene entrevistas asignadas';
    ELSEIF v_usuarios_count > 0 THEN
        SET p_resultado = 'No se puede eliminar el entrevistador porque está asociado a un usuario del sistema';
    ELSE
        -- Eliminar el entrevistador
        DELETE FROM entrevistadores WHERE id_entrevistador = p_id_entrevistador;
        SET p_resultado = 'Entrevistador eliminado exitosamente';
        COMMIT;
    END IF;
END //

-- Obtener estadísticas detalladas de un entrevistador
CREATE PROCEDURE sp_obtener_estadisticas_entrevistador(IN p_id_entrevistador INT)
BEGIN
    SELECT e.*, r.nom_rol,
           COUNT(ent.id_entrevista) as total_entrevistas,
           AVG(ent.puntaje) as puntaje_promedio,
           COUNT(CASE WHEN ent.fecha_entrevista >= CURDATE() THEN 1 END) as entrevistas_pendientes,
           COUNT(CASE WHEN ent.id_estadoentrevista = 3 THEN 1 END) as entrevistas_completadas,
           COUNT(CASE WHEN ent.id_estadoentrevista = 1 THEN 1 END) as entrevistas_programadas,
           COUNT(CASE WHEN ent.id_estadoentrevista = 4 THEN 1 END) as entrevistas_canceladas
    FROM entrevistadores e
    LEFT JOIN roles r ON e.id_rol = r.id_rol
    LEFT JOIN entrevistas ent ON e.id_entrevistador = ent.id_entrevistador
    WHERE e.id_entrevistador = p_id_entrevistador
    GROUP BY e.id_entrevistador;
END //

-- Obtener entrevistas de un entrevistador específico
CREATE PROCEDURE sp_obtener_entrevistas_entrevistador(IN p_id_entrevistador INT)
BEGIN
    SELECT 
        e.id_entrevista,
        e.fecha_entrevista,
        c.nom_candidato,
        v.titulo_vacante,
        es.nom_estado as estado_entrevista,
        es.id_estadoentrevista,
        e.puntaje,
        CASE 
            WHEN e.fecha_entrevista < CURDATE() THEN 'Pasada'
            WHEN e.fecha_entrevista = CURDATE() THEN 'Hoy'
            ELSE 'Futura'
        END as tipo_fecha
    FROM entrevistas e
    JOIN postulaciones p ON e.id_postulacion = p.id_postulacion
    JOIN candidatos c ON p.id_candidato = c.id_candidato
    JOIN vacantes v ON p.id_vacante = v.id_vacante
    JOIN estados_entrevistas es ON e.id_estadoentrevista = es.id_estadoentrevista
    WHERE e.id_entrevistador = p_id_entrevistador
    ORDER BY e.fecha_entrevista DESC
    LIMIT 20;
END //

-- Obtener próximas entrevistas de un entrevistador
CREATE PROCEDURE sp_obtener_proximas_entrevistas_entrevistador(IN p_id_entrevistador INT)
BEGIN
    SELECT 
        e.id_entrevista,
        e.fecha_entrevista,
        c.nom_candidato,
        v.titulo_vacante,
        es.nom_estado as estado_entrevista,
        es.id_estadoentrevista
    FROM entrevistas e
    JOIN postulaciones p ON e.id_postulacion = p.id_postulacion
    JOIN candidatos c ON p.id_candidato = c.id_candidato
    JOIN vacantes v ON p.id_vacante = v.id_vacante
    JOIN estados_entrevistas es ON e.id_estadoentrevista = es.id_estadoentrevista
    WHERE e.id_entrevistador = p_id_entrevistador
    AND e.fecha_entrevista >= CURDATE()
    ORDER BY e.fecha_entrevista ASC
    LIMIT 10;
END //

-- Obtener estadísticas generales de todos los entrevistadores
CREATE PROCEDURE sp_obtener_estadisticas_entrevistadores()
BEGIN
    SELECT 
        e.id_entrevistador,
        e.nom_entrevistador,
        COUNT(ent.id_entrevista) as total_entrevistas,
        AVG(ent.puntaje) as puntaje_promedio,
        COUNT(CASE WHEN ent.fecha_entrevista >= CURDATE() THEN 1 END) as entrevistas_pendientes,
        COUNT(CASE WHEN ent.id_estadoentrevista = 3 THEN 1 END) as entrevistas_completadas,
        COUNT(CASE WHEN ent.id_estadoentrevista = 1 THEN 1 END) as entrevistas_programadas,
        COUNT(CASE WHEN ent.id_estadoentrevista = 4 THEN 1 END) as entrevistas_canceladas,
        r.nom_rol
    FROM entrevistadores e
    LEFT JOIN entrevistas ent ON e.id_entrevistador = ent.id_entrevistador
    LEFT JOIN roles r ON e.id_rol = r.id_rol
    GROUP BY e.id_entrevistador, e.nom_entrevistador, r.nom_rol
    ORDER BY total_entrevistas DESC;
END //

DELIMITER ;

