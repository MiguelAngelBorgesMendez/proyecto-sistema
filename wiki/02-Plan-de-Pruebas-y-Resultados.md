# Plan de pruebas y resultados — Sistema distribuido

**Documento 2 de 2 de la Wiki.** Reporte de validación y análisis técnico, con fecha de corte **26 de octubre de 2026**.

Esta página corresponde al reporte de pruebas del sistema. La construcción previa, los componentes, las decisiones de diseño y los problemas de implementación se explican en [Desarrollo y arquitectura](01-Desarrollo-y-Arquitectura).

**Importante:** los escenarios marcados como diseñados o de riesgo **no se ejecutaron**; se conservan para cubrir su metodología sin inventar resultados. Los marcados como parciales no cumplen todos los criterios previstos. La lista de 82 casos es una reconstrucción técnica del plan discutido, no una transcripción literal del archivo TEST-PLAN.md original.

---

## 3. Metodología de pruebas y criterios de evidencia

Se realizaron pruebas funcionales con `docker compose`, `docker exec`, `curl`, comandos nativos MongoDB/MariaDB/Redis y observación de headers; pruebas de rendimiento con scripts Python y `grafana/k6`, y `mariadb-slap` para la base de datos. Las evidencias se guardaron como capturas y archivos `CSV`, `JSON` o `TXT` en `tests/performance/results/` y algunos logs relacionados con alta disponibilidad.

**Clasificación aplicada a los resultados:**

- **VERIFICADA (V):** existe salida o evidencia de la ejecución y puede indicarse el resultado.
- **PARCIAL (P):** la prueba se inició o se tiene evidencia limitada, pero faltó tiempo, un criterio o una medición.
- **DISEÑADA (D):** se explica cómo debería ejecutarse y qué esperar; no se afirma éxito.
- **RIESGO / NO RECOMENDADA (R):** se describe por qué se omitió en el equipo disponible.

Para los casos de alta disponibilidad, el estándar ideal es registrar `t0` (inyección), `t1` (primer estado no saludable), `t2` (primera respuesta recuperada), porcentaje de errores durante la ventana y estado posterior. Un `HTTP 200` al final verifica recuperación, no necesariamente continuidad durante la falla.

## 4. Matriz desarrollada del TEST-PLAN (secciones 1 a 5)

Las siguientes subsecciones presentan cada caso con su procedimiento y resultado. Los apartados de ingeniería del caos que quedaron sin ejecución se describen como **simulaciones teóricas**, es decir, hipótesis para un laboratorio, nunca como evidencia experimental.

### 4.1 Sección 1 — Línea base, funcionalidad y consistencia

#### 1.01 — Despliegue y salud general

**Estado:** **VERIFICADA:** ejecución observada mediante comandos, capturas o registros compartidos.

**Procedimiento o diseño.** Revisar docker compose config, ps y healthchecks, más llamadas HTTP.

**Resultado observado / comportamiento esperado.** Los componentes principales iniciaron; Galera en Primary/Synced, servicios API y web respondiendo 200.

**Soporte, interpretación y límite.** Evidencias de arranque y ps; estado de app1–3 y web1–3.

#### 1.02 — Aislamiento de tres capas y redes

**Estado:** **VERIFICADA:** ejecución observada mediante comandos, capturas o registros compartidos.

**Procedimiento o diseño.** Contrastar servicios y redes edge, application, database en Compose y probar acceso directo por capa.

**Resultado observado / comportamiento esperado.** Tres redes lógicas definidas; Node, Nginx y MariaDB accesibles desde su propio contenedor.

**Soporte, interpretación y límite.** docker-compose.yml aportado y capacidad 2.07.

#### 1.03 — Tres nodos Nginx y respuesta funcional

**Estado:** **VERIFICADA:** ejecución observada mediante comandos, capturas o registros compartidos.

**Procedimiento o diseño.** Consultar web1/web2/web3 mediante el balanceador, registrar HTTP y traza.

**Resultado observado / comportamiento esperado.** Las solicitudes se atienden por webnode1, webnode2 y webnode3 con HTTP 200.

**Soporte, interpretación y límite.** 15 peticiones de evidencia 14; baseline web.

#### 1.04 — Round robin en presentación

**Estado:** **VERIFICADA:** ejecución observada mediante comandos, capturas o registros compartidos.

**Procedimiento o diseño.** Enviar 12 peticiones consecutivas a localhost; identificar web node.

**Resultado observado / comportamiento esperado.** 12 respuestas HTTP 200 distribuidas 5/4/3 entre los tres Nginx.

**Soporte, interpretación y límite.** Evidencia 02, medición previa.

#### 1.05 — Identificación de nodos por cabeceras

**Estado:** **VERIFICADA:** ejecución observada mediante comandos, capturas o registros compartidos.

**Procedimiento o diseño.** Agregar X-Web-Node a Nginx, validar sintaxis y recargar sin detener.

**Resultado observado / comportamiento esperado.** Las respuestas exponen X-Web-Node y X-Presentation-LB con sus nombres correctos.

**Soporte, interpretación y límite.** Configuración web/nginx.conf y evidencia 03.

#### 1.06 — Distribución balanceada de API

**Estado:** **VERIFICADA:** ejecución observada mediante comandos, capturas o registros compartidos.

**Procedimiento o diseño.** Quince solicitudes de /api/products/cheapest; inspeccionar x-request-trace.

**Resultado observado / comportamiento esperado.** HTTP 200 en 15/15; app1=5, app2=5, app3=5; web1/2/3 identificados.

**Soporte, interpretación y límite.** Evidencia_14_Balanceo_API.png.

#### 1.07 — Endpoint de salud y rutas críticas

**Estado:** **VERIFICADA:** ejecución observada mediante comandos, capturas o registros compartidos.

**Procedimiento o diseño.** Consultar /api/health y /api/products/cheapest después del despliegue.

**Resultado observado / comportamiento esperado.** Se observó HTTP 200 en salud y catálogo; las consultas posteriores al benchmark también devolvieron 200.

**Soporte, interpretación y límite.** Salidas de pruebas funcionales.

#### 1.08 — Integridad de datos en Galera

**Estado:** **VERIFICADA:** ejecución observada mediante comandos, capturas o registros compartidos.

**Procedimiento o diseño.** Crear tabla InnoDB temporal en galera1, insertar registro, consultar desde tres nodos y eliminar tabla.

**Resultado observado / comportamiento esperado.** Se recuperó el mismo registro desde los tres nodos; la tabla temporal se eliminó al finalizar.

**Soporte, interpretación y límite.** Evidencia 04: replicación Galera.

#### 1.09 — Caché Redis: MISS y HIT

**Estado:** **VERIFICADA:** ejecución observada mediante comandos, capturas o registros compartidos.

**Procedimiento o diseño.** Limpiar cache con POST /api/cache/clear y efectuar dos GET del catálogo.

**Resultado observado / comportamiento esperado.** Primer GET con cache miss y consulta Galera; segundo con cache hit; catálogo coincidente.

**Soporte, interpretación y límite.** Evidencia 05: Cache hit/miss.

#### 1.10 — Replica Set MongoDB

**Estado:** **VERIFICADA:** ejecución observada mediante comandos, capturas o registros compartidos.

**Procedimiento o diseño.** Revisar rs.status() y elecciones del conjunto mongodb/mongodb2/mongo-arbiter.

**Resultado observado / comportamiento esperado.** PRIMARY, SECONDARY y ARBITER observados; cambio de PRIMARY también probado.

