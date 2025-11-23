/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19  Distrib 10.11.11-MariaDB, for Linux (x86_64)
--
-- Host: localhost    Database: SistemaReclutamiento
-- ------------------------------------------------------
-- Server version	10.11.11-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `audit_candidatos`
--

DROP TABLE IF EXISTS `audit_candidatos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `audit_candidatos` (
  `id_audit` bigint(20) NOT NULL AUTO_INCREMENT,
  `id_candidato` bigint(20) DEFAULT NULL,
  `op` char(1) DEFAULT NULL,
  `changed_by` varchar(120) DEFAULT NULL,
  `changed_at` timestamp NULL DEFAULT current_timestamp(),
  `payload` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`payload`)),
  PRIMARY KEY (`id_audit`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `audit_candidatos`
--

LOCK TABLES `audit_candidatos` WRITE;
/*!40000 ALTER TABLE `audit_candidatos` DISABLE KEYS */;
INSERT INTO `audit_candidatos` VALUES
(1,3,'I','usuario_recludb@%','2025-11-23 02:43:46','{\"identificacion\": \"C003\", \"nombre\": \"Candidato Test\", \"email\": \"test3@test.com\", \"telefono\": \"8133333333\", \"id_fuente\": 1}'),
(2,2,'U','usuario_recludb@%','2025-11-23 02:44:55','{\"identificacion_old\": \"C002\", \"identificacion_new\": \"C002\", \"nombre_old\": \"Candidato SP\", \"nombre_new\": \"Nombre Actualizado\", \"email_old\": \"nuevo@test.com\", \"email_new\": \"nuevo@test.com\", \"telefono_old\": \"8123456789\", \"telefono_new\": \"8123456789\", \"id_fuente_old\": 1, \"id_fuente_new\": 1}'),
(3,3,'D','usuario_recludb@%','2025-11-23 02:48:17','{\"identificacion\": \"C003\", \"nombre\": \"Candidato Test\", \"email\": \"test3@test.com\", \"telefono\": \"8133333333\", \"id_fuente\": 1}'),
(4,4,'I','usuario_recludb@%','2025-11-23 02:54:09','{\"identificacion\": \"C004\", \"nombre\": \"Candidato Trigger\", \"email\": \"trigger@test.com\", \"telefono\": \"8134444444\", \"id_fuente\": 1}'),
(5,6,'I','usuario_recludb@%','2025-11-23 02:55:03','{\"identificacion\": \"C3899\", \"nombre\": \"Candidato Trigger\", \"email\": \"trigger5551@test.com\", \"telefono\": \"8134444444\", \"id_fuente\": 1}');
/*!40000 ALTER TABLE `audit_candidatos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `audit_entrevistas`
--

DROP TABLE IF EXISTS `audit_entrevistas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `audit_entrevistas` (
  `id_audit` bigint(20) NOT NULL AUTO_INCREMENT,
  `id_entrevista` bigint(20) DEFAULT NULL,
  `op` char(1) DEFAULT NULL,
  `changed_by` varchar(120) DEFAULT NULL,
  `changed_at` timestamp NULL DEFAULT current_timestamp(),
  `payload` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`payload`)),
  PRIMARY KEY (`id_audit`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `audit_entrevistas`
--

LOCK TABLES `audit_entrevistas` WRITE;
/*!40000 ALTER TABLE `audit_entrevistas` DISABLE KEYS */;
INSERT INTO `audit_entrevistas` VALUES
(1,3,'I','usuario_recludb@%','2025-11-23 02:44:19','{\"postulacion\": 1, \"fecha\": \"2025-11-24\", \"entrevistador\": 2}'),
(2,1,'U','usuario_recludb@%','2025-11-23 02:44:55','{\"old_puntaje\": 85.5, \"new_puntaje\": 95.0}');
/*!40000 ALTER TABLE `audit_entrevistas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `audit_ofertas`
--

