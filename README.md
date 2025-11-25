# Sistema de Reclutamiento con Docker

Este proyecto utiliza **Docker** y **Docker Compose** para levantar un entorno de desarrollo que incluye una base de datos **MariaDB** y una aplicación web **Flask**. A continuación, te explicamos los pasos para ejecutar el proyecto.

## Requisitos previos

Asegúrate de tener instalados los siguientes programas en tu máquina:

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/)

## Pasos para ejecutar el proyecto

1. **Levantar los contenedores**:

   Abre una terminal y navega hasta el directorio del proyecto. Luego ejecuta:

   ```bash
   docker-compose up
Esto levantará los contenedores de la base de datos y la aplicación web.

Subir el dump de la base de datos:

Una vez que el contenedor de la base de datos esté corriendo, debes subir el dump a la instancia de MariaDB.

Copia los archivos de la base de datos en la carpeta ./initdb/ dentro de tu proyecto:

procedures.sql

datosejemplo.sql

schema.sql

schemabaseperonodump.sql

Ejemplo:

pgsql
Copy code
C:\Users\themo\OneDrive\Documents\ProyectoFinal\initdb\procedures.sql
C:\Users\themo\OneDrive\Documents\ProyectoFinal\initdb\datosejemplo.sql
C:\Users\themo\OneDrive\Documents\ProyectoFinal\initdb\schema.sql
C:\Users\themo\OneDrive\Documents\ProyectoFinal\schemabaseperonodump.sql
Reconstruir y levantar los contenedores en segundo plano:

Después de haber subido los archivos, ejecuta:

bash
Copy code
docker-compose up -d --build
Este comando asegura que los contenedores se reconstruyan y se ejecuten en segundo plano.

Acceder a la aplicación:

Una vez que los contenedores estén corriendo, puedes acceder a la aplicación web a través de tu navegador. Simplemente abre tu navegador y ve a:

Local: http://localhost:5000

Usando la IP de la máquina: http://<tu_ip_local>:5000

La aplicación debería estar disponible y funcionando.

Estructura del Docker Compose
A continuación se describe la configuración de docker-compose.yml:

yaml
Copy code
version: '3.9'

services:
  db:
    image: mariadb:11
    container_name: reclutamiento-db
    restart: always
    environment:
      MYSQL_ROOT_PASSWORD: rootpassword
      MYSQL_DATABASE: sistema_reclutamiento
      MYSQL_USER: usuario_recludb
      MYSQL_PASSWORD: 666
    ports:
      - "3306:3306"
    volumes:
      - ./initdb:/docker-entrypoint-initdb.d

  web:
    build: .
    container_name: reclutamiento-flask
    restart: always
    ports:
      - "5000:5000"
    environment:
      FLASK_APP: app.py
      FLASK_ENV: development
      DB_HOST: db
      DB_USER: usuario_recludb
      DB_PASSWORD: 666
      DB_NAME: sistema_reclutamiento
    depends_on:
      - db
    volumes:
      - .:/app
Explicación de los servicios:
db: Este servicio configura la base de datos MariaDB y expone el puerto 3306. Se inicializa con los archivos de base de datos ubicados en ./initdb/.

web: Este servicio configura la aplicación web Flask y expone el puerto 5000. Se conecta a la base de datos utilizando las variables de entorno definidas.

Archivos en ./initdb/
procedures.sql: Contiene las funciones y procedimientos almacenados para la base de datos.

datosejemplo.sql: Contiene datos de ejemplo que se insertarán en las tablas de la base de datos.

schema.sql: Define la estructura de las tablas en la base de datos.

schemabaseperonodump.sql: Versión del esquema sin los datos, ideal para cuando necesitas solo la estructura sin insertar datos.

Consideraciones
Asegúrate de que tu máquina tenga suficiente memoria y recursos para ejecutar Docker, especialmente si estás utilizando una base de datos pesada.

Si deseas realizar alguna modificación en la base de datos o en la aplicación, no dudes en modificar los archivos dentro de los contenedores y luego reconstruir los contenedores con docker-compose up -d --build.

Problemas comunes
Si el puerto 5000 ya está en uso, puedes modificar el archivo docker-compose.yml para exponer otro puerto.

Ejemplo:

yaml
Copy code
ports:
  - "8080:5000"
¡Listo! Ahora puedes comenzar a trabajar con tu sistema de reclutamiento en un entorno Dockerizado.