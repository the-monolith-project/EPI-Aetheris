# EPI-Aetheris — Contexto del proyecto

> **Para el lector IA:** este archivo ya no contiene el contexto en sí — vive en `docs/contexto/`, dividido por función de consulta en vez de en un solo documento de ~400 líneas. Empezar por los dos primeros; no cargar los demás salvo que la pregunta lo requiera.

- [`docs/contexto/00-resumen.md`](docs/contexto/00-resumen.md) — qué es el proyecto, equipo, marco TMP-STC, preferencias del usuario.
- [`docs/contexto/01-decisiones-cerradas.md`](docs/contexto/01-decisiones-cerradas.md) — decisiones cerradas/no negociables. Consultar antes de proponer stack, esquema, fuentes o alcance.
- [`docs/contexto/02-decisiones-abiertas.md`](docs/contexto/02-decisiones-abiertas.md) — lo que sigue sin resolver. No inventar respuesta a nada de aquí, preguntar.
- [`docs/contexto/03-fuentes-de-datos.md`](docs/contexto/03-fuentes-de-datos.md) — evidencia empírica y trampas de ingesta por fuente: OpenDengue, boletines MINSAL (dengue, neumonías y vigilancia viral), Open-Meteo y el ONI de NOAA. Referencia profunda, no lectura por defecto.
- [`docs/contexto/CHANGELOG.md`](docs/contexto/CHANGELOG.md) — historial completo sesión a sesión. Consultar solo para el "por qué y cuándo", no para el estado actual.

Ver también `docs/adr/` para las decisiones registradas en formato ADR, independientes de este contexto: empezó siendo el registro de cambios de esquema (toda migración exige ADR previo) y hoy incluye también decisiones de fuente, producto y método sin migración asociada — por ejemplo la 0019 (integridad de la vigilancia) y la 0020 (predicción de casos a corto plazo) y `AGENTS.md` en la raíz para convenciones de código.