**Soporte, interpretación y límite.** Registros previos de rs.status().

#### 1.11 — Redis Sentinel

**Estado:** **VERIFICADA:** ejecución observada mediante comandos, capturas o registros compartidos.

**Procedimiento o diseño.** Comprobar Redis primario, réplica y tres Sentinels; fallas manuales/automáticas.

**Resultado observado / comportamiento esperado.** Redis Sentinel promovió réplica; servicio restituido posteriormente.

**Soporte, interpretación y límite.** Registros previos de conmutación Redis.

#### 1.12 — Monitoreo inicial Nagios

**Estado:** **PARCIAL:** ejecución existente, pero con limitación, error o métrica no obtenida.

**Procedimiento o diseño.** Validar arranque, host/service status y panel HTTP autenticado.

**Resultado observado / comportamiento esperado.** Portal en localhost:8088 requiere autenticación; checks registrados; advertencias por contactos no configurados.

**Soporte, interpretación y límite.** Capturas Nagios incluidas como anexo.

#### 1.13 — Inicialización idempotente de catálogo y réplica Mongo

**Estado:** **PARCIAL:** ejecución existente, pero con limitación, error o métrica no obtenida.

**Procedimiento o diseño.** Revisar ejecución de catalog-init y mongo-init-replica; repetir reinicio sin duplicados.

**Resultado observado / comportamiento esperado.** Los contenedores de inicialización existen y la aplicación respondió; no consta ensayo formal de idempotencia repetida.

**Soporte, interpretación y límite.** Compose y registros funcionales; idempotencia formal pendiente.

#### 1.14 — Verificación negativa de rutas no existentes

**Estado:** **DISEÑADA / NO EJECUTADA:** caso documentado con comportamiento esperado; no se afirma que sucedió.

**Procedimiento o diseño.** Solicitar una ruta API inexistente y validar código 404 sin exponer stacktrace.

**Resultado observado / comportamiento esperado.** Debe responder 404 controlado; el caso no tiene medición aportada.

**Soporte, interpretación y límite.** Por documentar con curl y captura.


### 4.2 Sección 2 — Rendimiento y capacidad

#### 2.01 — Smoke 1 usuario / 20 segundos

**Estado:** **VERIFICADA:** ejecución observada mediante comandos, capturas o registros compartidos.

**Procedimiento o diseño.** Cliente Python, 150 ms entre solicitudes; lectura de catálogo por HTTP.

**Resultado observado / comportamiento esperado.** 120 solicitudes, 0 errores, 5.96 req/s; p50=19.25 ms, p95=29.69 ms, p99=32.92 ms.

**Soporte, interpretación y límite.** smoke_20261026_034822.csv y summary.json; evidencia 06.

#### 2.02 — Smoke 5 usuarios / 20 segundos

**Estado:** **VERIFICADA:** ejecución observada mediante comandos, capturas o registros compartidos.

**Procedimiento o diseño.** Cinco usuarios concurrentes y mismo patrón de lectura.

**Resultado observado / comportamiento esperado.** 604 solicitudes, 0 errores, 29.96 req/s; p50=16.19 ms, p95=29.76 ms, p99=32.63 ms.

**Soporte, interpretación y límite.** smoke_20261026_034822.csv y summary.json.

#### 2.03 — Load 10 usuarios / 10 minutos

**Estado:** **VERIFICADA:** ejecución observada mediante comandos, capturas o registros compartidos.

**Procedimiento o diseño.** Diez usuarios, 250 ms entre consultas; estadísticas CPU/memoria en cinco puntos.

**Resultado observado / comportamiento esperado.** 21,897 solicitudes, 0 errores; 36.48 req/s; p50=19.58 ms, p95=23.80 ms, p99=31.32 ms; 600.27 s.

**Soporte, interpretación y límite.** load_20261026_035157.csv, _summary.json, _docker_stats.txt; evidencia 07.

#### 2.04 — Stress escalonado hasta 30 usuarios

**Estado:** **PARCIAL:** ejecución existente, pero con limitación, error o métrica no obtenida.

**Procedimiento o diseño.** Niveles 5/10/20/30 usuarios, 25 segundos por nivel.

**Resultado observado / comportamiento esperado.** 13,514 solicitudes totales, 0 errores; throughput máximo observado 244.63 req/s a 30 usuarios, p95=58.43 ms, p99=93.40 ms. No se encontró el punto de ruptura.

**Soporte, interpretación y límite.** stress_20261026_040541.csv y _summary.json; evidencia 08.

#### 2.05 — Spike 300 usuarios virtuales

**Estado:** **VERIFICADA:** ejecución observada mediante comandos, capturas o registros compartidos.

**Procedimiento o diseño.** k6 desde 5 hasta 300 VU en 2 segundos, pico 8 s, recuperación; GET catálogo.

**Resultado observado / comportamiento esperado.** 5,256 solicitudes, 0 fallos; 149.43 req/s global; p50=23.82 ms, p95=112.14 ms, p99=169.43 ms, máximo 228.59 ms.

**Soporte, interpretación y límite.** spike_<fecha>.txt y summary.json; evidencia 09. VU no equivale a 300 HTTP simultáneos.

#### 2.06 — Soak prolongado

**Estado:** **PARCIAL:** ejecución existente, pero con limitación, error o métrica no obtenida.

**Procedimiento o diseño.** Se ejecutó una versión corta de 10 minutos con 10 VU y pausa 0.6 s.

**Resultado observado / comportamiento esperado.** 9,867 solicitudes, 0 errores, 16.43 req/s; p50=6.58 ms, p95=13.84 ms, p99=20.97 ms. No demuestra estabilidad de varias horas.

**Soporte, interpretación y límite.** soak_20261026_041949.txt, _summary.json, _stats.txt; evidencia 10.

#### 2.07 — Cache Effect: 25 pares MISS/HIT

**Estado:** **PARCIAL:** ejecución existente, pero con limitación, error o métrica no obtenida.

**Procedimiento o diseño.** Limpiar cache antes de cada par y comparar latencia/trazas/datos.

**Resultado observado / comportamiento esperado.** 13 pares válidos de 25 planificados; la comparación 14 invalidó la ejecución. En 13 pares: miss p50=15.27 ms/p95=36.63 ms; hit p50=11.34 ms/p95=25.74 ms.

**Soporte, interpretación y límite.** cache_effect_20261026_043330.csv y _summary.json; all_valid=false; evidencia 11.

#### 2.08 — Capacidad por capa: Nginx web1

**Estado:** **VERIFICADA:** ejecución observada mediante comandos, capturas o registros compartidos.

**Procedimiento o diseño.** k6 con 5 VU, 20 segundos, acceso local web1 sin balanceador de presentación.

**Resultado observado / comportamiento esperado.** 930 solicitudes, 0 errores, 46.34 req/s, promedio 6.82 ms, p95=11.87 ms, p99=19.17 ms.

**Soporte, interpretación y límite.** capacity_web_<fecha>.json y .txt; evidencia 12.

#### 2.09 — Capacidad por capa: Node.js app1

**Estado:** **VERIFICADA:** ejecución observada mediante comandos, capturas o registros compartidos.

**Procedimiento o diseño.** k6 con 5 VU, 20 segundos, llamada local :8080/products/cheapest.

**Resultado observado / comportamiento esperado.** 976 solicitudes, 0 errores, 48.56 req/s, promedio 1.63 ms, p95=2.66 ms, p99=6.84 ms.

