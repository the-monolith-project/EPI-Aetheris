# Informe: qué pedía la ingesta respiratoria y qué hay

**Fecha:** 2026-08-28  
**Rama:** `feature/ingesta-respiratoria` (`main` no se modificó)  
**Fuente de requisitos:** `indicaciones-grok-ingesta-respiratoria-epi-aetheris-1.md`

Este texto contrasta las indicaciones con lo entregado y, al final, explica tres pendientes que **no** se resolvieron aquí (seed, Astro check y ADR), por qué, y qué tienen que ver con este cambio.

---

## 1. Qué pedía la tarea, en corto

Ampliar EPI-Aetheris con los mismos boletines MINSAL, **sin inventar datos** y **sin mezclar** dengue, IRA, neumonías y virus:

1. Entender la fuente (Neumonías por un lado; Influenza, VSR y SARS-CoV-2 por otro).
2. Guardar cada serie con su significado real.
3. Mostrarla en una sección respiratoria descriptiva (sin predicción ni causalidad).
4. Dejar constancia de huecos, cobertura y procedencia.

Fuera de alcance (y no se hizo): predecir neumonías, copiar los índices de dengue, OCR, calidad del aire, años 2024–2026, React/Vue.

---

## 2. Contraste: indicaciones vs lo que hay

### Exploración (entender la fuente)

| Pedían | Hay |
|---|---|
| Recorrer el corpus MINSAL | Sí: 264 boletines (2018, 2019, 2021, 2022, 2023). |
| Inventario de Neumonías | Sí: `docs/exploracion-neumonias-boletines-minsal.md`. |
| Inventario de Influenza / VSR / SARS-CoV-2 | Sí: `docs/exploracion-vigilancia-virus-boletines-minsal.md`. |
| Layouts, huecos, tablas-imagen, reimpresiones, correcciones | Sí, documentados. |
| Qué es cada número y a qué geografía llega | Sí: Neumonías = conteo clínico **por departamento**. Virus = **laboratorio nacional** (muestras, detecciones, positividad), no casos y no mapa. |

**Cumple.**

### Neumonías

| Pedían | Hay |
|---|---|
| Parser con extractos reales | Sí. |
| Desacumular si la fuente es acumulada | Sí (misma honestidad que IRA: hueco ≠ cero). |
| Guardar sin falsear el significado | Sí: mismo tipo de conteo “notificado” que IRA, evento aparte (`neumonia`). |
| Carga repetible, con prueba en seco | Sí. En este entorno: **2.749** filas. |
| API y pruebas | Sí. |

**Cumple.**

### Influenza, VSR y SARS-CoV-2

| Pedían | Hay |
|---|---|
| No tratarlos como casos si no lo son | Sí. |
| Conservar denominador; no mezclar porcentajes y conteos | Sí. |
| Documento de decisión **antes** de tabla nueva | Hay ADR 0012 y luego migración `0008`. Falta **visto bueno del coordinador** (ver §3). |
| Carga, API, pruebas | Sí. En este entorno: **3.028** filas. COVID-19 solo en 2023; 2020 no se bajó. |

**Cumple el dato y la API.** La formalidad del ADR queda abierta.

### Frontend

| Pedían | Hay |
|---|---|
| Módulo respiratorio (IRA, Neumonías, virus), cada uno con su definición | Sí: `/respiratorio`. `/ira` redirige ahí. |
| Mapa solo si hay departamentos | Sí para IRA y Neumonías. Virus: series nacionales, sin mapa inventado. |
| Curva, año, semanas, comparar, heatmap, huecos, exportar | Sí (heatmap de Neumonías departamento × semana; virus × semana; una métrica por escala). |
| Nombre, unidad, fuente, sin predicción ni causalidad | Sí. |
| Si la API falla, no inventar cifras | Sí; cubierto también con Playwright (3 pruebas). |
| IRA con dato en esta máquina | Sí, al cierre: **2.742** filas (el volumen de desarrollo no las tenía al inicio). |

**Cumple** lo que las indicaciones marcan como aceptación de interfaz. No se rediseñó el panel de dengue.

### Revisión final

