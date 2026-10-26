# Proyecto Sistema — Arquitectura distribuida de tres capas

Repositorio académico para el sistema distribuido implementado con **Docker Compose, HAProxy, Keepalived, Nginx, Node.js, MariaDB Galera, MongoDB Replica Set, Redis Sentinel y Nagios**.

**Autor:** Miguel Angel Borges Mendez  
**Fecha de documentación:** 26 de octubre de 2026.

## Documentación principal

Estas son las dos páginas completas preparadas para la **Wiki**:

1. [Desarrollo y arquitectura del proyecto](wiki/01-Desarrollo-y-Arquitectura.md): objetivos, arquitectura, componentes, construcción, configuración, dificultades y decisiones técnicas **antes de las pruebas**.
2. [Plan de pruebas y resultados](wiki/02-Plan-de-Pruebas-y-Resultados.md): metodología, resultados medidos y **82 casos** de las secciones 1 a 5, con su estado real, incidencias y limitaciones.

**Importante:** la Wiki de GitHub es un repositorio Git separado. Estas páginas se conservan aquí como fuente editable mientras se publican en la pestaña **Wiki**; su presencia aquí no implica que ya estén visibles en la Wiki.

## Estado de la entrega

La documentación está publicada en este repositorio. El **código completo del proyecto aún debe subirse desde el equipo donde está la carpeta `~/Desktop/distributedsystems`**, pues el acceso conectado a GitHub no tiene acceso al contenido de esa carpeta local.

El sistema se ha probado en condiciones concretas de laboratorio, pero **no se afirma que las pruebas pendientes hayan sido superadas**. El análisis diferencia entre verificado, parcial, diseñado y de riesgo.

## Seguridad antes de subir el código

No subir `.env` reales, contraseñas, tokens, keyfiles de MongoDB, claves privadas, volúmenes persistentes ni bases de datos exportadas con datos privados. Usar `.env.example` con marcadores de posición. Conservar los scripts, archivos Compose, configuraciones sin secretos y los registros de pruebas que no incluyan credenciales.

## Wiki

En el repositorio, abrir **Wiki**, crear la primera página **Home** si GitHub lo solicita y después copiar los Markdown de `wiki/` al repositorio `proyecto-sistema.wiki.git` mediante Git Bash. Los pasos concretos se facilitan junto con esta entrega.
