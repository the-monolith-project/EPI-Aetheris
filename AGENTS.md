# EPI-Aetheris — Agent Instructions

Este archivo define cómo deben trabajar los agentes de programación dentro de este repositorio.

Su propósito es indicar **qué fuentes consultar, qué reglas respetar y cómo proceder antes de modificar código**. No duplica la documentación de `docs/`, salvo el contexto técnico consolidado en la sección 17 (antes en un `CLAUDE.md` aparte).

---

## 1. Punto de entrada obligatorio

Antes de realizar cambios relevantes, lee:

`docs/contexto/00-resumen.md`

Ese archivo es el punto de entrada al contexto de EPI-Aetheris.

No cargues toda la documentación por defecto. Consulta archivos adicionales únicamente cuando sean relevantes para la tarea.

---

## 2. Fuentes de autoridad del proyecto

### Contexto general

`docs/contexto/00-resumen.md`

Contiene:

* alcance actual del proyecto;
* propósito de EPI-Aetheris;
* estado general;
* restricciones principales;
* referencias hacia documentación más detallada.

### Decisiones cerradas

`docs/contexto/01-decisiones-cerradas.md`

Contiene decisiones ya tomadas por el equipo.

No reabras, contradigas o reemplaces una decisión cerrada sin una instrucción explícita del coordinador o del usuario.

### Decisiones abiertas

`docs/contexto/02-decisiones-abiertas.md`

Contiene asuntos que todavía requieren evidencia, implementación, validación o decisión del equipo.

**No inventes una respuesta para cerrar estos puntos.**

Si una tarea depende directamente de una decisión abierta:

1. identifica la dependencia;
2. explica qué información falta;
3. evita convertir una hipótesis en una decisión oficial.

### Fuentes y evidencia de datos

`docs/contexto/03-fuentes-de-datos.md`

Consulta este archivo antes de:

* modificar pipelines de ingestión;
* interpretar datos epidemiológicos;
* interpretar variables climáticas;
* modificar transformaciones;
* cambiar agregaciones;
* introducir nuevas fuentes;
* corregir supuestos sobre MINSAL, OpenDengue u Open-Meteo.

Las particularidades empíricas documentadas aquí tienen prioridad sobre suposiciones generales acerca de esas fuentes.

### Historial

`docs/contexto/CHANGELOG.md`

Contiene historial detallado del proyecto.

Úsalo cuando necesites saber:

* por qué existe determinado comportamiento;
* cuándo se produjo un cambio;
* qué experimentos se realizaron;
* qué decisiones anteriores llevaron al estado actual.

No es necesario leerlo completo para cada tarea.

---

## 3. Architecture Decision Records

Las decisiones arquitectónicas formales se registran en:

`docs/adr/`

Plantilla actual:

`docs/adr/0001-plantilla-base.md`

Un ADR puede tener los estados:

* Propuesto
* Aceptado
* Rechazado
* Obsoleto

Los ADR aceptados representan decisiones arquitectónicas vigentes.

### Cambios de esquema

**No modifiques el esquema de base de datos sin comprobar primero los ADR existentes.**

Cualquier cambio que implique, entre otros:

* nuevas tablas;
* nuevas columnas;
* eliminación de columnas;
* nuevas restricciones;
* modificación de `CHECK`;
* cambios estructurales en relaciones;
* cambios en valores controlados a nivel de esquema;

requiere un ADR aceptado antes de implementar la migración.

No escribas primero la migración para documentarla después.

---

## 4. Precedencia de información

Cuando varias fuentes parezcan entrar en conflicto, utiliza este orden como guía:

1. ADR aceptado aplicable.
2. `docs/contexto/01-decisiones-cerradas.md`.
3. Estado vigente descrito en `docs/contexto/00-resumen.md`.
4. Evidencia especializada documentada en `docs/contexto/03-fuentes-de-datos.md`.
5. Código y configuración actualmente presentes en `main`.
6. Historial en `docs/contexto/CHANGELOG.md`.
7. Documentación histórica, comentarios antiguos o experimentos.

