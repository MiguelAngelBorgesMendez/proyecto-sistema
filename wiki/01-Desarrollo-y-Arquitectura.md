# Desarrollo y arquitectura del proyecto

**Proyecto:** Sistema distribuido de catálogo de productos, arquitectura de tres capas.  
**Autor:** Miguel Angel Borges Mendez  
**Fecha de corte:** 26 de octubre de 2026.

> Esta página documenta **la construcción y evolución del sistema antes de la batería formal de pruebas**. Para la validación, consultar [Plan de pruebas y resultados](02-Plan-de-Pruebas-y-Resultados).

## 1. Introducción

El objetivo fue desarrollar una aplicación web distribuida en contenedores para consultar un catálogo de productos. A diferencia de una aplicación monolítica en un solo servidor, las peticiones pasan por una capa de presentación, una capa de lógica de aplicación y una capa de persistencia. Se plantearon nodos redundantes, balanceadores y mecanismos de elección de servidores primarios para reducir la dependencia de un solo contenedor.

La implementación se realizó en Windows con Docker Desktop y Git Bash mediante Docker Compose, que declara redes internas, servicios, volúmenes, variables de entorno, dependencias y políticas de reinicio.

## 2. Objetivos

- Separar presentación, aplicación y almacenamiento mediante redes Docker.
- Distribuir peticiones entre tres servidores Nginx y tres instancias Node.js.
- Implementar balanceadores HAProxy con Keepalived en modo principal/respaldo y direcciones IP virtuales.
- Mantener un catálogo relacional en tres nodos MariaDB Galera.
- Incorporar reseñas/documentos en MongoDB Replica Set.
- Añadir caché Redis replicado, con tres Redis Sentinel para promoción de primario.
- Incorporar monitorización de infraestructura mediante Nagios.
- Definir inicializaciones repetibles y trazabilidad de las rutas de una solicitud.

## 3. Diseño de tres capas

```text
             Navegador / curl
                    |
               localhost:80
                    |
    HAProxy presentación (master y backup)
    Keepalived: VIP edge 172.30.0.250
                    |
         +----------+----------+
         |          |          |
       web1       web2       web3        Nginx
         +----------+----------+
                    |
    HAProxy aplicación (master y backup)
    Keepalived: VIP 172.31.0.250
                    |
         +----------+----------+
         |          |          |
        app1       app2       app3       Node.js
         +----------+----------+
                    |
         +----------+--------------------+
         |          |                    |
     Galera proxy  MongoDB rs0      Redis + réplica
         |         (con árbitro)    + 3 Sentinel
     galera1/2/3
                    |
               Nagios observa
```

Las redes declaradas son **edge** (`172.30.0.0/24`), **application** (`172.31.0.0/24`, interna) y **database** (`172.18.0.0/16`, interna). El Compose examinado presenta **30 servicios y siete volúmenes nombrados**. Los servicios temporales de inicialización forman parte del inventario, aunque no todos permanecen ejecutándose como procesos persistentes.

## 4. Componentes creados y configuración

### 4.1 Capa de presentación: Nginx + HAProxy + Keepalived

Se desplegaron `web1`, `web2` y `web3` con Nginx. El HAProxy de presentación utiliza `balance roundrobin` y chequeos de salud de los backends, de modo que cada petición puede atenderse desde un servidor web distinto. Se prepararon dos balanceadores (`presentation-lb-master` y `presentation-lb-backup`) y dos procesos Keepalived para gestionar una VIP interna de presentación.

Se incorporaron cabeceras **X-Web-Node** y **X-Presentation-LB**. La primera permite identificar el Nginx que sirvió la respuesta; la segunda indica el balanceador de presentación activo. Estos encabezados se validaron mediante `nginx -t` y recarga controlada de Nginx, sin reinstalar la capa.

### 4.2 Capa de aplicación: Node.js, HAProxy y Keepalived

La API del catálogo se implementó en tres instancias Node.js: `app1`, `app2` y `app3`. Las tres escuchan en el puerto interno 8080 y reciben tráfico a través del HAProxy de aplicación. Los contenedores de balanceo y Keepalived de esta capa funcionan también como principal/respaldo, con VIP `172.31.0.250`.

Las rutas funcionales observadas en el proyecto son:

| Método | Ruta | Finalidad |
|---|---|---|
| GET | `/api/health` | Comprobación del servicio |
| GET | `/api/products/cheapest` | Catálogo de productos económicos |
| POST | `/api/cache/clear` | Invalidación de la entrada de caché |
| GET | `/` | Interfaz web desde la capa Nginx |

La cabecera `x-request-trace` permite ver el recorrido lógico completo de una petición, por ejemplo: `presentation-lb-master -> webnode3 -> application-lb-master -> app1 -> redis -> cache hit`.

### 4.3 Base de datos relacional: MariaDB Galera

Se desplegaron tres nodos `galera1`, `galera2` y `galera3` para los datos del catálogo, con replicación Galera. Se definió un servicio `catalog-init` que prepara el catálogo y un `galera-proxy` dedicado para enrutar conexiones.