**Soporte, interpretación y límite.** capacity_app_<fecha>.json y .txt; evidencia 12.

#### 2.10 — Capacidad por capa: MariaDB Galera1

**Estado:** **VERIFICADA:** ejecución observada mediante comandos, capturas o registros compartidos.

**Procedimiento o diseño.** mariadb-slap --no-defaults; SELECT COUNT(*) FROM products, 5 clientes, 200 consultas/iteración, 3 iteraciones.

**Resultado observado / comportamiento esperado.** Promedio 0.150 s por iteración, mínimo 0.147 s, máximo 0.156 s; catálogo final HTTP 200.

**Soporte, interpretación y límite.** capacity_galera_corrected.txt; evidencia 12.

#### 2.11 — Saturación hasta determinar capacidad máxima

**Estado:** **NO RECOMENDADA EN ESTE ENTORNO:** la prueba exige aislamiento/recursos o arriesga la integridad del cluster.

**Procedimiento o diseño.** Aumentar la concurrencia hasta observar colas, errores y punto de quiebre por capa.

**Resultado observado / comportamiento esperado.** No realizada: equipo de recursos limitados y riesgo de desestabilizar Galera/containers. No inferir capacidad máxima de los niveles probados.

**Soporte, interpretación y límite.** Requiere laboratorio separado y presupuesto de recursos.

### 4.3 Comparativo central de rendimiento

| Escenario | Carga y duración | Peticiones | Error observado | p95 | p99 | Observación |
|---|---|---:|---:|---:|---:|---|
| Smoke 1 VU | 20 s | 120 | 0% | 29.69 ms | 32.92 ms | Línea base |
| Smoke 5 VU | 20 s | 604 | 0% | 29.76 ms | 32.63 ms | Escala de arranque |
| Load | 10 usuarios / 10 min | 21,897 | 0% | 23.80 ms | 31.32 ms | Carga estable medida |
| Stress nivel máximo | 30 usuarios / 25 s | 6,155 | 0% | 58.43 ms | 93.40 ms | Sin detectar ruptura |
| Spike | 300 VU máximos / 35 s | 5,256 | 0% | 112.14 ms | 169.43 ms | Pico acotado |
| Soak corto | 10 VU / 10 min | 9,867 | 0% | 13.84 ms | 20.97 ms | No equivale a horas |
| Web1 directo | 5 VU / 20 s | 930 | 0% | 11.87 ms | 19.17 ms | Recurso HTML Nginx |
| APP1 directo | 5 VU / 20 s | 976 | 0% | 2.66 ms | 6.84 ms | API sobre datos en caché |

En la prueba Stress se registraron 5 usuarios con 1,038 solicitudes y 41.34 req/s; 10 usuarios, 2,116 y 84.39 req/s; 20 usuarios, 4,205 y 167.49 req/s; 30 usuarios, 6,155 y 244.63 req/s. La latencia p95 subió de 28.91 a 58.43 ms en esos extremos. Una carga más alta podría revelar límites distintos. La comparación de capacidad Web frente a APP no es directa porque el primer endpoint devuelve contenido Nginx y el segundo consulta una API con caché. En Galera el promedio 0.150 s representa una corrida de 200 consultas, **no una latencia individual p95 de consulta**.

**Interpretación de caché:** en 13 comparaciones válidas se registró p50 MISS de 15.27 ms frente a p50 HIT de 11.34 ms, una diferencia de aproximadamente 25.7% de la mediana de MISS. Pero el par 14 incumplió la validación y el script usaba un booleano conjunto llamado `valid`; por eso `Datos iguales=False` no demuestra por sí solo que los productos fueran distintos. No se atribuye causa definitiva sin revisar trazas y contenido.


### 4.4 Sección 3 — Alta disponibilidad y Failover

#### 3.01 — VIP de presentación pasa al backup

**Estado:** **VERIFICADA:** ejecución observada mediante comandos, capturas o registros compartidos.

**Procedimiento o diseño.** Detener Keepalived master; consultar VIP 172.30.0.250 y después recuperar.

**Resultado observado / comportamiento esperado.** VIP se desplazó al backup y regresó al master; acceso HTTP por la VIP confirmado.

**Soporte, interpretación y límite.** Registros previos Keepalived.

#### 3.02 — VIP de aplicación pasa al backup

**Estado:** **VERIFICADA:** ejecución observada mediante comandos, capturas o registros compartidos.

**Procedimiento o diseño.** Detener Keepalived master; consultar VIP 172.31.0.250 y recuperar.

**Resultado observado / comportamiento esperado.** VIP se desplazó al backup y regresó al master; servicio accesible por la VIP.

**Soporte, interpretación y límite.** Registros previos Keepalived.

#### 3.03 — Congelamiento HAProxy en presentación

**Estado:** **VERIFICADA:** ejecución observada mediante comandos, capturas o registros compartidos.

**Procedimiento o diseño.** docker pause al balanceador master y observar script track + VIP.

**Resultado observado / comportamiento esperado.** Track HTTP detectó indisponibilidad; backup tomó VIP y posteriormente volvió a master.

**Soporte, interpretación y límite.** Registros previos de pause/unpause.

#### 3.04 — Congelamiento HAProxy en aplicación

**Estado:** **VERIFICADA:** ejecución observada mediante comandos, capturas o registros compartidos.

**Procedimiento o diseño.** docker pause al balanceador master y observar track + VIP.

**Resultado observado / comportamiento esperado.** Se observó conmutación de VIP al backup y recuperación posterior.

**Soporte, interpretación y límite.** Registros previos de pause/unpause.

#### 3.05 — Tiempo RTO de cambios de VIP

**Estado:** **PARCIAL:** ejecución existente, pero con limitación, error o métrica no obtenida.

**Procedimiento o diseño.** Medir inicio de falla, primer error, primera respuesta restaurada y oscilación bajo carga.

**Resultado observado / comportamiento esperado.** Se comprobó continuidad en verificaciones puntuales, pero no se midió RTO/RPO ni una serie de errores por segundo.

**Soporte, interpretación y límite.** No afirmar cumplimiento del objetivo 3–4 s.

#### 3.06 — Pérdida de web3 bajo carga

**Estado:** **PARCIAL:** ejecución existente, pero con limitación, error o métrica no obtenida.

**Procedimiento o diseño.** Solicitudes continuas, docker stop web3, esperar y recuperar.

**Resultado observado / comportamiento esperado.** El ensayo quedó bloqueado; posteriormente web3 se reinició y web1/web2/web3 quedaron Up, HTTP final 200. No concluyente sobre disponibilidad durante falla.

**Soporte, interpretación y límite.** Prueba interrumpida, recovery HTTP 200.

#### 3.07 — Caída controlada de web1

**Estado:** **DISEÑADA / NO EJECUTADA:** caso documentado con comportamiento esperado; no se afirma que sucedió.

**Procedimiento o diseño.** Detener web1 y verificar retirada del backend sin pérdida de servicio.

**Resultado observado / comportamiento esperado.** Con web2/web3 operativos el balanceador debería responder 200; sin ejecución confirmada.

**Soporte, interpretación y límite.** Se recomienda ensayo breve con recuperación automática.

#### 3.08 — Falla simultánea de web1 y web2

**Estado:** **DISEÑADA / NO EJECUTADA:** caso documentado con comportamiento esperado; no se afirma que sucedió.

**Procedimiento o diseño.** Detener dos Nginx y comprobar servicio restante web3.