DROP TABLE IF EXISTS `audit_ofertas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `audit_ofertas` (
  `id_audit` bigint(20) NOT NULL AUTO_INCREMENT,
  `id_oferta` bigint(20) DEFAULT NULL,
  `op` char(1) DEFAULT NULL,
  `changed_by` varchar(120) DEFAULT NULL,
  `changed_at` timestamp NULL DEFAULT current_timestamp(),
  `payload` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`payload`)),
  PRIMARY KEY (`id_audit`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `audit_ofertas`
--

LOCK TABLES `audit_ofertas` WRITE;
/*!40000 ALTER TABLE `audit_ofertas` DISABLE KEYS */;
INSERT INTO `audit_ofertas` VALUES
(1,1,'U','usuario_recludb@%','2025-11-23 02:44:29','{\"old_estado\": 2, \"new_estado\": 1, \"old_monto\": 15000.00, \"new_monto\": 20000.00}'),
(3,1,'U','usuario_recludb@%','2025-11-23 02:48:51','{\"old_estado\": 1, \"new_estado\": 2, \"old_monto\": 20000.00, \"new_monto\": 20000.00}'),
(4,1,'U','usuario_recludb@%','2025-11-23 02:53:02','{\"old_estado\": 2, \"new_estado\": 2, \"old_monto\": 20000.00, \"new_monto\": 20000.00}'),
(5,4,'I','usuario_recludb@%','2025-11-23 02:57:56','{\"postulacion\": 5, \"monto\": 30000.00, \"estado\": 1}'),
(6,4,'U','usuario_recludb@%','2025-11-23 02:58:00','{\"old_estado\": 1, \"new_estado\": 2, \"old_monto\": 30000.00, \"new_monto\": 30000.00}');
/*!40000 ALTER TABLE `audit_ofertas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `audit_postulaciones`
--