Durante la implementación surgió una incidencia de arranque por estados persistidos `safe_to_bootstrap: 0`. Para proteger el enrutamiento hacia instancias que no están listas, se preparó un chequeo WSREP en el proxy, evaluando: `wsrep_cluster_status = Primary`, `wsrep_local_state_comment = Synced` y `wsrep_ready = ON`. El ajuste del proxy debe contrastarse con la versión efectiva del archivo Compose que se suba al repositorio.

### 4.4 MongoDB Replica Set

Se configuró un conjunto de réplicas `rs0`, con dos servidores de datos (`mongodb`, `mongodb2`) y un árbitro (`mongo-arbiter`). Se incorporaron pasos de inicialización como `mongodb-keyfile-init` y `mongo-init-replica` para establecer autenticación entre miembros y configurar la réplica.

El árbitro participa en la votación, pero no conserva una copia de los documentos. La distinción es importante al explicar tolerancia a fallos y quorum.

### 4.5 Redis, réplica y Sentinel

Redis se utiliza como caché para la consulta del catálogo, con la clave `store:products:cheapest`. Se añadió un contenedor de réplica y tres procesos Sentinel (`redis-sentinel1`, `redis-sentinel2`, `redis-sentinel3`) para supervisión del primario y elección de un reemplazo. Se trabajó sobre las configuraciones para conservar la operación tras cambios de rol.

La API debe consultar el primario actual a través del mecanismo apropiado de Sentinel; una referencia fija a `redis` no garantiza por sí sola recuperación transparente ante cambios de primario. Este comportamiento debe comprobarse en el código definitivo publicado.

### 4.6 Nagios

Se desplegó Nagios con interfaz de acceso mediante `http://localhost:8088`, autenticación y archivo de configuración de arquitectura. El panel registra estados de hosts/servicios y proporciona material para correlacionar incidentes. Durante las verificaciones aparecieron **15 advertencias** sobre contactos o grupos de contacto, por lo que el envío externo de alertas sigue pendiente de prueba.

### 4.7 Redes, volúmenes y seguridad

Las redes Docker segmentan el tráfico y las dependencias de los servicios. Los volúmenes preservan datos de Galera y MongoDB después del reinicio de contenedores. En la preparación de GitHub **no deben subirse** contraseñas, el archivo `.env` con valores reales, llaves de MongoDB ni archivos de bases de datos que contengan secretos. Debe ofrecerse `.env.example` con marcadores de posición.

## 5. Proceso de construcción del proyecto

**Etapa 1 — Diseño.** Definición de componentes, diagrama de capas, redes y puertos. Se adoptó Docker Compose como mecanismo de despliegue.

**Etapa 2 — Presentación.** Configuración de Nginx, archivos HAProxy, backends de tres nodos y la pareja Keepalived. Implementación de la VIP y cabeceras de diagnóstico.

**Etapa 3 — Aplicación.** Preparación de la API Node.js, configuración de tres instancias, variables de conexión y balanceador independiente de aplicación.

**Etapa 4 — Persistencia.** Inicialización de MariaDB Galera, proxy SQL, MongoDB Replica Set y Redis con réplica y Sentinel. Se resolvieron incidencias de bootstrap, configuración de autenticación y sincronización.

**Etapa 5 — Monitorización y revisión.** Incorporación de Nagios, revisión de healthchecks, registros y trazabilidad. Tras estabilizar el despliegue, se elaboró la batería de pruebas descrita en la segunda página.

## 6. Archivos relevantes

La estructura local contiene o contempla `docker-compose.yml`, `web/nginx.conf`, `haproxy/`, `keepalived/`, `nagios/`, scripts de inicialización, código Node.js, `tests/performance/`, `TEST-PLAN.md` y `TODO.md`. Las rutas exactas de código dependerán de la carga final del árbol local original.

## 7. Decisiones, dificultades y limitaciones

1. **Galera:** el arranque de un clúster persistente exige controlar cuidadosamente el nodo seguro y el quorum; no se recomienda alterar estados sin respaldo.
2. **Keepalived:** la migración de VIP se probó dentro de Docker; esto **no equivale** necesariamente a conservar el puerto `localhost:80` del host cuando cae el contenedor que lo publica. Se identifica un riesgo de punto único de ingreso.
3. **Redis:** el descubrimiento dinámico del primario debe verificarse en la configuración final de los clientes.
4. **Nagios:** existe monitorización funcional, pero no se ha demostrado el envío de notificaciones externas.
5. **Recursos:** el laboratorio dispone de aproximadamente cuatro CPU y 5.8 GiB de memoria Docker, lo que condiciona pruebas de saturación y caos profundo.

## 8. Entrega y reproducción

```bash
docker compose config --quiet
docker compose up -d
docker compose ps
curl -i http://localhost/api/health
curl -i http://localhost/api/products/cheapest
```

Se requiere antes un archivo `.env` local válido basado en una plantilla sin secretos. No ejecutar `docker compose down -v` si se desea conservar el estado de las bases de datos.

## 9. Cierre

Se construyó un prototipo distribuido con redundancia en presentación y aplicación, replicación de datos, caché de catálogo y monitorización. Su funcionamiento normal quedó demostrado en pruebas puntuales; las garantías más fuertes de disponibilidad, recuperación bajo todas las condiciones y operación continua requieren ensayos adicionales y recursos de laboratorio independientes.

**Siguiente lectura:** [Plan de pruebas y resultados](02-Plan-de-Pruebas-y-Resultados).