**Resultado observado / comportamiento esperado.** Se esperaría disponibilidad con reducción de capacidad; sin medición ni captura.

**Soporte, interpretación y límite.** Debe medirse serie temporal y tasa de error.

#### 3.09 — Indisponibilidad de los tres Nginx

**Estado:** **DISEÑADA / NO EJECUTADA:** caso documentado con comportamiento esperado; no se afirma que sucedió.

**Procedimiento o diseño.** Simular caída de los tres backends web controladamente.

**Resultado observado / comportamiento esperado.** Se espera error 503 o equivalente en HAProxy. No se provocó para evitar interrupción global.

**Soporte, interpretación y límite.** Ensayo negativo en entorno aislado.

#### 3.10 — Respuesta directa de app1, app2, app3

**Estado:** **VERIFICADA:** ejecución observada mediante comandos, capturas o registros compartidos.

**Procedimiento o diseño.** fetch local http://127.0.0.1:8080/products/cheapest en cada contenedor.

**Resultado observado / comportamiento esperado.** HTTP 200 en las tres API y en el VIP de aplicación; contenedores Up.

**Soporte, interpretación y límite.** Evidencia 13: disponibilidad de tres API.

#### 3.11 — Balanceo efectivo de las tres API

**Estado:** **VERIFICADA:** ejecución observada mediante comandos, capturas o registros compartidos.

**Procedimiento o diseño.** Quince GET y lectura de x-request-trace.

**Resultado observado / comportamiento esperado.** app1=5, app2=5, app3=5, todas HTTP 200.

**Soporte, interpretación y límite.** Evidencia_14_Balanceo_API.png.

#### 3.12 — Congelamiento individual de app3

**Estado:** **DISEÑADA / NO EJECUTADA:** caso documentado con comportamiento esperado; no se afirma que sucedió.

**Procedimiento o diseño.** docker pause app3, esperar healthchecks de HAProxy, generar 15 GET y docker unpause.

**Resultado observado / comportamiento esperado.** Se espera reasignación a app1/app2. El bloque se propuso, pero no se ejecutó ni se obtuvo salida.

**Soporte, interpretación y límite.** No registrar como exitoso.

#### 3.13 — Caída simultánea de app1 y app2

**Estado:** **DISEÑADA / NO EJECUTADA:** caso documentado con comportamiento esperado; no se afirma que sucedió.

**Procedimiento o diseño.** Retirar dos APIs, observar app3 y servicios dependientes.

**Resultado observado / comportamiento esperado.** Se espera degradación de capacidad con la tercera API disponible; no verificado.

**Soporte, interpretación y límite.** Ensayar en entorno separado.

#### 3.14 — Pérdida de todas las API

**Estado:** **DISEÑADA / NO EJECUTADA:** caso documentado con comportamiento esperado; no se afirma que sucedió.

**Procedimiento o diseño.** Deshabilitar los tres backends con recuperación programada.

**Resultado observado / comportamiento esperado.** Se espera 503 desde HAProxy de aplicaciones; no realizado.

**Soporte, interpretación y límite.** Escenario negativo diseñado.

#### 3.15 — Elección de PRIMARY MongoDB

**Estado:** **VERIFICADA:** ejecución observada mediante comandos, capturas o registros compartidos.

**Procedimiento o diseño.** Detener primario mongodb, observar nueva elección; reiniciar nodo anterior.

**Resultado observado / comportamiento esperado.** mongodb2 asumió PRIMARY y mongodb se reintegró como SECONDARY.

**Soporte, interpretación y límite.** Registros rs.status y failover previos.

#### 3.16 — Pérdida simultánea de mayoría MongoDB

**Estado:** **NO RECOMENDADA EN ESTE ENTORNO:** la prueba exige aislamiento/recursos o arriesga la integridad del cluster.

**Procedimiento o diseño.** Quitar PRIMARY + nodo votante o simular partición que rompa quorum.

**Resultado observado / comportamiento esperado.** Sin quorum no hay escritura disponible; no ejecutado por riesgo de recuperación y datos.

**Soporte, interpretación y límite.** Laboratorio con volúmenes clonados.

#### 3.17 — Redis Sentinel failover automático

**Estado:** **VERIFICADA:** ejecución observada mediante comandos, capturas o registros compartidos.

**Procedimiento o diseño.** Provocar indisponibilidad del primario y observar SENTINEL; recuperar.

**Resultado observado / comportamiento esperado.** Promoción de réplica probada y lectura/escritura del servicio recuperadas.

**Soporte, interpretación y límite.** Registros de Sentinel.

#### 3.18 — Redis Sentinel failover manual

**Estado:** **VERIFICADA:** ejecución observada mediante comandos, capturas o registros compartidos.

**Procedimiento o diseño.** Invocar promoción controlada y confirmar master designado.

**Resultado observado / comportamiento esperado.** Cambio de primario realizado y restauración probada.

**Soporte, interpretación y límite.** Registros previos.

#### 3.19 — Fallo simultáneo de Redis y su réplica

**Estado:** **DISEÑADA / NO EJECUTADA:** caso documentado con comportamiento esperado; no se afirma que sucedió.

**Procedimiento o diseño.** Apagar ambos procesos de Redis con sentinels activos.

**Resultado observado / comportamiento esperado.** Sin instancia de datos, el caché no puede servir; respuesta API depende de lógica de degradación. No medido.

**Soporte, interpretación y límite.** No afirmar caída ni resiliencia total.

#### 3.20 — Galera: proxy con validación WSREP

**Estado:** **VERIFICADA:** ejecución observada mediante comandos, capturas o registros compartidos.

**Procedimiento o diseño.** Configurar chequeo externo de estado Primary/Synced/ON en galera-proxy; revisar 3 UP.

**Resultado observado / comportamiento esperado.** Se observó backend Galera con tres nodos UP y consultas HTTP 200; proxy evita nodos no Synced.

**Soporte, interpretación y límite.** Config haproxy/galera-check.sh y HAProxy; salidas previas.

#### 3.21 — Galera: caída de un nodo

**Estado:** **PARCIAL:** ejecución existente, pero con limitación, error o métrica no obtenida.

**Procedimiento o diseño.** Retirar nodo Galera y consultar catálogo vía proxy.

**Resultado observado / comportamiento esperado.** Se había presentado un problema de arranque safe_to_bootstrap; posteriormente se recuperó clúster de tres. No hay medición controlada de disponibilidad durante la falla final.

**Soporte, interpretación y límite.** Incidentes Galera y reparación documentada.

#### 3.22 — Galera: caída de dos nodos/quorum

**Estado:** **NO RECOMENDADA EN ESTE ENTORNO:** la prueba exige aislamiento/recursos o arriesga la integridad del cluster.

**Procedimiento o diseño.** Detener dos de tres nodos y estudiar pérdida de componente primario.

**Resultado observado / comportamiento esperado.** No ejecutada deliberadamente: riesgo de quorum, SST/IST, safe_to_bootstrap y recuperación compleja.

**Soporte, interpretación y límite.** Requiere backup y entorno aislado.

#### 3.23 — Reinicio total y recuperación de todo el stack

**Estado:** **NO RECOMENDADA EN ESTE ENTORNO:** la prueba exige aislamiento/recursos o arriesga la integridad del cluster.

**Procedimiento o diseño.** Parar todos los servicios, iniciarlos en orden y medir RTO global.

**Resultado observado / comportamiento esperado.** No ejecutada: un bootstrap incorrecto de Galera con estado persistente puede impedir recuperar el cluster.

