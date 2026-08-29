# EPI-Aetheris — Resumen

> **Para el lector IA:** este es el punto de entrada al contexto del proyecto. Para decisiones ya cerradas, `01-decisiones-cerradas.md`. Para lo que sigue sin resolver, `02-decisiones-abiertas.md` — no invente respuesta a nada que esté ahí, pregunte. Para la evidencia empírica detrás de cada fuente de datos, `03-fuentes-de-datos.md`. Para el historial completo sesión a sesión, `CHANGELOG.md`. Los cuatro archivos son más largos que este; léalos solo cuando la pregunta lo requiera, no por defecto.

## Qué es

EPI-Aetheris es un sistema **open-source, contenedorizado y desplegable a costo cero** que cruza datos públicos históricos de casos de dengue con variables climáticas, piloteado en El Salvador. **El objetivo original — clasificar el riesgo de brote (alto/medio/bajo) por semana epidemiológica — quedó cerrado el 2026-08-18** (`docs/informe-cierre-rescate-prediccion.md`): cinco vías de validación no sostuvieron capacidad predictiva real en los años con brote conocido. El proyecto pivotó a **"Camino Ancho"**: una herramienta descriptiva, no predictiva, de análisis espacio-temporal, organizada en cuatro módulos (M1 idoneidad biofísica e M2 anomalía climática continua ya implementados; M3 presión epidemiológica relativa e M4 confianza de vigilancia sin fórmula aprobada todavía). Ver "Pivote 'Camino Ancho'" en `01-decisiones-cerradas.md` para el detalle completo. El mapa sigue pintando datos departamentales de MINSAL como capa descriptiva — nunca como salida de un clasificador, porque ya no hay ninguno en producción. La arquitectura es agnóstica al tipo de evento y a la región — dengue/El Salvador es el caso piloto, no el límite.

**Lo que NO es:** ni un descubrimiento científico ni "predecir dengue con IA" (eso ya existe en la literatura, y de hecho el propio intento de predicción de este proyecto se cerró sin adoptarse). El aporte es de **ingeniería de software**: entregar como sistema reproducible y gratuito una capa de integración, trazabilidad y exploración histórica que la academia no publica como software. Ver `01-decisiones-cerradas.md` para el posicionamiento frente al estado del arte.

**Nombre:** el vigente es **EPI-Aetheris**. "EPI Aethery" fue un error de transcripción (jul–30 jul 2026) y "EPICAST" es el codename histórico de ideación — ninguno de los dos en material nuevo.

## Equipo e institución

- **INSAMT** (Instituto Nacional de San Miguel Tepezontes), El Salvador. Estudiantes de 3er año de Bachillerato Técnico Vocacional en Desarrollo de Software, Equipo 4.
- Se presenta en **Expotécnica** (evaluador: Prof. William Mejía), asignatura Desarrollo de Software.
- 5 integrantes totales, **3 dedicados full a programación**. El coordinador (GitHub `0V3R`, Eduardo) es uno de los 3, con rol específico de **revisor técnico y QA** dentro del trío — no solo integrador externo al código.
- **Plazo:** MVP en 2 meses máximo desde la selección de propuesta.
- Repositorio: `github.com/the-monolith-project/EPI-Aetheris`, rama principal `main` con protección activa.

## El problema

El dengue es endémico en El Salvador. La respuesta institucional es mayoritariamente reactiva pese a que existe correlación científicamente documentada entre incidencia y clima (temperatura, lluvia, humedad) con semanas de rezago. Falta una herramienta local, desplegable y gratuita que cruce casos con clima para anticipar riesgo. Público objetivo: unidades de epidemiología y tomadores de decisión que priorizan fumigación, campañas y recursos.

## Marco metodológico (TMP-STC)

Toda decisión se evalúa contra tres pilares, con exigencia de honestidad brutal, no validación complaciente:

- **Pilar 1 — Utilidad:** problema real, medible, urgente, con público objetivo definido.
- **Pilar 2 — Aplicación:** open-source, modular, portable, costo de replicación → 0. Self-hosting se prefiere sobre SaaS de terceros, pero **no es mandato incondicional** — se evalúa caso por caso contra el Pilar 3 (ejemplo real: self-hosting de Open-Meteo evaluado y descartado, ver `01-decisiones-cerradas.md`).
- **Pilar 3 — Reconocimiento:** realismo técnico/financiero. Costos ocultos auditados, márgenes de error declarados, prohibidos los atajos ("nadie se va a dar cuenta").

**Clasificación CIMT:** principal Tecnología (T); secundarias Matemática (M — modelado, features, estadística) y Ciencia (C — dominio epidemiológico, validación).

## Propuestas descartadas antes de EPI-Aetheris

No re-proponer estos caminos:

- **AULA-PULSE** (deserción escolar): requería datos personales de menores; sin dataset público, fabricar uno se consideró deshonesto y éticamente inaceptable.
- **PHISH-GUARD** (phishing): campo saturado, sin aporte nuevo posible en 2 meses.
- **GRID-SENSE** (anomalías de consumo eléctrico): riesgo de datos insuficientes para una demo convincente.
- **Fabricar datasets propios: prohibido**, como principio del proyecto, no solo preferencia — ver `01-decisiones-cerradas.md`.

## Preferencias de trabajo del usuario

- Exige evaluación técnica honesta y directa, no enmarcado optimista; quiere riesgos reales declarados.
- Desarrollador web con perfil Linux/open-source (CachyOS/Arch); trabaja con Node.js, Astro, TypeScript, Tailwind, Supabase, Docker, GitHub Actions.
- Español neutro: sin voseo ni modismos regionales (ni salvadoreños ni argentinismos).
- Sin emojis en respuestas técnicas o de código.
- Prefiere texto mínimo y diseño limpio en entregables.