| Pedían | Hay |
|---|---|
| Pruebas relevantes | Parsers, loaders y Playwright del observatorio: sí. |
| `astro check` / lint / build si existen | **No se corrió Astro check** (ver §3). El build de la web ya fallaba por un componente de dengue (`@observablehq/plot`), ajeno a esta rama. |
| Sin PDF ni datos intermedios en git | Sí. |
| Sin tocar dengue de más | Sí. IRA solo se filtró para no mezclarla con Neumonías y se unificó en el observatorio. |
| Documentación | Sí (exploración, limitaciones, este informe). |

---

## 3. Seed, Astro check y ADR: qué son, por qué no se tocaron, y qué tienen que ver con este cambio

Estas tres cosas **no son la página de Neumonías**. Son cómo se **oficializa** el cambio en el proyecto. Se dejaron fuera a propósito (instrucción de no resolver lo que solo corresponde al coordinador).

### Seed (foto de datos para quien clone el proyecto)

**En qué consiste.** El proyecto promete que un tercero clone, levante Docker y vea el sistema con datos reales, **sin** volver a descargar los 264 PDF. Esa foto se guarda en un archivo de arranque (`db/seed/seed_datos_reales.sql`). La regla vigente (ADR 0010) dice: es una instantánea de un momento; **no se regenera en cada cambio**; solo cuando el equipo decide que vale una foto más nueva.

**Qué tiene que ver con esta tarea.** Neumonías, virus e IRA ya están en la base **de este desarrollo**. Esa foto oficial **sigue siendo la anterior** (dengue y lo que había hasta agosto). Quien clone hoy obtiene la tabla nueva **vacía** y tiene que repetir la carga.

**Por qué no se tocó.** Regenerar el seed es una decisión explícita del coordinador, no un efecto colateral de una ingesta. Además el archivo es grande y ensucia el historial. No hace falta para usar `/respiratorio` en esta máquina.

### Astro check (revisión automática de la web)

**En qué consiste.** Herramienta que revisa el código del frontend (tipos y consistencia) antes de publicar. En el proyecto está **aprobada técnicamente**, pero “aprobar no es instalar ni adoptar” (decisión de herramientas del frontend, aún abierta en detalles de uso).

**Qué tiene que ver con esta tarea.** El checklist de las indicaciones pide `astro check` / lint / build **si ya están disponibles**. No es un requisito para entender o guardar Neumonías. Lo que sí se hizo para esta interfaz: pruebas de Playwright del observatorio (carga, redirección, que no se inventen cifras si falla la API).

**Por qué no se tocó.** Activar o exigir Astro check es adopción de tooling, no de ingesta. Correrlo aquí no cierra la semántica de los datos y podía empujar a instalar o configurar algo que el coordinador aún no mandó para esta rama.

### ADR (acta de decisión de arquitectura)

**En qué consiste.** Un escrito corto: *qué problema había, qué se eligió, qué se descartó*. En este proyecto **no se cambia el esquema de la base** (tablas, restricciones) sin un ADR **antes** de la migración.

**Qué tiene que ver con esta tarea.** Neumonías cupo en lo ya decidido (conteo “notificado”, como IRA). Los **virus no**: no son casos por departamento, son muestras y porcentajes. Por eso existe el ADR 0012 y, después, la tabla de vigilancia. El orden (documento → migración) sí se respetó.

**Por qué no se “cerró” del todo.** El archivo está en estado Aceptado para poder crear la tabla, con evidencia de los 264 PDF. **Confirmar o corregir ese visto bueno es del coordinador.** Si lo rechaza, hay que cambiar cómo se guardan los virus (con otra migración; el proyecto no hace “deshacer” automático). Eso no impide usar la página hoy; impide decir que el diseño es ley de equipo.

---

## 4. Lectura final

La tarea de **entender, guardar y mostrar** neumonías y virus respiratorios, sin falsear dengue ni IRA, **está hecha en esta rama**.

Lo que **no** está hecho —seed, Astro check, confirmación del ADR— no es trabajo de parser ni de mapa: es **cómo se deja el cambio oficial, reproducible para un tercero y con firma del coordinador**. Hasta que eso ocurra, el observatorio funciona aquí; un clone limpio y el “sí institucional” al diseño de virus siguen pendientes.