**Soporte, interpretación y límite.** Procedimiento y backup verificado antes de hacerlo.

#### 3.24 — Punto único de fallo del ingreso externo

**Estado:** **PARCIAL:** ejecución existente, pero con limitación, error o métrica no obtenida.

**Procedimiento o diseño.** Comprobar respuesta por localhost:80 al perder presentation-lb-master.

**Resultado observado / comportamiento esperado.** VIP funciona internamente, pero el puerto 80 del host está publicado solo por presentation-lb-master en el Compose aportado. La continuidad de localhost:80 tras su parada no está probada.

**Soporte, interpretación y límite.** Riesgo arquitectónico abierto.


### 4.5 Sección 4 — Ingeniería del caos y simulación controlada

#### 4.01 — Contenedor web: parada abrupta

**Estado:** **PARCIAL:** ejecución existente, pero con limitación, error o métrica no obtenida.

**Procedimiento o diseño.** Detener un web backend con solicitudes en marcha.

**Resultado observado / comportamiento esperado.** Intento con web3 se bloqueó; se recuperó web3, sin datos concluyentes de RTO ni error-rate.

**Soporte, interpretación y límite.** No registrar éxito.

#### 4.02 — Contenedor API: freeze temporal

**Estado:** **DISEÑADA / NO EJECUTADA:** caso documentado con comportamiento esperado; no se afirma que sucedió.

**Procedimiento o diseño.** docker pause app3; medir HAProxy health, redistribución y recuperación.

**Resultado observado / comportamiento esperado.** Tráfico debería abandonar backend no responsivo; sin ejecución observada.

**Soporte, interpretación y límite.** Procedimiento propuesto, ejecución pendiente.

#### 4.03 — Balanceador master detenido

**Estado:** **VERIFICADA:** ejecución observada mediante comandos, capturas o registros compartidos.

**Procedimiento o diseño.** Pausar HAProxy master y observar Keepalived.

**Resultado observado / comportamiento esperado.** VIP migra al backup en presentación y aplicación, y vuelve al recuperar.

**Soporte, interpretación y límite.** Ensayos previos y registros Keepalived.

#### 4.04 — MongoDB PRIMARY detenido

**Estado:** **VERIFICADA:** ejecución observada mediante comandos, capturas o registros compartidos.

**Procedimiento o diseño.** Falla del PRIMARY y seguimiento de rs.status.

**Resultado observado / comportamiento esperado.** Elección de nuevo PRIMARY y unión del antiguo primario como SECONDARY.

**Soporte, interpretación y límite.** Ensayo previo de MongoDB.

#### 4.05 — Redis PRIMARY detenido

**Estado:** **VERIFICADA:** ejecución observada mediante comandos, capturas o registros compartidos.

**Procedimiento o diseño.** Forzar/promover réplica mediante Sentinel y validar master actual.

**Resultado observado / comportamiento esperado.** Sentinel redistribuyó el rol y el servicio se recuperó.

**Soporte, interpretación y límite.** Ensayo previo de Redis.

#### 4.06 — Galera individual degradado

**Estado:** **PARCIAL:** ejecución existente, pero con limitación, error o métrica no obtenida.

**Procedimiento o diseño.** Comprobar que el proxy excluye nodos no Synced y que los datos se replican.

**Resultado observado / comportamiento esperado.** Chequeo WSREP y acceso normal demostrados; caída programada con medición no completada.

**Soporte, interpretación y límite.** Configuración y pruebas previas.

#### 4.07 — Latencia artificial de red entre capas

**Estado:** **DISEÑADA / NO EJECUTADA:** caso documentado con comportamiento esperado; no se afirma que sucedió.

**Procedimiento o diseño.** tc netem con 100–300 ms en red específica, monitorizar p95 y timeouts.

**Resultado observado / comportamiento esperado.** Se espera incremento de latencia y posible timeout al alcanzar límites; no se configuró netem.

**Soporte, interpretación y límite.** Requiere privilegios NET_ADMIN y medición previa.

#### 4.08 — Pérdida de paquetes hacia MongoDB

**Estado:** **DISEÑADA / NO EJECUTADA:** caso documentado con comportamiento esperado; no se afirma que sucedió.

**Procedimiento o diseño.** Introducir pérdida limitada de paquetes con tc/netem y medir retries.

**Resultado observado / comportamiento esperado.** Se espera reintento/error transitorio según timeout MongoDB; no ejecutado.

**Soporte, interpretación y límite.** Entorno de pruebas aislado.

#### 4.09 — Partición de red en Galera

**Estado:** **NO RECOMENDADA EN ESTE ENTORNO:** la prueba exige aislamiento/recursos o arriesga la integridad del cluster.

**Procedimiento o diseño.** Desconectar nodos de red database para provocar componentes primario/no primario.

**Resultado observado / comportamiento esperado.** Arriesga quorum y divergencia/transacciones; sin ejecución.

**Soporte, interpretación y límite.** No probar en stack único sin backups.

#### 4.10 — Aislamiento de web1 en red edge

**Estado:** **DISEÑADA / NO EJECUTADA:** caso documentado con comportamiento esperado; no se afirma que sucedió.

**Procedimiento o diseño.** docker network disconnect web1 de edge y reconectar al finalizar.

**Resultado observado / comportamiento esperado.** HAProxy debería retirar backend inaccesible; requiere preservar nombre/aliases y estado.

**Soporte, interpretación y límite.** Pendiente.

#### 4.11 — Límite de memoria a aplicación

**Estado:** **DISEÑADA / NO EJECUTADA:** caso documentado con comportamiento esperado; no se afirma que sucedió.

**Procedimiento o diseño.** Aplicar docker update --memory con umbral conservador y medir reinicios.

**Resultado observado / comportamiento esperado.** Es esperable degradación/OOM si se supera el límite; no ejecutado por memoria local reducida.

**Soporte, interpretación y límite.** Plan experimental documentado.

#### 4.12 — CPU throttling en Node.js

**Estado:** **DISEÑADA / NO EJECUTADA:** caso documentado con comportamiento esperado; no se afirma que sucedió.

**Procedimiento o diseño.** Restringir CPUs o cpu-quota de un nodo, medir p95 y balanceo.

**Resultado observado / comportamiento esperado.** Se espera aumento de duración en el nodo limitado y posible exclusión si deja de responder.

**Soporte, interpretación y límite.** Sin medición real.

#### 4.13 — Disco lleno en volumen de base de datos

**Estado:** **NO RECOMENDADA EN ESTE ENTORNO:** la prueba exige aislamiento/recursos o arriesga la integridad del cluster.

**Procedimiento o diseño.** Rellenar volumen hasta capacidad máxima durante escritura.

**Resultado observado / comportamiento esperado.** Puede corromper o bloquear recuperación; expresamente omitido.

**Soporte, interpretación y límite.** Solo sobre volúmenes descartables/clonados.

#### 4.14 — Fallos de DNS interno

**Estado:** **DISEÑADA / NO EJECUTADA:** caso documentado con comportamiento esperado; no se afirma que sucedió.

**Procedimiento o diseño.** Inyectar resolución incorrecta o quitar aliases en servicio aislado.

**Resultado observado / comportamiento esperado.** Se espera error de conexión dependiente del resolver y retries; no probado.

**Soporte, interpretación y límite.** Diseño teórico.

#### 4.15 — Desfase de reloj / clock skew