Si el conflicto no puede resolverse con estas fuentes, **decláralo en lugar de asumir una respuesta**.

No cambies documentación silenciosamente para hacerla coincidir con una implementación contradictoria.

---

## 5. Principios no negociables

### Datos

* Utiliza únicamente datos reales, públicos y agregados.
* No fabriques datasets.
* No simules datos epidemiológicos para hacer que una demo funcione.
* No rellenes datos ausentes mediante supuestos no aprobados.
* No conviertas ausencia de datos en cero salvo que la documentación de la fuente lo establezca explícitamente.
* Conserva trazabilidad y procedencia de los datos.

### Interpretación epidemiológica

EPI-Aetheris es una herramienta de apoyo para estimar y comunicar riesgo.

No presentes su salida como:

* diagnóstico;
* certeza clínica;
* predicción infalible;
* recomendación médica;
* descubrimiento epidemiológico novedoso.

El aporte principal del proyecto es de ingeniería de software: reproducibilidad, integración, despliegue y acceso abierto.

### Costos y dependencias

El sistema debe mantenerse reproducible y con costo de replicación tendiendo a cero.

Antes de introducir una dependencia:

1. determina si ya existe una herramienta equivalente en el proyecto;
2. comprueba decisiones cerradas relacionadas;
3. justifica la necesidad;
4. evalúa mantenimiento, licencia, tamaño y complejidad;
5. evita servicios pagos, freemium obligatorios o suscripciones necesarias para el funcionamiento central.

No instales una dependencia únicamente porque simplifica unas pocas líneas de código.

### Privacidad

No introduzcas datos personales.

El sistema trabaja con información pública y agregada y debe conservar esa característica.

### Reproducibilidad

Docker forma parte del funcionamiento esperado del proyecto.

Un cambio que funcione únicamente en la máquina local del desarrollador no se considera una implementación completa.

---

## 6. Alcance epidemiológico actual

No asumas que todas las capas geográficas representan la misma cosa.

El clasificador de la primera fase opera a **nivel nacional**.

El mapa puede mostrar información departamental como capa descriptiva, pero eso no significa que exista una predicción departamental del modelo.

Nunca transformes una clasificación nacional en etiquetas departamentales salvo que exista una implementación y decisión explícita que lo respalde.

Consulta siempre la documentación vigente antes de modificar esta relación.

---

## 7. Arquitectura general

Antes de modificar una parte importante del sistema, inspecciona su implementación actual.

La arquitectura principal está compuesta por:

* PostgreSQL para persistencia;
* FastAPI/Python en `backend/`;
* Astro + TypeScript en `web/`;
* Docker Compose para orquestación.

No introduzcas otro framework, ORM, motor de base de datos, plataforma o arquitectura principal sin comprobar primero las decisiones existentes.

La presencia de una alternativa técnicamente válida no significa que deba introducirse.

---

## 8. Base de datos

Las migraciones están en:

`db/migrations/`

Antes de cambiar una migración o escribir una nueva:

1. revisa los ADR relacionados;
2. inspecciona el esquema vigente;
3. identifica qué código depende del esquema;
4. comprueba pipelines de ingestión;
5. comprueba consultas del backend;
6. determina compatibilidad con datos existentes.

No inventes valores controlados.

Cuando exista una lista documentada de valores válidos, utiliza exactamente esos valores.

---

## 9. Ingestión y datos

Los pipelines de ingestión contienen conocimiento de dominio que no siempre resulta evidente observando solamente el código.

Antes de corregir un comportamiento que parezca extraño, consulta:

`docs/contexto/03-fuentes-de-datos.md`

En particular, evita asumir comportamientos uniformes en:

* boletines MINSAL;
* semanas epidemiológicas;
* OpenDengue;
* Open-Meteo;
* datos acumulados;
* valores faltantes;
* revisiones de boletines;
* agregación temporal.

Una implementación más simple no es necesariamente una implementación correcta.

---

## 10. Frontend

El frontend se encuentra en:

`web/`

