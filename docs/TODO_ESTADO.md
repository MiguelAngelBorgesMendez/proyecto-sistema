# Seguimiento del proyecto — TODO (estado al 26/10/2026)

**Aviso:** este es un `TODO_ESTADO.md` reconstruido con el Compose y la conversación. No reemplaza ni marca automáticamente como completado el `TODO.md` original porque ese archivo no se recibió completo. El carácter `[x]` señala un hito demostrado, `[~]` indica parcial y `[ ]` pendiente por confirmar/ejecutar.

## Arquitectura e inicialización

- [x] Desplegar tres Nginx y tres aplicaciones Node.js operativos.
- [x] Configurar pares HAProxy/Keepalived master/backup con VIP internas de presentación y aplicación.
- [x] Comprobar cabeceras identificadoras de nodos web y trace de las API.
- [x] Configurar MongoDB `rs0` con dos nodos de datos y árbitro; verificar elección de primario.
- [x] Incorporar autenticación mediante keyfile Mongo y tarea `mongo-init-replica`.
- [x] Configurar Redis primario, réplica y tres Sentinels; verificar failover manual/automático.
- [x] Configurar tres Galera y validar sincronización y replicación de registro temporal.
- [~] Persistir y revisar en GitHub la versión final del proxy Galera con chequeo WSREP (en el material aportado aparece otra configuración anterior).
- [x] Incluir `catalog-init` y verificar respuesta del catálogo.
- [~] Confirmar idempotencia de inicializadores con prueba repetida.
- [~] Confirmar descubrimiento dinámico Sentinel/Mongo en todos los clientes desplegados.

## Testing funcional y rendimiento

- [x] Baseline de los tres nodos web, round robin y tres aplicaciones.
- [x] Consistencia de Galera y prueba de caché HIT/MISS.
- [x] Smoke y Load con resultados archivados.
- [~] Stress hasta 30 usuarios sin fallo; falta capacidad máxima.
- [x] Spike hasta 300 VU en la ventana probada.
- [~] Soak de 10 minutos; falta duración de varias horas.
- [~] Cache Effect: 13 de 25 pares válidos, fallo de condición en el par 14.
- [x] Capacidad por capa web/app/SQL, con corrección `mariadb-slap --no-defaults`.

## Alta disponibilidad y caos

- [x] VIP interna de Keepalived migra en presentación y aplicación.
- [x] Congelamiento HAProxy master y recuperación de las VIP.
- [x] Elección de MongoDB y promoción Redis Sentinel.
- [~] WEB3: ejecución de caída bajo carga bloqueada; recuperación posterior HTTP 200.
- [ ] APP3 `docker pause/unpause` con medición bajo carga.
- [ ] RTO medido de cada failover en segundos.
- [ ] Retirada simultánea de múltiples webs o APIs en laboratorio.
- [ ] Falla controlada de nodo Galera bajo sonda continua y quorum.
- [ ] Chaos con latencia/pérdida de paquetes/CPU limitada/fallas compuestas.
- [ ] Particiones Galera/reinicio total solo en laboratorio aislado con backup.
- [ ] Validar entrada externa `localhost:80` cuando se pierde `presentation-lb-master`.

## Observabilidad, seguridad y entrega

- [x] Ejecutar Nagios y mostrar panel de hosts y servicios.
- [~] Configuración sintácticamente válida, pero 15 advertencias de contactos.
- [ ] Probar envío real de alertas a correo u otro destino.
- [ ] Calcular MTTD, MTTR, uptime 99.9% y error budget en ventana temporal.
- [x] Redactar informe que distingue resultados reales, parciales y simulaciones teóricas.
- [ ] Revisar que las cifras citadas correspondan a archivos de `tests/performance/results` del repositorio.
- [ ] Adjuntar capturas 01–13 faltantes si están en el equipo local.
- [ ] Revisar `.gitignore` para `.env`, volúmenes, keyfiles y secretos antes de publicar.
- [ ] Comparar la lista anterior con el `TODO.md` original y reconciliar diferencias.

## Orden recomendado de cierre

1. Hacer backup y verificar cambios finales del Compose y de los scripts de Redis/Galera.
2. Corregir alertas Nagios y revisar el enrutamiento externo de ingreso.
3. Completar Cache Effect y una prueba de APP3 con instrumentación de RTO.
4. Ejecutar las pruebas destructivas pendientes en un entorno clon separado.
5. Archivar CSV/JSON/TXT sin alteración y completar carpeta de evidencias.