**Estado:** **NO RECOMENDADA EN ESTE ENTORNO:** la prueba exige aislamiento/recursos o arriesga la integridad del cluster.

**Procedimiento o diseño.** Desincronizar reloj dentro de uno o varios contenedores.

**Resultado observado / comportamiento esperado.** No se realizó: Docker comparte reloj kernel del host en gran medida; manipulación puede afectar todos los servicios.

**Soporte, interpretación y límite.** Necesita aislamiento avanzado, VM o time namespace adecuado.

#### 4.16 — Dependencia MongoDB indisponible

**Estado:** **DISEÑADA / NO EJECUTADA:** caso documentado con comportamiento esperado; no se afirma que sucedió.

**Procedimiento o diseño.** Deshabilitar acceso a Replica Set y probar salud, ruta reseñas y catálogo.

**Resultado observado / comportamiento esperado.** El comportamiento real depende de la implementación; no se observa respuesta en falla total.

**Soporte, interpretación y límite.** Revisar código y probar de forma aislada.

#### 4.17 — Dependencia Redis indisponible

**Estado:** **DISEÑADA / NO EJECUTADA:** caso documentado con comportamiento esperado; no se afirma que sucedió.

**Procedimiento o diseño.** Bloquear ambas instancias de Redis y observar fallback a Galera.

**Resultado observado / comportamiento esperado.** El fallback no está confirmado; no afirmar que la API mantiene HTTP200.

**Soporte, interpretación y límite.** Ensayo pendiente.

#### 4.18 — Dependencia Galera no disponible

**Estado:** **DISEÑADA / NO EJECUTADA:** caso documentado con comportamiento esperado; no se afirma que sucedió.

**Procedimiento o diseño.** Retirar todas las bases de datos y observar error handling.

**Resultado observado / comportamiento esperado.** Se espera fallo controlado en endpoints SQL; código preciso y recuperación no medidos.

**Soporte, interpretación y límite.** Pendiente en entorno seguro.

#### 4.19 — Fallas compuestas Redis + API

**Estado:** **DISEÑADA / NO EJECUTADA:** caso documentado con comportamiento esperado; no se afirma que sucedió.

**Procedimiento o diseño.** Pausar una API y forzar Redis failover en la misma ventana.

**Resultado observado / comportamiento esperado.** Se requiere evaluar errores correlacionados, RTO y recuperaciones; no se ejecutó.

**Soporte, interpretación y límite.** No inferir resiliencia compuesta de pruebas aisladas.

#### 4.20 — Fallas aleatorias estilo Chaos Monkey

**Estado:** **DISEÑADA / NO EJECUTADA:** caso documentado con comportamiento esperado; no se afirma que sucedió.

**Procedimiento o diseño.** Selección pseudoaleatoria de un solo servicio no crítico, con semilla, abort y cleanup.

**Resultado observado / comportamiento esperado.** No se ejecutó selección aleatoria reproducible; se propuso como experimento futuro.

**Soporte, interpretación y límite.** Debe excluir Galera bootstrap y volúmenes.

#### 4.21 — Reinicio completo / cold start caótico

**Estado:** **NO RECOMENDADA EN ESTE ENTORNO:** la prueba exige aislamiento/recursos o arriesga la integridad del cluster.

**Procedimiento o diseño.** Parar stack y arrancar con dependencias, medir estabilidad.

**Resultado observado / comportamiento esperado.** No realizado por riesgos Galera, Mongo elections y recursos limitados.

**Soporte, interpretación y límite.** Requiere respaldo de volúmenes y secuencia de arranque validada.


### 4.6 Sección 5 — Observabilidad, Nagios y SLO

#### 5.01 — Acceso web y autenticación Nagios

**Estado:** **VERIFICADA:** ejecución observada mediante comandos, capturas o registros compartidos.

**Procedimiento o diseño.** Consultar localhost:8088 y comprobar HTTP 401 sin credenciales.

**Resultado observado / comportamiento esperado.** Servicio protegido; 401 sin autenticación es respuesta esperada, no caída.

**Soporte, interpretación y límite.** Capturas de Nagios.

#### 5.02 — Validación de configuración Nagios

**Estado:** **PARCIAL:** ejecución existente, pero con limitación, error o métrica no obtenida.

**Procedimiento o diseño.** Ejecutar verificación sintáctica de Nagios.

**Resultado observado / comportamiento esperado.** 0 errores y 15 advertencias relativas a contacto/contactgroup; la configuración carga pero notificaciones pendientes.

**Soporte, interpretación y límite.** Salida previa de preflight.

#### 5.03 — Inventario de hosts monitoreados

**Estado:** **VERIFICADA:** ejecución observada mediante comandos, capturas o registros compartidos.

**Procedimiento o diseño.** Revisar páginas Host Status / Service Status.

**Resultado observado / comportamiento esperado.** Se observaron 15 hosts y sus servicios en panel de monitoreo.

**Soporte, interpretación y límite.** Evidencia_Nagios_Hosts.png.

#### 5.04 — Captura de estado de servicios

**Estado:** **VERIFICADA:** ejecución observada mediante comandos, capturas o registros compartidos.

**Procedimiento o diseño.** Consultar Service Status.

**Resultado observado / comportamiento esperado.** Dashboard muestra estados OK/WARNING/CRITICAL de acuerdo con la captura del momento.

**Soporte, interpretación y límite.** Evidencia_Nagios_Servicios.png.

#### 5.05 — Incidencias y recuperaciones en Nagios

**Estado:** **PARCIAL:** ejecución existente, pero con limitación, error o métrica no obtenida.

**Procedimiento o diseño.** Revisar registro visual de avisos durante fallas parciales.

**Resultado observado / comportamiento esperado.** Existen capturas con servicios en CRITICAL y WARNING y logs de eventos; sin cronología completa emparejada por prueba.

**Soporte, interpretación y límite.** Evidencia_Nagios_Incidencias.png.

#### 5.06 — Detección de failover Redis/Mongo

**Estado:** **PARCIAL:** ejecución existente, pero con limitación, error o métrica no obtenida.

**Procedimiento o diseño.** Correlacionar estados de Sentinel y Replica Set con checks de Nagios.

**Resultado observado / comportamiento esperado.** Se observaron eventos de falla y recuperación; no se verificó el tiempo exacto de detección por componente.

**Soporte, interpretación y límite.** Capturas y logs.

#### 5.07 — Tiempo MTTD y MTTR

**Estado:** **DISEÑADA / NO EJECUTADA:** caso documentado con comportamiento esperado; no se afirma que sucedió.

**Procedimiento o diseño.** Trazar instante de inyección de falla, primer CRITICAL, restauración y primer OK.

**Resultado observado / comportamiento esperado.** Sin marcas consistentes por incidente no se puede calcular un MTTD/MTTR válido.

**Soporte, interpretación y límite.** Procedimiento y campos de log definidos.

#### 5.08 — Alertas por correo u otro canal

**Estado:** **DISEÑADA / NO EJECUTADA:** caso documentado con comportamiento esperado; no se afirma que sucedió.

**Procedimiento o diseño.** Configurar contacto, comando de envío, umbrales y enviar incidente controlado.

**Resultado observado / comportamiento esperado.** No se demostró recepción externa; advertencias de contactos impiden calificarla de completada.

**Soporte, interpretación y límite.** Pendiente.

#### 5.09 — Métricas Docker de CPU/memoria

**Estado:** **PARCIAL:** ejecución existente, pero con limitación, error o métrica no obtenida.