Tecnologías principales:

* Astro;
* TypeScript;
* Tailwind;
* Leaflet.

Antes de instalar una librería nueva, revisa si existe una decisión previa sobre el stack.

No introduzcas React, Vue u otro framework de componentes salvo decisión explícita del equipo.

Al representar resultados epidemiológicos:

* diferencia claramente datos descriptivos y salidas del modelo;
* muestra incertidumbre cuando corresponda;
* evita lenguaje que sugiera certeza;
* no conviertas etiquetas nacionales en riesgo departamental;
* conserva accesibilidad y legibilidad.

---

## 11. Backend

El backend se encuentra en:

`backend/`

La API principal utiliza FastAPI.

Antes de modificar endpoints:

1. revisa consumidores actuales;
2. conserva contratos existentes salvo que el cambio sea intencional;
3. comprueba validación de entrada;
4. comprueba manejo de errores;
5. revisa implicaciones de seguridad;
6. revisa cambios de serialización;
7. ejecuta pruebas relevantes.

No confundas CORS con otras medidas de seguridad HTTP. Una capa no sustituye automáticamente a otra.

---

## 12. Seguridad

Cuando una tarea toque autenticación, middleware, CORS, cabeceras HTTP, secretos, configuración del servidor o exposición de endpoints:

* analiza explícitamente las consecuencias de seguridad;
* no elimines controles únicamente para resolver un error de desarrollo;
* no guardes secretos en el repositorio;
* utiliza `.env.example` únicamente como referencia de variables;
* nunca copies credenciales reales a código, documentación, tests o commits.

---

## 13. Forma de trabajar

Para tareas de implementación utiliza, salvo instrucción distinta, este flujo:

**analizar → proponer → implementar → validar → revisar diff**

### Analizar

Antes de modificar:

* inspecciona archivos relevantes;
* identifica dependencias;
* consulta documentación aplicable;
* comprueba decisiones cerradas y abiertas.

### Proponer

Cuando la tarea implique una decisión técnica no trivial:

* explica brevemente el enfoque;
* identifica archivos afectados;
* señala riesgos o trade-offs.

No conviertas automáticamente una propuesta en una decisión arquitectónica.

### Implementar

Realiza el cambio mínimo necesario para cumplir la tarea.

Evita:

* refactors no solicitados;
* cambios cosméticos masivos;
* renombrados innecesarios;
* añadir dependencias sin necesidad;
* modificar componentes fuera del alcance sin justificación.

### Validar

Después de implementar:

* ejecuta tests relevantes;
* ejecuta linters/typecheck cuando existan;
* comprueba comportamiento directamente relacionado;
* revisa errores introducidos.

Si una validación no puede ejecutarse, indícalo explícitamente.

### Revisar diff

Antes de considerar finalizada una tarea:

* inspecciona el diff;
* comprueba que no haya archivos ajenos modificados;
* busca cambios accidentales;
* resume qué cambió y qué queda pendiente.

---

## 14. Tareas de análisis o revisión

Si el usuario solicita:

* revisar;
* analizar;
* investigar;
* comparar;
* auditar;
* explicar;
* evaluar un PR;
* buscar problemas;

no modifiques archivos automáticamente.

Primero entrega los hallazgos.

Solo implementa cambios cuando la solicitud incluya explícitamente corregir, modificar, implementar o equivalente.

---

## 15. Git

### Flujo de ramas

* `main` es la rama de **release**: es lo que Render despliega (ver `render.yaml`). Solo recibe PRs desde `dev`.
* `dev` es la rama de **integración** y la rama por defecto del repo. Todas las PRs de features y fixes van contra `dev`.
* Cuando `dev` está estable se abre una PR `dev → main`; ese merge dispara el despliegue.
* Ramas de trabajo: `feat/*`, `fix/*`, `chore/*`, `docs/*`, partiendo de `dev`.

Respeta el estado actual del repositorio.

Antes de modificar:

* revisa `git status`;
* no sobrescribas trabajo ajeno;
* no descartes cambios locales que no hayas creado;
* no uses comandos destructivos para limpiar el árbol sin autorización.

