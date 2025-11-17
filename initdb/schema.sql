-- =======================================
-- Crear base de datos, usuario y privilegios
-- =======================================

-- Crear la base de datos
CREATE DATABASE IF NOT EXISTS sistema_reclutamiento
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- Crear el usuario
CREATE USER IF NOT EXISTS 'usuario_recludb'@'%' IDENTIFIED BY '666';

-- Dar todos los privilegios sobre la base de datos al usuario
GRANT ALL PRIVILEGES ON SistemaReclutamiento.* TO 'usuario_recludb'@'%';

-- Aplicar cambios de privilegios
FLUSH PRIVILEGES;

-- Seleccionar la base de datos para usarla
USE sistema_reclutamiento;

-- =======================================
-- ==========================
-- Tablas principales
-- ==========================

CREATE TABLE fuentes (
  id_fuente BIGINT PRIMARY KEY AUTO_INCREMENT,
  nom_fuente TEXT NOT NULL,
  desc_fuente TEXT
);

CREATE TABLE roles (
  id_rol BIGINT PRIMARY KEY AUTO_INCREMENT,
  nom_rol TEXT NOT NULL UNIQUE,
  desc_rol TEXT
);

CREATE TABLE departamentos (
  id_departamento BIGINT PRIMARY KEY AUTO_INCREMENT,
  nom_departamento TEXT NOT NULL
);

CREATE TABLE estados_vacantes (
  id_estadovacante BIGINT PRIMARY KEY AUTO_INCREMENT,
  nom_estado TEXT NOT NULL UNIQUE,
  desc_estado TEXT
);

CREATE TABLE estados_ofertas (
  id_estadoferta BIGINT PRIMARY KEY AUTO_INCREMENT,
  nom_estado TEXT NOT NULL UNIQUE,
  desc_estado TEXT
);

CREATE TABLE estados_entrevistas (
  id_estadoentrevista BIGINT PRIMARY KEY AUTO_INCREMENT,
  nom_estado TEXT NOT NULL UNIQUE,
  desc_estado TEXT
);

CREATE TABLE etapas (
  id_etapa BIGINT PRIMARY KEY AUTO_INCREMENT,
  nom_etapa TEXT NOT NULL UNIQUE,
  desc_etapa TEXT
);

CREATE TABLE candidatos (
  id_candidato BIGINT PRIMARY KEY AUTO_INCREMENT,
  nom_candidato TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  telefono TEXT,
  fecha_aplicacion DATE NOT NULL,
  id_fuente BIGINT,
  FOREIGN KEY (id_fuente) REFERENCES fuentes(id_fuente)
);

CREATE TABLE entrevistadores (
  id_entrevistador BIGINT PRIMARY KEY AUTO_INCREMENT,
  nom_entrevistador TEXT NOT NULL,
  id_rol BIGINT NOT NULL,
  telefono TEXT,
  email TEXT NOT NULL UNIQUE,
  hashed_pass TEXT,
  FOREIGN KEY (id_rol) REFERENCES roles(id_rol)
);

CREATE TABLE vacantes (
  id_vacante BIGINT PRIMARY KEY AUTO_INCREMENT,
  titulo_vacante TEXT NOT NULL,
  desc_vacante TEXT,
  id_departamento BIGINT,
  fecha_creacion DATE NOT NULL,
  id_estadovacante BIGINT,
  FOREIGN KEY (id_departamento) REFERENCES departamentos(id_departamento),
  FOREIGN KEY (id_estadovacante) REFERENCES estados_vacantes(id_estadovacante)
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
  puntaje INT,
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
-- Auditorías
-- ==========================

CREATE TABLE audit_candidatos (
  id_audit BIGINT PRIMARY KEY AUTO_INCREMENT,
  id_candidato BIGINT,
  op CHAR(1),
  changed_by TEXT,
  changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  payload JSON,
  FOREIGN KEY (id_candidato) REFERENCES candidatos(id_candidato)
);

CREATE TABLE audit_vacantes (
  id_audit BIGINT PRIMARY KEY AUTO_INCREMENT,
  id_vacante BIGINT,
  op CHAR(1),
  changed_by TEXT,
  changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  payload JSON,
  FOREIGN KEY (id_vacante) REFERENCES vacantes(id_vacante)
);

CREATE TABLE audit_postulaciones (
  id_audit BIGINT PRIMARY KEY AUTO_INCREMENT,
  id_postulacion BIGINT,
  op CHAR(1),
  changed_by TEXT,
  changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  payload JSON,
  FOREIGN KEY (id_postulacion) REFERENCES postulaciones(id_postulacion)
);

CREATE TABLE audit_entrevistas (
  id_audit BIGINT PRIMARY KEY AUTO_INCREMENT,
  id_entrevista BIGINT,
  op CHAR(1),
  changed_by TEXT,
  changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  payload JSON,
  FOREIGN KEY (id_entrevista) REFERENCES entrevistas(id_entrevista)
);

CREATE TABLE audit_ofertas (
  id_audit BIGINT PRIMARY KEY AUTO_INCREMENT,
  id_oferta BIGINT,
  op CHAR(1),
  changed_by TEXT,
  changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  payload JSON,
  FOREIGN KEY (id_oferta) REFERENCES ofertas(id_oferta)
);