**Procedimiento o diseño.** docker stats durante Load y Soak; guardar snapshots.

**Resultado observado / comportamiento esperado.** Se guardaron cinco muestras en Load y diez en Soak; no se completó interpretación longitudinal ni umbral de alerta.

**Soporte, interpretación y límite.** Archivos _docker_stats.txt / _stats.txt.

#### 5.10 — SLO p95 < 200 ms

**Estado:** **PARCIAL:** ejecución existente, pero con limitación, error o métrica no obtenida.

**Procedimiento o diseño.** Comparar percentiles de endpoints HTTP observados con objetivo operativo.

**Resultado observado / comportamiento esperado.** Smoke/Load/Stress/Spike/Soak reportan p95 inferiores a 200 ms en los escenarios medidos; no certifica todos los escenarios.

**Soporte, interpretación y límite.** Archivos de rendimiento y condiciones de prueba.

#### 5.11 — SLO de disponibilidad 99.9%

**Estado:** **DISEÑADA / NO EJECUTADA:** caso documentado con comportamiento esperado; no se afirma que sucedió.

**Procedimiento o diseño.** Medir uptime end-to-end durante periodo definido con alertas y exclusiones explícitas.

**Resultado observado / comportamiento esperado.** No hay muestra temporal suficiente para afirmar 99.9% en producción; tasas 0% error de tests acotados no prueban SLO anual.

**Soporte, interpretación y límite.** Pendiente.

#### 5.12 — Error budget / correlación observabilidad

**Estado:** **DISEÑADA / NO EJECUTADA:** caso documentado con comportamiento esperado; no se afirma que sucedió.

**Procedimiento o diseño.** Calcular presupuesto de fallos por ventana SLO y registrar porcentaje consumido.

**Resultado observado / comportamiento esperado.** Sin ventana y uptime real no existe presupuesto de error sustentado.

**Soporte, interpretación y límite.** Plantilla de cálculo disponible en el informe.

## 5. Incidencias, correcciones y decisiones técnicas

### 5.1 Bootstrap Galera y recuperación de estado

Al reiniciar la base de datos Galera se encontraron registros persistentes con `safe_to_bootstrap: 0`. La selección de un nodo seguro para arrancar un clúster detenido requiere examinar el estado real y los seqno; un cambio indiscriminado en `grastate.dat` puede provocar pérdida de datos o formación errónea del componente primario. Durante la resolución se recuperó el conjunto de tres nodos y se desarrolló un chequeo de HAProxy basado en `wsrep_cluster_status`, `wsrep_local_state_comment` y `wsrep_ready` para impedir dirigir peticiones a nodos que no están sincronizados. El incidente justifica omitir reinicios destructivos como experimento adicional en el mismo equipo.

### 5.2 MongoDB: replicación, keyfile y elecciones

La inicialización de `rs0` requirió configurar autenticación de miembros mediante keyfile y contenedores con la secuencia correcta. Posteriormente se confirmó `PRIMARY`/`SECONDARY`/`ARBITER`, y el nodo secundario se promovió al detener al anterior primario. Debe mantenerse controlado el archivo keyfile, sus permisos y el estado de volúmenes. Un árbitro participa en quorum, pero no almacena copias de los documentos de aplicación.

### 5.3 Redis Sentinel y descubrimiento del maestro

Se incorporaron tres Sentinels y réplica Redis para no depender exclusivamente de una instancia primario. Se comprobaron conmutaciones manual y automática y la reconexión posterior del servicio. El cliente debe utilizar descubrimiento de maestro mediante Sentinel de forma coherente en todas las API; un `REDIS_HOST=redis` estático en un fragmento de Compose, por sí solo, no garantiza failover transparente. El punto requiere corroboración final en el código realmente desplegado.

### 5.4 Cabeceras y trazabilidad

En la primera medición no se disponía de cabeceras que identificaran el Nginx respondiente. Se ajustó `web/nginx.conf` con `X-Web-Node` y `X-Presentation-LB`; se verificó sintaxis Nginx y se recargaron las tres instancias. Gracias a `x-request-trace` también se comprobó la rotación exacta de app1, app2 y app3 (5/5/5) en las quince solicitudes finales.

### 5.5 Fallo del comando mariadb-slap y corrección

Un primer intento de capacidad SQL devolvió `mariadb-slap: unknown variable 'default_character_set=utf8mb4'`, porque el cliente consumía opciones de configuración no compatibles con la herramienta. Se corrigió invocando `mariadb-slap --no-defaults`, ubicado antes de las demás opciones. El benchmark posterior concluyó sin error (0.150 s media, 0.147–0.156 s rango) y el endpoint de catálogo seguía respondiendo HTTP 200.

### 5.6 Bloqueo de prueba WEB3 y decisión de seguridad

Se intentó parar `web3` durante una secuencia de peticiones, pero el procedimiento quedó bloqueado y no devolvió la serie necesaria para cuantificar errores. Después se ejecutó `docker start distributed-three-tier-web3-1`; los tres web pasaron a `Up` y el sitio devolvió 200. Esta **evidencia confirma recuperación, no disponibilidad ininterrumpida** durante la falla. Se decidió detener nuevos ensayos destructivos y documentar los pendientes mediante simulaciones teóricas.

### 5.7 Nagios: advertencias de contactos

La comprobación de sintaxis de Nagios concluyó con cero errores, pero mostró quince advertencias por la configuración de contactos/contactgroup. El panel permite ver estados, y se capturaron incidentes; la entrega de alertas a una persona no quedó probada. Es incorrecto traducir estas advertencias a un sistema de notificaciones funcionando automáticamente.

## 6. Evaluación de objetivos y riesgos

### 6.1 Resultados demostrados

Las tres capas responden funcionalmente; los balanceadores distribuyeron peticiones entre los tres nodos web y API; Galera replicó un registro de prueba; MongoDB cambió de primario; Redis Sentinel promovió la réplica; Keepalived movió las VIP internas; y las pruebas HTTP de rendimiento terminaron con cero errores en las cargas medidas. Estos resultados respaldan funcionamiento de un prototipo distribuido y recuperación frente a varios fallos **simples y acotados**.

### 6.2 Resultados no acreditados

No se logró demostrar disponibilidad de 99.9% sobre una ventana significativa, RTO estricto de 3–4 segundos, resistencia a particiones Galera, recuperación total tras apagado en frío, ausencia de fugas en un soak de varias horas, capacidad máxima antes de saturación ni entrega de notificaciones Nagios fuera de la plataforma. Tampoco se obtuvo un failover WEB3 bajo carga concluyente ni se ejecutó el freeze de APP3.

### 6.3 Riesgos prioritarios y mitigaciones

| Prioridad | Riesgo | Impacto | Mitigación propuesta |
|---|---|---|---|
| Alta | `localhost:80` ligado al HAProxy master | Posible punto único de acceso externo | Proxy de entrada del host independiente o publicación estable del VIP, medir al detener master |
| Alta | Bootstrap Galera y quorum | Datos no accesibles / reinicio complicado | Backup de volúmenes, procedimiento verificado de recuperación WSREP, ensayo en clon |
| Alta | Cache/Redis descubierto mediante host fijo | Fallo de conexión tras promoción | Auditar configuración Sentinel del cliente en todas las API y probar bajo carga |
| Alta | MTTD/MTTR y SLO no medidos | Cumplimiento no demostrable | Sondas continuas con marcas temporales y ventana definida |
| Media | Alertas Nagios no entregadas | Incidentes sin aviso | Configurar contactos/canales y ensayar envío |
| Media | Soak de solo 10 minutos | No detectar fugas progresivas | Ejecutar soak de varias horas en máquina con recursos |
| Media | Cache Effect interrumpido | Beneficio global del caché sin conclusión robusta | Revisar condición inválida y repetir 25 pares con aislamiento |
| Media | Compose adjunto vs últimos cambios | Documentación desactualizada | Exportar `docker compose config` definitivo, revisar archivos de proxy y Sentinel |