No hagas commit, push, merge, rebase o force push salvo que el usuario lo solicite.

Al trabajar con un Pull Request, distingue siempre entre:

* estado de `main`;
* rama del PR;
* cambios del diff;
* cambios que surgirían después del merge.

---

## 16. Documentación

No crees un sistema paralelo de documentación sin necesidad.

La estructura existente es la fuente de verdad:

```text
docs/
├── adr/
├── contexto/
├── corrida-canal-endemico-nacional.md
└── corrida-canal-endemico-nacional-4zonas.md
```

Cuando surja conocimiento nuevo:

* decisión arquitectónica formal → `docs/adr/`;
* decisión cerrada de proyecto → `docs/contexto/01-decisiones-cerradas.md`;
* asunto todavía pendiente → `docs/contexto/02-decisiones-abiertas.md`;
* evidencia sobre fuentes de datos → `docs/contexto/03-fuentes-de-datos.md`;
* cambio histórico relevante → `docs/contexto/CHANGELOG.md`;
* resultado reproducible de una corrida → documentación específica de la corrida cuando corresponda.

No dupliques información extensa entre `AGENTS.md` y `docs/`.

La sección 17 de este archivo recoge el contexto técnico acumulado; el resto debe mantenerse principalmente como **guía de operación para agentes**. Cuando una información sea parte del conocimiento permanente del proyecto, debe registrarse en `docs/` según la estructura existente, no solo aquí.

---

## 17. Contexto técnico del proyecto

Referencia rápida. El detalle vive en `docs/`; aquí solo lo que conviene tener a mano antes de tocar código. Si `docs/contexto/` contradice algo, aplica la precedencia de la sección 4.

### Qué es y qué no es

EPI-Aetheris es un sistema de vigilancia epidemiológica **descriptiva** (piloto: dengue e IRA en El Salvador). Ingesta casos históricos y predictores ambientales, los alinea por semana epidemiológica y los expone vía FastAPI + mapa Leaflet.

- **El clasificador predictivo está retirado** (pivote "Camino Ancho", cerrado 2026-08-18 — `docs/informe-cierre-rescate-prediccion.md`). El código entrenado (`entrenar_clasificador.py` y afines) se conserva como referencia histórica: **no lo extiendas ni presentes su salida como predicción en vivo.**
- El proyecto es descriptivo, no predictivo: "qué está pasando y qué tan inusual es contra su propia historia", nunca "qué va a pasar".
- El aporte es de **ingeniería de software** (sistema libre, contenedorizado, reproducible), no de novedad epidemiológica ni un oráculo médico.
- Modelo de dominio **agnóstico a enfermedad y región**: `tipos_evento` y `regiones` son catálogos, no columnas fijas.

### Módulos Camino Ancho

- **M1 — Idoneidad biofísica (`Iv`)** y **M2 — Anomalía climática continua (Z-score leave-one-out)** — implementados en `backend/api/idoneidad.py`, servidos vía `GET /api/v1/spatial/current` y `/api/v1/temporal/{codigo}`. M2 es serie continua: sin alerta binaria, sin lenguaje de lead-time.
- **M3 — Presión epidemiológica relativa** — implementado en `backend/api/presion.py` (fórmula **cerrada** por la coordinación 2026-08-21, `docs/modulo-3-presion-epidemiologica.md`): percentil histórico leave-one-out por departamento, `probable` y `confirmado` como series **separadas** (nunca `total`), años base 2018/2019/2021/2022/2023, ventana ±1 semana, piso de ≥3 años, cortes P50/P75. Salida = percentil + lectura cualitativa (baja/media/alta), **nunca alerta binaria**; celdas insuficientes → `null` + nota. Vía `GET /api/v1/presion/current` y `/api/v1/presion/temporal/{codigo}`. No ajustes estos parámetros sin nueva decisión de la coordinación.
- **M4 — Confianza de vigilancia** — no implementado, sin fórmula aprobada. No la inventes.