DROP TABLE IF EXISTS `audit_postulaciones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `audit_postulaciones` (
  `id_audit` bigint(20) NOT NULL AUTO_INCREMENT,
  `id_postulacion` bigint(20) DEFAULT NULL,
  `op` char(1) DEFAULT NULL,
  `changed_by` varchar(120) DEFAULT NULL,
  `changed_at` timestamp NULL DEFAULT current_timestamp(),
  `payload` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`payload`)),
  PRIMARY KEY (`id_audit`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `audit_postulaciones`
--

LOCK TABLES `audit_postulaciones` WRITE;
/*!40000 ALTER TABLE `audit_postulaciones` DISABLE KEYS */;
INSERT INTO `audit_postulaciones` VALUES
(1,1,'I','admin','2025-11-23 02:15:14','{\"detalle\": \"Postulación creada\"}'),
(2,2,'I','usuario_recludb@%','2025-11-23 02:43:46','{\"candidato\": 2, \"vacante\": 2, \"fecha\": \"2025-11-23\", \"etapa\": 1}'),
(3,5,'I','usuario_recludb@%','2025-11-23 02:57:49','{\"candidato\": 6, \"vacante\": 6, \"fecha\": \"2025-11-23\", \"etapa\": 10}');
/*!40000 ALTER TABLE `audit_postulaciones` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `audit_vacantes`
--

DROP TABLE IF EXISTS `audit_vacantes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `audit_vacantes` (
  `id_audit` bigint(20) NOT NULL AUTO_INCREMENT,
  `id_vacante` bigint(20) DEFAULT NULL,
  `op` char(1) DEFAULT NULL,
  `changed_by` varchar(120) DEFAULT NULL,
  `changed_at` timestamp NULL DEFAULT current_timestamp(),
  `payload` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`payload`)),
  PRIMARY KEY (`id_audit`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `audit_vacantes`
--

LOCK TABLES `audit_vacantes` WRITE;
/*!40000 ALTER TABLE `audit_vacantes` DISABLE KEYS */;
INSERT INTO `audit_vacantes` VALUES
(1,3,'I','usuario_recludb@%','2025-11-23 02:43:46','{\"titulo\": \"Vacante Prueba\", \"estado\": 1, \"fecha_creacion\": \"2025-11-23\"}'),
(2,2,'U','usuario_recludb@%','2025-11-23 02:44:55','{\"titulo_old\": \"Vacante SP\", \"titulo_new\": \"Vacante Actualizada 2\", \"estado_old\": 1, \"estado_new\": 1}'),
(3,3,'D','usuario_recludb@%','2025-11-23 02:48:17','{\"titulo\": \"Vacante Prueba\", \"estado\": 1}'),
(4,1,'U','usuario_recludb@%','2025-11-23 02:48:51','{\"titulo_old\": \"Vacante Actualizada\", \"titulo_new\": \"Vacante Actualizada\", \"estado_old\": null, \"estado_new\": null}'),
(5,4,'I','usuario_recludb@%','2025-11-23 02:54:09','{\"titulo\": \"Vacante Trigger\", \"estado\": 1, \"fecha_creacion\": \"2025-11-23\"}'),
(6,6,'I','usuario_recludb@%','2025-11-23 02:56:24','{\"titulo\": \"Vacante Trigger 6061\", \"estado\": 1, \"fecha_creacion\": \"2025-11-23\"}'),
(7,6,'U','usuario_recludb@%','2025-11-23 02:58:00','{\"titulo_old\": \"Vacante Trigger 6061\", \"titulo_new\": \"Vacante Trigger 6061\", \"estado_old\": 1, \"estado_new\": 1}');
/*!40000 ALTER TABLE `audit_vacantes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `candidatos`
--

DROP TABLE IF EXISTS `candidatos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `candidatos` (
  `id_candidato` bigint(20) NOT NULL AUTO_INCREMENT,
  `identificacion` varchar(20) NOT NULL,
  `nom_candidato` varchar(120) NOT NULL,
  `email` varchar(120) NOT NULL,
  `telefono` varchar(15) DEFAULT NULL,
  `fecha_aplicacion` date NOT NULL,
  `id_fuente` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id_candidato`),
  UNIQUE KEY `identificacion` (`identificacion`),
  UNIQUE KEY `email` (`email`),
  KEY `id_fuente` (`id_fuente`),
  CONSTRAINT `candidatos_ibfk_1` FOREIGN KEY (`id_fuente`) REFERENCES `fuentes` (`id_fuente`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `candidatos`
--

LOCK TABLES `candidatos` WRITE;
/*!40000 ALTER TABLE `candidatos` DISABLE KEYS */;
INSERT INTO `candidatos` VALUES
(1,'C001-A','Candidato Modificado','cand@test.com','8111111111','2025-11-23',1),
(2,'C002','Nombre Actualizado','nuevo@test.com','8123456789','2025-11-23',1),
(4,'C004','Candidato Trigger','trigger@test.com','8134444444','2025-11-23',1),
(6,'C3899','Candidato Trigger','trigger5551@test.com','8134444444','2025-11-23',1);
/*!40000 ALTER TABLE `candidatos` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb3 */ ;
/*!50003 SET character_set_results = utf8mb3 */ ;
/*!50003 SET collation_connection  = utf8mb3_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`usuario_recludb`@`%`*/ /*!50003 TRIGGER deduplicacionCandidatoBI
BEFORE INSERT ON candidatos
FOR EACH ROW
BEGIN
  IF (SELECT COUNT(*) FROM candidatos WHERE email = NEW.email) > 0 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'ERROR: El email ya existe para otro candidato.';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb3 */ ;
/*!50003 SET character_set_results = utf8mb3 */ ;
/*!50003 SET collation_connection  = utf8mb3_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`usuario_recludb`@`%`*/ /*!50003 TRIGGER candidatoAIUD_I
AFTER INSERT ON candidatos
FOR EACH ROW
BEGIN
  INSERT INTO audit_candidatos(id_candidato, op, changed_by, payload)
  VALUES (
    NEW.id_candidato,
    'I',
    CURRENT_USER(),
    JSON_OBJECT(
      'identificacion', NEW.identificacion,
      'nombre', NEW.nom_candidato,
      'email', NEW.email,
      'telefono', NEW.telefono,
      'id_fuente', NEW.id_fuente
    )
  );
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb3 */ ;
/*!50003 SET character_set_results = utf8mb3 */ ;
/*!50003 SET collation_connection  = utf8mb3_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`usuario_recludb`@`%`*/ /*!50003 TRIGGER candidatoAIUD_U
AFTER UPDATE ON candidatos
FOR EACH ROW
BEGIN
  INSERT INTO audit_candidatos(id_candidato, op, changed_by, payload)
  VALUES (
    NEW.id_candidato,
    'U',
    CURRENT_USER(),
    JSON_OBJECT(
      'identificacion_old', OLD.identificacion,
      'identificacion_new', NEW.identificacion,
      'nombre_old', OLD.nom_candidato,
      'nombre_new', NEW.nom_candidato,
      'email_old', OLD.email,
      'email_new', NEW.email,
      'telefono_old', OLD.telefono,
      'telefono_new', NEW.telefono,
      'id_fuente_old', OLD.id_fuente,
      'id_fuente_new', NEW.id_fuente
    )
  );
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb3 */ ;
/*!50003 SET character_set_results = utf8mb3 */ ;
/*!50003 SET collation_connection  = utf8mb3_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`usuario_recludb`@`%`*/ /*!50003 TRIGGER candidatoAIUD_D
AFTER DELETE ON candidatos
FOR EACH ROW
BEGIN
  INSERT INTO audit_candidatos(id_candidato, op, changed_by, payload)
  VALUES (
    OLD.id_candidato,
    'D',
    CURRENT_USER(),
    JSON_OBJECT(
      'identificacion', OLD.identificacion,
      'nombre', OLD.nom_candidato,
      'email', OLD.email,
      'telefono', OLD.telefono,
      'id_fuente', OLD.id_fuente
    )
  );
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `departamentos`
--

DROP TABLE IF EXISTS `departamentos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `departamentos` (
  `id_departamento` bigint(20) NOT NULL AUTO_INCREMENT,
  `nom_departamento` varchar(80) NOT NULL,
  PRIMARY KEY (`id_departamento`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `departamentos`
--

LOCK TABLES `departamentos` WRITE;
/*!40000 ALTER TABLE `departamentos` DISABLE KEYS */;
INSERT INTO `departamentos` VALUES
(1,'Pruebas');
/*!40000 ALTER TABLE `departamentos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `entrevistadores`
--

DROP TABLE IF EXISTS `entrevistadores`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `entrevistadores` (
  `id_entrevistador` bigint(20) NOT NULL AUTO_INCREMENT,
  `nom_entrevistador` varchar(120) NOT NULL,
  `id_rol` bigint(20) NOT NULL,
  `telefono` varchar(15) DEFAULT NULL,
  `email` varchar(120) NOT NULL,
  PRIMARY KEY (`id_entrevistador`),
  UNIQUE KEY `email` (`email`),
  KEY `id_rol` (`id_rol`),
  CONSTRAINT `entrevistadores_ibfk_1` FOREIGN KEY (`id_rol`) REFERENCES `roles` (`id_rol`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `entrevistadores`
--

LOCK TABLES `entrevistadores` WRITE;
/*!40000 ALTER TABLE `entrevistadores` DISABLE KEYS */;
INSERT INTO `entrevistadores` VALUES
(1,'Entrevistador Prueba',1,'8000000000','entre@test.com'),
(2,'Ana Martínez',1,'8111111111','ana@test.com');
/*!40000 ALTER TABLE `entrevistadores` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `entrevistas`
--

DROP TABLE IF EXISTS `entrevistas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `entrevistas` (
  `id_entrevista` bigint(20) NOT NULL AUTO_INCREMENT,
  `id_postulacion` bigint(20) NOT NULL,
  `fecha_entrevista` date NOT NULL,
  `puntaje` decimal(4,1) DEFAULT NULL,
  `notas` text DEFAULT NULL,
  `id_estadoentrevista` bigint(20) DEFAULT NULL,
  `id_entrevistador` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id_entrevista`),
  UNIQUE KEY `uq_entrevista` (`id_postulacion`,`fecha_entrevista`),
  KEY `id_estadoentrevista` (`id_estadoentrevista`),
  KEY `id_entrevistador` (`id_entrevistador`),
  CONSTRAINT `entrevistas_ibfk_1` FOREIGN KEY (`id_postulacion`) REFERENCES `postulaciones` (`id_postulacion`),
  CONSTRAINT `entrevistas_ibfk_2` FOREIGN KEY (`id_estadoentrevista`) REFERENCES `estados_entrevistas` (`id_estadoentrevista`),
  CONSTRAINT `entrevistas_ibfk_3` FOREIGN KEY (`id_entrevistador`) REFERENCES `entrevistadores` (`id_entrevistador`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `entrevistas`
--

LOCK TABLES `entrevistas` WRITE;
/*!40000 ALTER TABLE `entrevistas` DISABLE KEYS */;
INSERT INTO `entrevistas` VALUES
(1,1,'2025-11-23',95.0,'Buen desempeño',NULL,1),
(3,1,'2025-11-24',85.0,NULL,NULL,2);
/*!40000 ALTER TABLE `entrevistas` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb3 */ ;
/*!50003 SET character_set_results = utf8mb3 */ ;
/*!50003 SET collation_connection  = utf8mb3_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`usuario_recludb`@`%`*/ /*!50003 TRIGGER entrevistaAIUD_I
AFTER INSERT ON entrevistas
FOR EACH ROW
BEGIN
  INSERT INTO audit_entrevistas(id_entrevista, op, changed_by, payload)
  VALUES (
    NEW.id_entrevista,
    'I',
    CURRENT_USER(),
    JSON_OBJECT(
      'postulacion', NEW.id_postulacion,
      'fecha', NEW.fecha_entrevista,
      'entrevistador', NEW.id_entrevistador
    )
  );
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb3 */ ;
/*!50003 SET character_set_results = utf8mb3 */ ;
/*!50003 SET collation_connection  = utf8mb3_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`usuario_recludb`@`%`*/ /*!50003 TRIGGER entrevistaAIUD_U
AFTER UPDATE ON entrevistas
FOR EACH ROW
BEGIN
  INSERT INTO audit_entrevistas(id_entrevista, op, changed_by, payload)
  VALUES (
    NEW.id_entrevista,
    'U',
    CURRENT_USER(),
    JSON_OBJECT(
      'old_puntaje', OLD.puntaje,
      'new_puntaje', NEW.puntaje
    )
  );
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb3 */ ;
/*!50003 SET character_set_results = utf8mb3 */ ;
/*!50003 SET collation_connection  = utf8mb3_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`usuario_recludb`@`%`*/ /*!50003 TRIGGER entrevistaAIUD_D
AFTER DELETE ON entrevistas
FOR EACH ROW
BEGIN
  INSERT INTO audit_entrevistas(id_entrevista, op, changed_by, payload)
  VALUES (
    OLD.id_entrevista,
    'D',
    CURRENT_USER(),
    JSON_OBJECT(
      'postulacion', OLD.id_postulacion
    )
  );
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `estados_entrevistas`
--

DROP TABLE IF EXISTS `estados_entrevistas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `estados_entrevistas` (
  `id_estadoentrevista` bigint(20) NOT NULL AUTO_INCREMENT,
  `nom_estado` varchar(50) NOT NULL,
  `desc_estado` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id_estadoentrevista`),
  UNIQUE KEY `nom_estado` (`nom_estado`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `estados_entrevistas`
--

LOCK TABLES `estados_entrevistas` WRITE;
/*!40000 ALTER TABLE `estados_entrevistas` DISABLE KEYS */;
INSERT INTO `estados_entrevistas` VALUES
(1,'Programada',NULL);
/*!40000 ALTER TABLE `estados_entrevistas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `estados_ofertas`
--

DROP TABLE IF EXISTS `estados_ofertas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `estados_ofertas` (
  `id_estadoferta` bigint(20) NOT NULL AUTO_INCREMENT,
  `nom_estado` varchar(50) NOT NULL,
  `desc_estado` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id_estadoferta`),
  UNIQUE KEY `nom_estado` (`nom_estado`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `estados_ofertas`
--

LOCK TABLES `estados_ofertas` WRITE;
/*!40000 ALTER TABLE `estados_ofertas` DISABLE KEYS */;
INSERT INTO `estados_ofertas` VALUES
(1,'Emitida',NULL),
(2,'Aceptada',NULL),
(3,'Rechazada',NULL);
/*!40000 ALTER TABLE `estados_ofertas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `estados_vacantes`
--

DROP TABLE IF EXISTS `estados_vacantes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `estados_vacantes` (
  `id_estadovacante` bigint(20) NOT NULL AUTO_INCREMENT,
  `nom_estado` varchar(50) NOT NULL,
  `desc_estado` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id_estadovacante`),
  UNIQUE KEY `nom_estado` (`nom_estado`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `estados_vacantes`
--

LOCK TABLES `estados_vacantes` WRITE;
/*!40000 ALTER TABLE `estados_vacantes` DISABLE KEYS */;
INSERT INTO `estados_vacantes` VALUES
(1,'Abierta',NULL);
/*!40000 ALTER TABLE `estados_vacantes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `etapas`
--

DROP TABLE IF EXISTS `etapas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `etapas` (
  `id_etapa` bigint(20) NOT NULL AUTO_INCREMENT,
  `nom_etapa` varchar(50) NOT NULL,
  `desc_etapa` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id_etapa`),
  UNIQUE KEY `nom_etapa` (`nom_etapa`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `etapas`
--

LOCK TABLES `etapas` WRITE;
/*!40000 ALTER TABLE `etapas` DISABLE KEYS */;
INSERT INTO `etapas` VALUES
(1,'Entrevista Inicial',NULL),
(2,'Inicial',NULL),
(3,'Postulacion',NULL),
(9,'Entrevista',NULL),
(10,'Oferta',NULL),
(11,'Contratado',NULL),
(12,'Rechazado',NULL);
/*!40000 ALTER TABLE `etapas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `fuentes`
--

DROP TABLE IF EXISTS `fuentes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `fuentes` (
  `id_fuente` bigint(20) NOT NULL AUTO_INCREMENT,
  `nom_fuente` varchar(80) NOT NULL,
  `desc_fuente` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id_fuente`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `fuentes`
--

LOCK TABLES `fuentes` WRITE;
/*!40000 ALTER TABLE `fuentes` DISABLE KEYS */;
INSERT INTO `fuentes` VALUES
(1,'Prueba',NULL);
/*!40000 ALTER TABLE `fuentes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ofertas`
--

DROP TABLE IF EXISTS `ofertas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `ofertas` (
  `id_oferta` bigint(20) NOT NULL AUTO_INCREMENT,
  `id_postulacion` bigint(20) NOT NULL,
  `monto_oferta` decimal(12,2) NOT NULL,
  `id_estadoferta` bigint(20) NOT NULL,
  `fecha_decision` date DEFAULT NULL,
  PRIMARY KEY (`id_oferta`),
  UNIQUE KEY `uq_oferta_postulacion` (`id_postulacion`),
  KEY `id_estadoferta` (`id_estadoferta`),
  CONSTRAINT `ofertas_ibfk_1` FOREIGN KEY (`id_postulacion`) REFERENCES `postulaciones` (`id_postulacion`),
  CONSTRAINT `ofertas_ibfk_2` FOREIGN KEY (`id_estadoferta`) REFERENCES `estados_ofertas` (`id_estadoferta`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ofertas`
--

LOCK TABLES `ofertas` WRITE;
/*!40000 ALTER TABLE `ofertas` DISABLE KEYS */;
INSERT INTO `ofertas` VALUES
(1,1,20000.00,2,'2025-11-23'),
(4,5,30000.00,2,NULL);
/*!40000 ALTER TABLE `ofertas` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb3 */ ;
/*!50003 SET character_set_results = utf8mb3 */ ;
/*!50003 SET collation_connection  = utf8mb3_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`usuario_recludb`@`%`*/ /*!50003 TRIGGER ofertaGuardrailsBI
BEFORE INSERT ON ofertas
FOR EACH ROW
BEGIN
  DECLARE etapa_actual BIGINT;

  SELECT id_etapa INTO etapa_actual
  FROM postulaciones
  WHERE id_postulacion = NEW.id_postulacion;

  IF etapa_actual < 5 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'ERROR: Solo se puede emitir oferta a candidatos finalistas.';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb3 */ ;
/*!50003 SET character_set_results = utf8mb3 */ ;
/*!50003 SET collation_connection  = utf8mb3_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`usuario_recludb`@`%`*/ /*!50003 TRIGGER ofertaAIUD_I
AFTER INSERT ON ofertas
FOR EACH ROW
BEGIN
  INSERT INTO audit_ofertas(id_oferta, op, changed_by, payload)
  VALUES (
    NEW.id_oferta,
    'I',
    CURRENT_USER(),
    JSON_OBJECT(
      'postulacion', NEW.id_postulacion,
      'monto', NEW.monto_oferta,
      'estado', NEW.id_estadoferta
    )
  );
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb3 */ ;
/*!50003 SET character_set_results = utf8mb3 */ ;
/*!50003 SET collation_connection  = utf8mb3_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`usuario_recludb`@`%`*/ /*!50003 TRIGGER ofertaAIUD_U
AFTER UPDATE ON ofertas
FOR EACH ROW
BEGIN
  INSERT INTO audit_ofertas(id_oferta, op, changed_by, payload)
  VALUES (
    NEW.id_oferta,
    'U',
    CURRENT_USER(),
    JSON_OBJECT(
      'old_estado', OLD.id_estadoferta,
      'new_estado', NEW.id_estadoferta,
      'old_monto', OLD.monto_oferta,
      'new_monto', NEW.monto_oferta
    )
  );
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb3 */ ;
/*!50003 SET character_set_results = utf8mb3 */ ;
/*!50003 SET collation_connection  = utf8mb3_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`usuario_recludb`@`%`*/ /*!50003 TRIGGER kpiTimeToFillAIoferta
AFTER UPDATE ON ofertas
FOR EACH ROW
BEGIN
  IF NEW.id_estadoferta = 2 AND OLD.id_estadoferta <> 2 THEN
    UPDATE vacantes v
    JOIN postulaciones p ON p.id_vacante = v.id_vacante
    SET v.time_to_fill = DATEDIFF(CURRENT_DATE(), v.fecha_creacion)
    WHERE p.id_postulacion = NEW.id_postulacion;
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb3 */ ;
/*!50003 SET character_set_results = utf8mb3 */ ;
/*!50003 SET collation_connection  = utf8mb3_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`usuario_recludb`@`%`*/ /*!50003 TRIGGER ofertaAIUD_D
AFTER DELETE ON ofertas
FOR EACH ROW
BEGIN
  INSERT INTO audit_ofertas(id_oferta, op, changed_by, payload)
  VALUES (
    OLD.id_oferta,
    'D',
    CURRENT_USER(),
    JSON_OBJECT(
      'postulacion', OLD.id_postulacion
    )
  );
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `postulaciones`
--

DROP TABLE IF EXISTS `postulaciones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `postulaciones` (
  `id_postulacion` bigint(20) NOT NULL AUTO_INCREMENT,
  `id_candidato` bigint(20) NOT NULL,
  `id_vacante` bigint(20) NOT NULL,
  `fecha_postula` date NOT NULL,
  `id_etapa` bigint(20) NOT NULL,
  PRIMARY KEY (`id_postulacion`),
  UNIQUE KEY `uq_postulacion` (`id_candidato`,`id_vacante`),
  KEY `id_vacante` (`id_vacante`),
  KEY `id_etapa` (`id_etapa`),
  CONSTRAINT `postulaciones_ibfk_1` FOREIGN KEY (`id_candidato`) REFERENCES `candidatos` (`id_candidato`),
  CONSTRAINT `postulaciones_ibfk_2` FOREIGN KEY (`id_vacante`) REFERENCES `vacantes` (`id_vacante`),
  CONSTRAINT `postulaciones_ibfk_3` FOREIGN KEY (`id_etapa`) REFERENCES `etapas` (`id_etapa`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `postulaciones`
--

LOCK TABLES `postulaciones` WRITE;
/*!40000 ALTER TABLE `postulaciones` DISABLE KEYS */;
INSERT INTO `postulaciones` VALUES
(1,1,1,'2025-11-23',11),
(2,2,2,'2025-11-23',1),
(5,6,6,'2025-11-23',10);
/*!40000 ALTER TABLE `postulaciones` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb3 */ ;
/*!50003 SET character_set_results = utf8mb3 */ ;
/*!50003 SET collation_connection  = utf8mb3_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`usuario_recludb`@`%`*/ /*!50003 TRIGGER postulacionAIUD_I
AFTER INSERT ON postulaciones
FOR EACH ROW
BEGIN
  INSERT INTO audit_postulaciones(id_postulacion, op, changed_by, payload)
  VALUES (
    NEW.id_postulacion,
    'I',
    CURRENT_USER(),
    JSON_OBJECT(
      'candidato', NEW.id_candidato,
      'vacante', NEW.id_vacante,
      'fecha', NEW.fecha_postula,
      'etapa', NEW.id_etapa
    )
  );
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb3 */ ;
/*!50003 SET character_set_results = utf8mb3 */ ;
/*!50003 SET collation_connection  = utf8mb3_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`usuario_recludb`@`%`*/ /*!50003 TRIGGER postulacionTransicionBU
BEFORE UPDATE ON postulaciones
FOR EACH ROW
BEGIN
  IF NEW.id_etapa < OLD.id_etapa THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'ERROR: No se permite retroceder de etapa.';
  END IF;

  IF NEW.id_etapa > OLD.id_etapa + 1 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'ERROR: Transición de etapa inválida (salto no permitido).';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb3 */ ;
/*!50003 SET character_set_results = utf8mb3 */ ;
/*!50003 SET collation_connection  = utf8mb3_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`usuario_recludb`@`%`*/ /*!50003 TRIGGER postulacionAIUD_U
AFTER UPDATE ON postulaciones
FOR EACH ROW
BEGIN
  INSERT INTO audit_postulaciones(id_postulacion, op, changed_by, payload)
  VALUES (
    NEW.id_postulacion,
    'U',
    CURRENT_USER(),
    JSON_OBJECT(
      'old_etapa', OLD.id_etapa,
      'new_etapa', NEW.id_etapa
    )
  );
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb3 */ ;
/*!50003 SET character_set_results = utf8mb3 */ ;
/*!50003 SET collation_connection  = utf8mb3_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`usuario_recludb`@`%`*/ /*!50003 TRIGGER postulacionAIUD_D
AFTER DELETE ON postulaciones
FOR EACH ROW
BEGIN
  INSERT INTO audit_postulaciones(id_postulacion, op, changed_by, payload)
  VALUES (
    OLD.id_postulacion,
    'D',
    CURRENT_USER(),
    JSON_OBJECT(
      'candidato', OLD.id_candidato,
      'vacante', OLD.id_vacante
    )
  );

END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `roles`
--

DROP TABLE IF EXISTS `roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `roles` (
  `id_rol` bigint(20) NOT NULL AUTO_INCREMENT,
  `nom_rol` varchar(50) NOT NULL,
  `desc_rol` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id_rol`),
  UNIQUE KEY `nom_rol` (`nom_rol`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `roles`
--

LOCK TABLES `roles` WRITE;
/*!40000 ALTER TABLE `roles` DISABLE KEYS */;
INSERT INTO `roles` VALUES
(1,'Entrevistador',NULL);
/*!40000 ALTER TABLE `roles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `roles_sistema`
--

DROP TABLE IF EXISTS `roles_sistema`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `roles_sistema` (
  `id_rolsistema` bigint(20) NOT NULL AUTO_INCREMENT,
  `nom_rol` varchar(50) NOT NULL,
  `desc_rol` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id_rolsistema`),
  UNIQUE KEY `nom_rol` (`nom_rol`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `roles_sistema`
--

LOCK TABLES `roles_sistema` WRITE;
/*!40000 ALTER TABLE `roles_sistema` DISABLE KEYS */;
INSERT INTO `roles_sistema` VALUES
(1,'Admin',NULL),
(2,'Reclutador',NULL),
(3,'Entrevistador',NULL);
/*!40000 ALTER TABLE `roles_sistema` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios` (
  `id_usuario` bigint(20) NOT NULL AUTO_INCREMENT,
  `username` varchar(80) NOT NULL,
  `hashed_pass` varchar(255) NOT NULL,
  `email` varchar(120) NOT NULL,
  `id_rolsistema` bigint(20) NOT NULL,
  `id_entrevistador` bigint(20) DEFAULT NULL,
  `activo` tinyint(4) DEFAULT 1,
  `creado_en` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_usuario`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`),
  KEY `id_rolsistema` (`id_rolsistema`),
  KEY `id_entrevistador` (`id_entrevistador`),
  CONSTRAINT `usuarios_ibfk_1` FOREIGN KEY (`id_rolsistema`) REFERENCES `roles_sistema` (`id_rolsistema`),
  CONSTRAINT `usuarios_ibfk_2` FOREIGN KEY (`id_entrevistador`) REFERENCES `entrevistadores` (`id_entrevistador`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuarios`
--

LOCK TABLES `usuarios` WRITE;
/*!40000 ALTER TABLE `usuarios` DISABLE KEYS */;
INSERT INTO `usuarios` VALUES
(1,'admin','1234','admin@test.com',1,NULL,1,'2025-11-23 02:11:35');
/*!40000 ALTER TABLE `usuarios` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vacantes`
--

DROP TABLE IF EXISTS `vacantes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `vacantes` (
  `id_vacante` bigint(20) NOT NULL AUTO_INCREMENT,
  `titulo_vacante` varchar(150) NOT NULL,
  `desc_vacante` text DEFAULT NULL,
  `id_departamento` bigint(20) DEFAULT NULL,
  `fecha_creacion` date NOT NULL,
  `id_estadovacante` bigint(20) DEFAULT NULL,
  `time_to_fill` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_vacante`),
  UNIQUE KEY `uk_vacante_departamento` (`titulo_vacante`,`id_departamento`),
  KEY `id_departamento` (`id_departamento`),
  KEY `id_estadovacante` (`id_estadovacante`),
  CONSTRAINT `vacantes_ibfk_1` FOREIGN KEY (`id_departamento`) REFERENCES `departamentos` (`id_departamento`),
  CONSTRAINT `vacantes_ibfk_2` FOREIGN KEY (`id_estadovacante`) REFERENCES `estados_vacantes` (`id_estadovacante`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `vacantes`
--

LOCK TABLES `vacantes` WRITE;
/*!40000 ALTER TABLE `vacantes` DISABLE KEYS */;
INSERT INTO `vacantes` VALUES
(1,'Vacante Actualizada','Descripción nueva desde SP',1,'2025-11-23',NULL,0),
(2,'Vacante Actualizada 2','Vacante creada con stored procedure',1,'2025-11-23',1,NULL),
(4,'Vacante Trigger','Prueba trigger time_to_fill',1,'2025-11-23',1,NULL),
(6,'Vacante Trigger 6061','Prueba trigger time_to_fill',1,'2025-11-23',1,0);
/*!40000 ALTER TABLE `vacantes` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb3 */ ;
/*!50003 SET character_set_results = utf8mb3 */ ;
/*!50003 SET collation_connection  = utf8mb3_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`usuario_recludb`@`%`*/ /*!50003 TRIGGER vacanteAIUD_I
AFTER INSERT ON vacantes
FOR EACH ROW
BEGIN
  INSERT INTO audit_vacantes(id_vacante, op, changed_by, payload)
  VALUES (
    NEW.id_vacante,
    'I',
    CURRENT_USER(),
    JSON_OBJECT(
      'titulo', NEW.titulo_vacante,
      'estado', NEW.id_estadovacante,
      'fecha_creacion', NEW.fecha_creacion
    )
  );
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb3 */ ;
/*!50003 SET character_set_results = utf8mb3 */ ;
/*!50003 SET collation_connection  = utf8mb3_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`usuario_recludb`@`%`*/ /*!50003 TRIGGER vacanteAIUD_U
AFTER UPDATE ON vacantes
FOR EACH ROW
BEGIN
  INSERT INTO audit_vacantes(id_vacante, op, changed_by, payload)
  VALUES (
    NEW.id_vacante,
    'U',
    CURRENT_USER(),
    JSON_OBJECT(
      'titulo_old', OLD.titulo_vacante,
      'titulo_new', NEW.titulo_vacante,
      'estado_old', OLD.id_estadovacante,
      'estado_new', NEW.id_estadovacante
    )
  );
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb3 */ ;
/*!50003 SET character_set_results = utf8mb3 */ ;
/*!50003 SET collation_connection  = utf8mb3_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`usuario_recludb`@`%`*/ /*!50003 TRIGGER vacanteAIUD_D
AFTER DELETE ON vacantes
FOR EACH ROW
BEGIN
  INSERT INTO audit_vacantes(id_vacante, op, changed_by, payload)
  VALUES (
    OLD.id_vacante,
    'D',
    CURRENT_USER(),
    JSON_OBJECT(
      'titulo', OLD.titulo_vacante,
      'estado', OLD.id_estadovacante
    )
  );
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-11-23  3:02:46