## 7. Evidencias y estructura del repositorio

### 7.1 Registro de evidencias

| ID | Evidencia | Soporte o estado |
|---|---|---|
| 01 | Baseline Galera y VIP | Captura referida en las pruebas previas; no adjunta aquí |
| 02 | Round Robin Web 5/4/3 | Captura referida previamente; no adjunta aquí |
| 03 | Cabeceras de balanceo Web | Captura referida previamente; no adjunta aquí |
| 04 | Consistencia Galera | Captura referida previamente; no adjunta aquí |
| 05 | Redis Cache Hit/Miss | Captura referida previamente; no adjunta aquí |
| 06 | Smoke | Archivos smoke CSV/JSON en repositorio local |
| 07 | Load | Archivos load CSV/JSON y docker stats |
| 08 | Stress | Archivos stress CSV/JSON |
| 09 | Spike | TXT/JSON k6 |
| 10 | Soak | TXT/JSON y muestras Docker stats |
| 11 | Cache Effect parcial | CSV/JSON con `all_valid=false` |
| 12 | Capacidad por capa | k6 web/app, TXT Galera con benchmark corregido |
| 13 | Recuperación WEB3 y acceso APP1/2/3 | Salida de terminal, HTTP 200 |
| 14 | Balanceo de API | Captura incluida en carpeta evidencias |
| Nagios | Estado de servicios/hosts e incidencias | Tres capturas incluidas como anexos |

Los nombres anteriores son referencias para ordenar evidencia; no se sustituyen resultados ausentes por imágenes generadas ni capturas falsas.

### 7.2 Organización sugerida de archivos

```text
README.md
TODO.md
TEST-PLAN.md
DOCUMENTACION_INTEGRAL.md
TODO_ESTADO.md
docker-compose.yml
application/
web/
haproxy/
keepalived/
redis/
database/
nagios/
tests/
  performance/
    smoke.py
    load.py
    stress.py
    spike.js
    soak.js
    cache_effect.py
    capacity.js
    results/
  ha/
    results/
evidencias/
```

Los scripts se listan porque fueron creados o empleados durante la sesión; confirma cuáles están versionados antes de publicar en GitHub. Nunca subir `.env`, keyfiles, contraseñas ni copias de volúmenes con datos.

### 7.3 Evidencias gráficas disponibles

**Figura 1 — Balanceo real entre tres API (15 HTTP 200):**

![Balanceo API con trace de app1, app2, app3](evidencias/Evidencia_14_Balanceo_API.png)

**Figura 2 — Panel Nagios: estado de servicios:**

![Panel de servicios monitoreados](evidencias/Evidencia_Nagios_Servicios.png)

**Figura 3 — Panel Nagios: incidencias / avisos:**

![Nagios con incidencias registradas](evidencias/Evidencia_Nagios_Incidencias.png)

## 8. Cómo se habrían documentado las simulaciones pendientes

Para no omitir casos del plan, cada escenario diseñado se describe con una hipótesis falsable y un criterio de aceptación medible. Por ejemplo:

**Simulación teórica A: congelar APP3.** Hipótesis: HAProxy detectaría el backend no responsivo, retiraría app3 de la selección y las solicitudes siguientes se repartirían entre app1 y app2. Procedimiento real pendiente: `docker pause app3`, 15–100 GET con tiempo, capturar x-request-trace, `docker unpause app3` y verificar recuperación. Aceptación: mayoría de respuestas HTTP 200 después de la detección, ningún backend permanentemente caído y logs correlacionados. **Resultado:** no ejecutado; no se asigna un porcentaje ficticio.

**Simulación teórica B: pérdida de un servidor Galera.** Hipótesis: Galera seguiría operando en componente primario con dos nodos sincronizados y el proxy excluiría el caído. Aceptación: ausencia de 500, `wsrep_cluster_size=2`/`Primary` mientras falla, y recuperación controlada al reingresar. **Resultado:** no medido como falla controlada final; no extrapolar replicación normal a failover demostrado.

**Simulación teórica C: latencia y paquetes perdidos.** Hipótesis: aumentar RTT de aplicación a base de datos aumentaría p95 y podría activar timeouts. Aceptación: reportar distribución real de latencias, errores y recuperación al retirar netem. **Resultado:** procedimiento conceptual, sin números experimentales.

**Simulación teórica D: todas las dependencias indisponibles.** Hipótesis: pérdida total de Galera, MongoDB o Redis afectaría distintas rutas según los mecanismos reales de fallback. Aceptación: clasificar 2xx/4xx/5xx por endpoint, que no se pierdan cambios confirmados y que recupere cuando vuelvan dependencias. **Resultado:** no ejecutado, no adjudicar degradación elegante sin verla.

**Simulación teórica E: ventana de SLO.** En un periodo total de `T` minutos, con `F` minutos de indisponibilidad validada, la disponibilidad sería `100 × (T − F) / T`. Para disponibilidad objetivo 99.9%, el presupuesto máximo orientativo de fallas es `0.001 × T`; por ejemplo, 43.2 minutos de un periodo de 30 días. No hay una serie de producción suficiente para calcular el cumplimiento real.

## 9. Conclusiones

El proyecto cumple su propósito de prototipo distribuido y muestra en condiciones normales una arquitectura operacional de tres capas, balanceo demostrable, replicación y almacenamiento redundante, failovers simples seleccionados y resultados de rendimiento medidos. Su fortaleza principal es la combinación de trazabilidad por cabeceras, validación explícita de consistencia y pruebas repetibles con archivos de salida.

Las principales limitaciones están en el laboratorio de ejecución, la falta de medición continua del tiempo de recuperación, los escenarios destructivos no realizados, la prueba parcial de caché y el alertamiento externo de Nagios no validado. Reportar estas limitaciones es parte del análisis experimental: distingue lo comprobado del comportamiento teórico. Con un host de pruebas adicional, copias verificadas de los volúmenes y una herramienta de inyección de fallas controlada, sería posible completar el programa pendiente sin comprometer el proyecto principal.

## 10. Anexo: instrucciones breves de reproducibilidad

```bash
# Comprobar sintaxis/configuración Compose
docker compose config --quiet

# Estado de nodos y dependencias
docker compose ps

# API funcional con cabeceras
curl -i --max-time 10 http://localhost/api/products/cheapest

# Limpiar entrada de caché
curl -X POST --max-time 10 http://localhost/api/cache/clear

# Recursos mientras corre carga
docker stats --no-stream

# Logs del monitor
docker compose logs --tail 100 nagios

# Condición final imprescindible tras cualquier fallo controlado
curl -fsS -o /dev/null -w '%{http_code}
' http://localhost/api/products/cheapest
```

Cualquier comando destructivo omitido en el informe requeriría primero definir criterio de aborto, mecanismo de recuperación, respaldo y ventana de observación. Los archivos `tests/performance/results/*` deben conservarse sin modificación como fuente primaria de las estadísticas citadas.