Nada de M1–M3 se persiste (se calcula on-request, sin cambios de esquema). El selector de capas del mapa (`web/src/components/MapaDepartamentos.astro`) tiene botones para M1/M2 y para las dos series de M3, y un placeholder deshabilitado para M4. IRA se sirve aparte (`backend/api/ira.py`, UI en `/ira`) y **no** computa módulos Camino Ancho.

### Arquitectura

Tres servicios Docker (`docker-compose.yml`, red `aetheris_network`):

- **`db`** — PostgreSQL 15. El esquema se carga desde `db/migrations/*.sql` **solo una vez, sobre volumen vacío**. Para una base ya inicializada usa el runner de ADR 0009: `python db/aplicar_migraciones.py --bootstrap` una vez, luego `python db/aplicar_migraciones.py` tras añadir cada migración (corre desde el host contra `localhost:5432`, sin rollback — una migración mala se corrige con otra migración).
- **`backend`** (`./backend`) — FastAPI + `psycopg2` directo, sin ORM. Entrada: `backend/api/main.py`.
- **`web`** (`./web`) — Astro + TypeScript + Leaflet.

### Valores controlados del esquema — reutiliza verbatim, nunca inventes

`variables_ambientales.variable` es texto libre **sin `CHECK`**: un typo crea una segunda serie separada en silencio. Usa exactamente estas cadenas:

`temp_max`, `temp_min`, `temp_media`, `precipitation_sum`, `precipitation_hours`, `humedad_relativa_media`, `punto_rocio`, `oni_anom`

(`et0_fao` está deprecado, nunca se carga. `oni_anom` = anomalía ONI de NOAA, ADR 0008, bajo región `SV` nacional. Añadir un predictor = añadir su string a esta lista en la misma sesión, no en el call site.)

- `casos_epidemiologicos.clasificacion`: `probable`, `confirmado`, `total` (agregado de OpenDengue, solo `fuente_id=opendengue_v1_3` nacional — **NO** equivale a `confirmado`), `notificado` (departamental sin split probable/confirmado, p.ej. IRA — ADR 0011). Nunca sumes `conteo` entre valores de `clasificacion` sin filtrar primero.
- `boletines_procesados.estado`: `pendiente`, `ok`, `revision_manual`, `error`, `ausencia_esperada` (ADR 0004), `sin_texto_extraible` (ADR 0007).
- `boletines_procesados.familia_esquema`: `A` o `B`.
- `fuentes_datos.codigo`: `opendengue_v1_3`, `minsal_pdf`, `open_meteo_era5_land`, `open_meteo_era5` (ADR 0006 — `era5` es exclusivo para `precipitation_sum`/`precipitation_hours`), `noaa_oni`.
- `regiones.codigo`: ISO 3166-2:SV (**sin verificar aún** contra el GeoJSON de Leaflet — confírmalo antes de usarlo como clave de join).
- Semanas epidemiológicas: **PAHO/CDC (MMWR), no ISO 8601** — usa la librería `epiweeks`, no recalcules límites a mano.

### Fuentes de datos

Las trampas empíricas —MINSAL (el año impreso en el PDF no es fiable; dos familias de tabla detectadas **por documento**, nunca por rango de año; celdas vacías = `0`; fila "Otros países"; Probable/Confirmado son **acumulados desde SE1** que hay que desacumular por diferencias; boletines de vacaciones sin tabla; ~49/52 semanas reales), OpenDengue (`case_definition_standardised` siempre `Total`; resolver la semana por coincidencia exacta de `calendar_start_date`), Open-Meteo (`era5_land` para temp/humedad/rocío + `era5` para precipitación, nunca `best_match`; ceros falsos de precipitación; rate-limit `429` por minuto)— están documentadas con evidencia en **`docs/contexto/03-fuentes-de-datos.md`**. Léela antes de tocar cualquier pipeline de ingesta. No reimplementes la desacumulación MINSAL desde cero: existe validada en `backend/ingestion/corrida_distribucion.py` y en producción en `backend/ingestion/minsal/parser.py`.

