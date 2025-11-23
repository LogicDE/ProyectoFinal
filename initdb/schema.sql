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
