# Cobertura del TEST-PLAN — Matriz de control

Esta matriz cubre los ejes identificados de las cinco secciones, sin afirmar reproducir literalmente el documento original (no adjunto). Los números siguientes son identificadores creados para la documentación, no el índice oficial del archivo ausente. Consulte `DOCUMENTACION_INTEGRAL.md` para procedimiento, resultado e interpretación de cada caso.

**Leyenda:** V: verificada; P: parcial; D: diseñada/no ejecutada; R: no recomendada en este entorno.

| ID | Prueba | Estado | Interpretación breve |
|---|---|---|---|
| 1.01 | Despliegue y salud general | V | Los componentes principales iniciaron; Galera en Primary/Synced, servicios API y web respondiendo 200. |
| 1.02 | Aislamiento de tres capas y redes | V | Tres redes lógicas definidas; Node, Nginx y MariaDB accesibles desde su propio contenedor. |
| 1.03 | Tres nodos Nginx y respuesta funcional | V | Las solicitudes se atienden por webnode1, webnode2 y webnode3 con HTTP 200. |
| 1.04 | Round robin en presentación | V | 12 respuestas HTTP 200 distribuidas 5/4/3 entre los tres Nginx. |
| 1.05 | Identificación de nodos por cabeceras | V | Las respuestas exponen X-Web-Node y X-Presentation-LB con sus nombres correctos. |
| 1.06 | Distribución balanceada de API | V | HTTP 200 en 15/15; app1=5, app2=5, app3=5; web1/2/3 identificados. |
| 1.07 | Endpoint de salud y rutas críticas | V | Se observó HTTP 200 en salud y catálogo; las consultas posteriores al benchmark también devolvieron 200. |
| 1.08 | Integridad de datos en Galera | V | Se recuperó el mismo registro desde los tres nodos; la tabla temporal se eliminó al finalizar. |
| 1.09 | Caché Redis: MISS y HIT | V | Primer GET con cache miss y consulta Galera; segundo con cache hit; catálogo coincidente. |
| 1.10 | Replica Set MongoDB | V | PRIMARY, SECONDARY y ARBITER observados; cambio de PRIMARY también probado. |
| 1.11 | Redis Sentinel | V | Redis Sentinel promovió réplica; servicio restituido posteriormente. |
| 1.12 | Monitoreo inicial Nagios | P | Portal en localhost:8088 requiere autenticación; checks registrados; advertencias por contactos no configurados. |
| 1.13 | Inicialización idempotente de catálogo y réplica Mongo | P | Los contenedores de inicialización existen y la aplicación respondió; no consta ensayo formal de idempotencia repetida. |
| 1.14 | Verificación negativa de rutas no existentes | D | Debe responder 404 controlado; el caso no tiene medición aportada. |
| 2.01 | Smoke 1 usuario / 20 segundos | V | 120 solicitudes, 0 errores, 5.96 req/s; p50=19.25 ms, p95=29.69 ms, p99=32.92 ms. |
| 2.02 | Smoke 5 usuarios / 20 segundos | V | 604 solicitudes, 0 errores, 29.96 req/s; p50=16.19 ms, p95=29.76 ms, p99=32.63 ms. |
| 2.03 | Load 10 usuarios / 10 minutos | V | 21,897 solicitudes, 0 errores; 36.48 req/s; p50=19.58 ms, p95=23.80 ms, p99=31.32 ms; 600.27 s. |
| 2.04 | Stress escalonado hasta 30 usuarios | P | 13,514 solicitudes totales, 0 errores; throughput máximo observado 244.63 req/s a 30 usuarios, p95=58.43 ms, p99=93.40 ms. No se encontró el punto de ruptura. |
| 2.05 | Spike 300 usuarios virtuales | V | 5,256 solicitudes, 0 fallos; 149.43 req/s global; p50=23.82 ms, p95=112.14 ms, p99=169.43 ms, máximo 228.59 ms. |
| 2.06 | Soak prolongado | P | 9,867 solicitudes, 0 errores, 16.43 req/s; p50=6.58 ms, p95=13.84 ms, p99=20.97 ms. No demuestra estabilidad de varias horas. |
| 2.07 | Cache Effect: 25 pares MISS/HIT | P | 13 pares válidos de 25 planificados; la comparación 14 invalidó la ejecución. En 13 pares: miss p50=15.27 ms/p95=36.63 ms; hit p50=11.34 ms/p95=25.74 ms. |
| 2.08 | Capacidad por capa: Nginx web1 | V | 930 solicitudes, 0 errores, 46.34 req/s, promedio 6.82 ms, p95=11.87 ms, p99=19.17 ms. |
| 2.09 | Capacidad por capa: Node.js app1 | V | 976 solicitudes, 0 errores, 48.56 req/s, promedio 1.63 ms, p95=2.66 ms, p99=6.84 ms. |
| 2.10 | Capacidad por capa: MariaDB Galera1 | V | Promedio 0.150 s por iteración, mínimo 0.147 s, máximo 0.156 s; catálogo final HTTP 200. |
| 2.11 | Saturación hasta determinar capacidad máxima | R | No realizada: equipo de recursos limitados y riesgo de desestabilizar Galera/containers. No inferir capacidad máxima de los niveles probados. |
| 3.01 | VIP de presentación pasa al backup | V | VIP se desplazó al backup y regresó al master; acceso HTTP por la VIP confirmado. |
| 3.02 | VIP de aplicación pasa al backup | V | VIP se desplazó al backup y regresó al master; servicio accesible por la VIP. |
| 3.03 | Congelamiento HAProxy en presentación | V | Track HTTP detectó indisponibilidad; backup tomó VIP y posteriormente volvió a master. |
| 3.04 | Congelamiento HAProxy en aplicación | V | Se observó conmutación de VIP al backup y recuperación posterior. |
| 3.05 | Tiempo RTO de cambios de VIP | P | Se comprobó continuidad en verificaciones puntuales, pero no se midió RTO/RPO ni una serie de errores por segundo. |
| 3.06 | Pérdida de web3 bajo carga | P | El ensayo quedó bloqueado; posteriormente web3 se reinició y web1/web2/web3 quedaron Up, HTTP final 200. No concluyente sobre disponibilidad durante falla. |
| 3.07 | Caída controlada de web1 | D | Con web2/web3 operativos el balanceador debería responder 200; sin ejecución confirmada. |
| 3.08 | Falla simultánea de web1 y web2 | D | Se esperaría disponibilidad con reducción de capacidad; sin medición ni captura. |
| 3.09 | Indisponibilidad de los tres Nginx | D | Se espera error 503 o equivalente en HAProxy. No se provocó para evitar interrupción global. |
| 3.10 | Respuesta directa de app1, app2, app3 | V | HTTP 200 en las tres API y en el VIP de aplicación; contenedores Up. |
| 3.11 | Balanceo efectivo de las tres API | V | app1=5, app2=5, app3=5, todas HTTP 200. |
| 3.12 | Congelamiento individual de app3 | D | Se espera reasignación a app1/app2. El bloque se propuso, pero no se ejecutó ni se obtuvo salida. |
| 3.13 | Caída simultánea de app1 y app2 | D | Se espera degradación de capacidad con la tercera API disponible; no verificado. |
| 3.14 | Pérdida de todas las API | D | Se espera 503 desde HAProxy de aplicaciones; no realizado. |
| 3.15 | Elección de PRIMARY MongoDB | V | mongodb2 asumió PRIMARY y mongodb se reintegró como SECONDARY. |
| 3.16 | Pérdida simultánea de mayoría MongoDB | R | Sin quorum no hay escritura disponible; no ejecutado por riesgo de recuperación y datos. |
| 3.17 | Redis Sentinel failover automático | V | Promoción de réplica probada y lectura/escritura del servicio recuperadas. |
| 3.18 | Redis Sentinel failover manual | V | Cambio de primario realizado y restauración probada. |
| 3.19 | Fallo simultáneo de Redis y su réplica | D | Sin instancia de datos, el caché no puede servir; respuesta API depende de lógica de degradación. No medido. |
| 3.20 | Galera: proxy con validación WSREP | V | Se observó backend Galera con tres nodos UP y consultas HTTP 200; proxy evita nodos no Synced. |
| 3.21 | Galera: caída de un nodo | P | Se había presentado un problema de arranque safe_to_bootstrap; posteriormente se recuperó clúster de tres. No hay medición controlada de disponibilidad durante la falla final. |
| 3.22 | Galera: caída de dos nodos/quorum | R | No ejecutada deliberadamente: riesgo de quorum, SST/IST, safe_to_bootstrap y recuperación compleja. |
| 3.23 | Reinicio total y recuperación de todo el stack | R | No ejecutada: un bootstrap incorrecto de Galera con estado persistente puede impedir recuperar el cluster. |
| 3.24 | Punto único de fallo del ingreso externo | P | VIP funciona internamente, pero el puerto 80 del host está publicado solo por presentation-lb-master en el Compose aportado. La continuidad de localhost:80 tras su parada no está probada. |
| 4.01 | Contenedor web: parada abrupta | P | Intento con web3 se bloqueó; se recuperó web3, sin datos concluyentes de RTO ni error-rate. |
| 4.02 | Contenedor API: freeze temporal | D | Tráfico debería abandonar backend no responsivo; sin ejecución observada. |
| 4.03 | Balanceador master detenido | V | VIP migra al backup en presentación y aplicación, y vuelve al recuperar. |
| 4.04 | MongoDB PRIMARY detenido | V | Elección de nuevo PRIMARY y unión del antiguo primario como SECONDARY. |
| 4.05 | Redis PRIMARY detenido | V | Sentinel redistribuyó el rol y el servicio se recuperó. |
| 4.06 | Galera individual degradado | P | Chequeo WSREP y acceso normal demostrados; caída programada con medición no completada. |
| 4.07 | Latencia artificial de red entre capas | D | Se espera incremento de latencia y posible timeout al alcanzar límites; no se configuró netem. |
| 4.08 | Pérdida de paquetes hacia MongoDB | D | Se espera reintento/error transitorio según timeout MongoDB; no ejecutado. |
| 4.09 | Partición de red en Galera | R | Arriesga quorum y divergencia/transacciones; sin ejecución. |
| 4.10 | Aislamiento de web1 en red edge | D | HAProxy debería retirar backend inaccesible; requiere preservar nombre/aliases y estado. |
| 4.11 | Límite de memoria a aplicación | D | Es esperable degradación/OOM si se supera el límite; no ejecutado por memoria local reducida. |
| 4.12 | CPU throttling en Node.js | D | Se espera aumento de duración en el nodo limitado y posible exclusión si deja de responder. |
| 4.13 | Disco lleno en volumen de base de datos | R | Puede corromper o bloquear recuperación; expresamente omitido. |
| 4.14 | Fallos de DNS interno | D | Se espera error de conexión dependiente del resolver y retries; no probado. |
| 4.15 | Desfase de reloj / clock skew | R | No se realizó: Docker comparte reloj kernel del host en gran medida; manipulación puede afectar todos los servicios. |
| 4.16 | Dependencia MongoDB indisponible | D | El comportamiento real depende de la implementación; no se observa respuesta en falla total. |
| 4.17 | Dependencia Redis indisponible | D | El fallback no está confirmado; no afirmar que la API mantiene HTTP200. |
| 4.18 | Dependencia Galera no disponible | D | Se espera fallo controlado en endpoints SQL; código preciso y recuperación no medidos. |
| 4.19 | Fallas compuestas Redis + API | D | Se requiere evaluar errores correlacionados, RTO y recuperaciones; no se ejecutó. |
| 4.20 | Fallas aleatorias estilo Chaos Monkey | D | No se ejecutó selección aleatoria reproducible; se propuso como experimento futuro. |
| 4.21 | Reinicio completo / cold start caótico | R | No realizado por riesgos Galera, Mongo elections y recursos limitados. |
| 5.01 | Acceso web y autenticación Nagios | V | Servicio protegido; 401 sin autenticación es respuesta esperada, no caída. |
| 5.02 | Validación de configuración Nagios | P | 0 errores y 15 advertencias relativas a contacto/contactgroup; la configuración carga pero notificaciones pendientes. |
| 5.03 | Inventario de hosts monitoreados | V | Se observaron 15 hosts y sus servicios en panel de monitoreo. |
| 5.04 | Captura de estado de servicios | V | Dashboard muestra estados OK/WARNING/CRITICAL de acuerdo con la captura del momento. |
| 5.05 | Incidencias y recuperaciones en Nagios | P | Existen capturas con servicios en CRITICAL y WARNING y logs de eventos; sin cronología completa emparejada por prueba. |
| 5.06 | Detección de failover Redis/Mongo | P | Se observaron eventos de falla y recuperación; no se verificó el tiempo exacto de detección por componente. |
| 5.07 | Tiempo MTTD y MTTR | D | Sin marcas consistentes por incidente no se puede calcular un MTTD/MTTR válido. |
| 5.08 | Alertas por correo u otro canal | D | No se demostró recepción externa; advertencias de contactos impiden calificarla de completada. |
| 5.09 | Métricas Docker de CPU/memoria | P | Se guardaron cinco muestras en Load y diez en Soak; no se completó interpretación longitudinal ni umbral de alerta. |
| 5.10 | SLO p95 < 200 ms | P | Smoke/Load/Stress/Spike/Soak reportan p95 inferiores a 200 ms en los escenarios medidos; no certifica todos los escenarios. |
| 5.11 | SLO de disponibilidad 99.9% | D | No hay muestra temporal suficiente para afirmar 99.9% en producción; tasas 0% error de tests acotados no prueban SLO anual. |
| 5.12 | Error budget / correlación observabilidad | D | Sin ventana y uptime real no existe presupuesto de error sustentado. |

**Criterio de cierre:** ninguna prueba D/R se considera satisfactoria por el solo hecho de describir el comportamiento esperado; P exige medir o justificar su limitación.