**2020 está deliberadamente ausente** de la ventana departamental (subregistro real por covid + riesgo de extracción) — no lo "arregles". Es una exclusión de ventana de entrenamiento: no filtres 2020 durante la ingesta. La serie nacional de OpenDengue sí muestra 2020 con nota explicativa.

### Convenciones del repo

- Contenido de dominio (tablas, columnas, comentarios, docstrings) en **español**.
- Extiende los catálogos (`tipos_evento` / `regiones` / `fuentes_datos`) en vez de añadir columnas por enfermedad o país.
- Datos crudos e intermedios **no se versionan** (`backend/ingestion/data/raw/` y `.../interim/` gitignoreados). Excepción deliberada: `db/seed/seed_datos_reales.sql` (ADR 0010, volcado `pg_dump --data-only` de las tablas de hechos, montado en `/docker-entrypoint-initdb.d/` para que `git clone` + `docker compose up` dé un sistema con datos reales).
- Valida PDFs descargados por firma de bytes (`%PDF`), no por `Content-Type` (el servidor devuelve `application/octet-stream`).

### Decisiones abiertas

`docs/contexto/02-decisiones-abiertas.md` es la fuente. No resuelvas unilateralmente: la fórmula de M4 y dónde vive su salida, las coordenadas departamentales para Open-Meteo, si la exclusión de 2020 gobierna la ingesta, y si algún clasificador se reactiva (la línea predictiva está cerrada — no la resucites sin instrucción explícita).

### Comandos

```bash
docker-compose up --build          # todo: API :8000 (/health), web :4321, Postgres :5432
```

Variables de entorno desde `.env` (copiar de `.env.example`; nunca commitear `.env`).

- **Backend fuera de Docker:** `cd backend && pip install -r requirements.txt && uvicorn api.main:app --reload` (entorno Arch — prefiere virtualenv).
- **Web fuera de Docker:** `cd web && pnpm install && pnpm dev|build|preview` (pnpm vía Corepack, fijado a v9 — **no `npm`**).
- **Tests:** pytest **desde `backend/`** (`pip install -r requirements.txt -r requirements-dev.txt`, luego `python -m pytest ingestion/tests/ api/tests/`). Los tests con BD se **saltan** (no fallan) si no hay Postgres en `localhost:5432`. No hay linter ni CI en el repo.
- **Multi-worktree (Orca ADE):** `docker-compose.yml` usa `container_name` y puertos fijos compartidos a nivel del daemon Docker — **solo un worktree corre `docker-compose up` a la vez**. No lo "arregles" namespaceando puertos/nombres por worktree sin preguntar.

---

## 18. Manejo de contradicciones

Si encuentras que:

* código y documentación discrepan;
* dos documentos se contradicen;
* un ADR aceptado contradice comportamiento actual;
* una decisión cerrada parece haber sido implementada de otra manera;

no "corrijas" automáticamente una de las partes.

Haz lo siguiente:

1. identifica exactamente la contradicción;
2. determina cuál fuente debería tener precedencia;
3. comprueba el historial cuando sea necesario;
4. informa del conflicto;
5. modifica solo cuando exista una conclusión suficientemente respaldada.

---

## 19. No asumir

Cuando falte información:

* no inventes datos;
* no inventes requisitos;
* no inventes una decisión del equipo;
* no conviertas una aproximación en hecho;
* no escondas incertidumbre.

Distingue claramente entre:

* estado actual;
* evidencia;
* decisión aprobada;
* hipótesis;
* propuesta;
* pendiente.

---

## 20. Objetivo del agente

Tu función dentro de EPI-Aetheris es ayudar a producir cambios:

* técnicamente correctos;
* reproducibles;
* verificables;
* coherentes con las decisiones existentes;
* honestos respecto a limitaciones y datos;
* simples de mantener por el equipo.

La prioridad no es generar la mayor cantidad de código posible.

La prioridad es **mejorar el proyecto sin romper su coherencia técnica ni documental**.
