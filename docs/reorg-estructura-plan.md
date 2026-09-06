# Plan de reorganización de estructura del repositorio

> Tarjeta Tech #60. Auditoría re-derivada el 2026-09-06 (la original del 2026-08-26
> no quedó registrada). Este documento **solo audita y planea**: no se ejecutó
> ningún `git mv`. Nada aquí toca el esquema de datos salvo lo marcado como
> follow-up.

---

## 1. Resumen de hallazgos

### Lo que ya está bien (no tocar)
- **`db/migrations/`** — numeradas `0001`–`0008`, convención sólida. El runner
  (`docker-entrypoint-initdb.d` + CI loop + `db/aplicar_migraciones.py`) depende
  del orden alfabético y del glob `db/migrations/*.sql`.
- **`docs/adr/`** — numerados `0001`–`0012`, formato ADR estándar.
- **`docs/contexto/`** — `00`–`03` + `CHANGELOG.md`, split por función de consulta,
  referenciado explícitamente por `AGENTS.md` (§§4, 13–17) y `EPI-Aetheris_Contexto_Maestro.md`.
- **Separación `backend/` / `web/` / `db/`** — limpia. `web/src/` ya está
  ordenado (`components/`, `components/analisis/`, `lib/`, `layouts/`, `pages/`,
  `styles/`, `utils/`).
- **Raíz** — sin directorios sueltos problemáticos. `.design-sync/`, `.jules/`
  son config de agentes; `orca.yaml`, `render.yaml`, `docker-compose.yml`,
  `.env.example` son estándar.

### Lo que mezcla cosas que deberían estar separadas

| # | Carpeta | Problema | Alcance |
|---|---------|----------|---------|
| A | **`docs/` (raíz)** | 38 archivos `.md` sueltos: corridas experimentales, entrenamientos del clasificador (familia de 13), experimentos, exploraciones MINSAL, protocolos, respuestas a protocolos, informes, borradores. Sin ninguna subcarpeta pese a que `docs/adr/` y `docs/contexto/` sí existen. | Parcial: los que no tienen referencias entrantes se pueden agrupar; los referenciados desde código/manifiestos/SQL/web requieren cuidado |
| B | **`docs/tobeer/`** | Mezcla `.py` (25 KB) + `.csv` + `.json` (28 KB) + `.md` en `docs/`. Es un *drop* de entrega a Isaac ("to be erased"). El `.py` es una variante desincronizada de `backend/ingestion/diagnostico_senal_etiqueta_auditable.py` (corrió con scikit-learn 1.8/numpy 2.4, el proyecto fija 1.5.1). Cero referencias entrantes en todo el repo. | Requiere decisión del usuario: borrar vs archivar |
| C | **`db/migrations/seed_datos_reales.sql`** | Archivo **vacío (0 bytes)**. Sobrevive de cuando el seed vivía en `db/migrations/`. Lo captura el glob `db/migrations/*.sql` (CI y `docker-entrypoint-initdb.d`) — hoy inocuo porque está vacío, pero es ruido y un pie de foto para un futuro `psql -f` sobre archivo vacío. El seed real vive en `db/seed/seed_datos_reales.sql` (5,1 MB). | Borrado, bajo riesgo (ver verificación en §4) |
| D | **`backend/ingestion/` (raíz del paquete)** | ~35 `.py` en un solo namespace plano mezclando: loaders de producción (`cargar_*`), build de geo, código del **clasificador retirado** (`entrenar_clasificador.py`, `construir_dataset_modelado.py`, `corrida_canal_endemico_*`), scripts de validación de las 5 Vías (`validar_via_*` + 5 manifiestos `via_*_manifesto_congelado.json`), experimentos descartados (`experimento_multipais.py`, `diagnostico_senal_etiqueta_auditable.py`), utilidades Camino Ancho. | **Fuera de alcance de ejecución** (ver §5) |
| E | **`backend/ingestion/clima/`** | Mezcla evidencia (`evidencia_*.json`), hallazgos (`hallazgos_*.md`), pruebas numeradas sueltas (`prueba2_*`, `prueba3_*`, `prueba4_*`) y una subcarpeta `prueba1_ecmwf_ifs/`. Inconsistente (unas pruebas en subcarpeta, otras no). | Bajo–medio, opcional |
| F | **`variables_ambientales`** (tabla) | Una sola tabla EAV (`variable` texto libre) mezcla observaciones climáticas **departamentales** (temp/humedad/rocío de `era5_land`, precipitación de `era5`) con el **índice oceánico ONI nacional** (`oni_anom`, sin resolución subnacional, guardado bajo `regiones.codigo='SV'`). | **Follow-up: requiere ADR antes de tocar** (ver §6) |

**Corrección al encuadre de la tarjeta:** "docs sueltos → subcarpetas" **no es
uniformemente bajo riesgo**. De los 38 archivos, 24 tienen 0 referencias
entrantes (mover = barato), pero 14 están referenciados desde `backend/api/*.py`,
`backend/ingestion/*.py`, los 4 manifiestos Vía congelados, comentarios en
migraciones SQL, un componente web con URL de GitHub *hardcodeada*, y tests.
Uno de ellos (`entrenamiento-clasificador-riesgo-nacional*.md`) tiene su ruta
**construida con un f-string en código** — un rename de ruta no lo arregla.

---

## 2. Conteo de referencias entrantes por doc suelto

Medido con `grep -rIl <basename>` sobre `backend/ web/ db/ .github/ AGENTS.md
README.md EPI-Aetheris_Contexto_Maestro.md orca.yaml render.yaml docker-compose.yml
docs/adr docs/contexto`.

| Refs | Archivos |
|------|----------|
| **0** | `borrador-registro-documental-via-menos-uno.md`, `corrida-via-{cero,uno,dos,tres,menos-uno}.md`, `diagnostico-senal-etiqueta-auditoria.md`, `entrenamiento-clasificador-riesgo-nacional*.md` (13 archivos), `experimento-multipais.md`, `limitaciones-ingesta-respiratoria.md`, `propuesta-coordinador-cierre-ingesta-respiratoria.md`, `protocolo-exploracion-respiratorios.md`, `respuesta-protocolo-evaluacion.md`, `respuesta-protocolo-via-menos-uno-v2.md` |
| **1** | `despliegue-render.md` (`render.yaml`), `experimento-oni-predictor.md` |
| **2** | `corrida-canal-endemico-nacional.md`, `corrida-canal-endemico-nacional-4zonas.md`, `levantamiento-gaps-stack-web.md` |
| **3** | `tarea-rescate-prediccion.md` (3 manifiestos Vía) |
| **4** | `experimento-ventana-climatica-ampliada.md` |
| **5** | `experimento-validacion-leadtime-camino-ancho.md`, `exploracion-neumonias-boletines-minsal.md`, `exploracion-vigilancia-virus-boletines-minsal.md`, `modulo-3-presion-epidemiologica.md`, `protocolo-evaluacion-rescate-prediccion.md` |
| **7** | `exploracion-ira-boletines-minsal.md`, `informe-cierre-rescate-prediccion.md` |

Además hay **enlaces entre docs sueltos** que el grep anterior no cubre y que se
romperían si los hermanos caen en subcarpetas distintas:
- `borrador-registro-documental-via-menos-uno.md` → `respuesta-protocolo-via-menos-uno-v2.md`, `protocolo-evaluacion-rescate-prediccion.md`, `corrida-via-menos-uno.md`
- `experimento-multipais.md` → `experimento-oni-predictor.md`, `experimento-ventana-climatica-ampliada.md`
- `experimento-oni-predictor.md` → `experimento-ventana-climatica-ampliada.md`
- `experimento-multipais.md` (línea 139: `corrida-via-cero.md` menciona `experimento-multipais.md`)
- `exploracion-vigilancia-virus-boletines-minsal.md` → `protocolo-exploracion-respiratorios.md`, `exploracion-neumonias-boletines-minsal.md`
- `respuesta-protocolo-*.md` → `protocolo-evaluacion-rescate-prediccion.md`
- `diagnostico-senal-etiqueta-auditoria.md` → `docs/tobeer/LEEME-procedencia.md` (+ hash SHA-256 de ese archivo embebido en una tabla)

**Consecuencia de diseño:** conviene agrupar *conjuntos que se enlazan entre sí*
en la **misma** subcarpeta, no separarlos por tipo. Los "rescate-predicción"
(protocolo + respuestas + borrador + corridas Vía + tarea) forman un cluster;
los "experimentos" (multipais + oni + ventana + leadtime) otro; los
"exploraciones respiratorias" otro.

---

## 3. Tabla de movimientos propuestos

Convención de destino: subcarpetas temáticas bajo `docs/`, en paralelo a
`adr/` y `contexto/`.

### Fase 1 — sin referencias entrantes (riesgo bajo)

| Origen | Destino | Referencias a actualizar | Riesgo |
|--------|---------|--------------------------|--------|
| `docs/entrenamiento-clasificador-riesgo-nacional*.md` (13) | `docs/clasificador-retirado/entrenamientos/` | **`backend/ingestion/entrenar_clasificador.py:301,306`** — la ruta se arma con `f"docs/entrenamiento-clasificador-riesgo-nacional{sufijo}.md"`. **Cambio de código, no reescritura de ruta**: actualizar el prefijo del f-string. Sin tests sobre ese string (verificar `test_entrenar_clasificador.py`). | Medio |
| `docs/experimento-multipais.md`, `docs/experimento-oni-predictor.md`, `docs/experimento-ventana-climatica-ampliada.md`, `docs/experimento-validacion-leadtime-camino-ancho.md` | `docs/experimentos/` | Enlaces relativos entre estos 4 (§2). `experimento-ventana-climatica-ampliada.md` (4 refs) y `experimento-validacion-leadtime-camino-ancho.md` (5 refs) están citados desde `backend/api/idoneidad.py`, `backend/api/main.py:524,536`, `backend/ingestion/{validar_leadtime_camino_ancho,construir_dataset_modelado,inicio_temporada_departamental}.py`, `docs/adr/0008`. **Estos dos suben a Fase 2.** Los otros dos (0 y 1 ref) quedan en Fase 1. | Bajo (multipais/oni) |
| `docs/corrida-via-{cero,uno,dos,tres,menos-uno}.md`, `docs/borrador-registro-documental-via-menos-uno.md`, `docs/respuesta-protocolo-evaluacion.md`, `docs/respuesta-protocolo-via-menos-uno-v2.md` | `docs/rescate-prediccion/` | Enlaces relativos internos del cluster (§2). Ninguno referenciado desde código. **Mover junto con `protocolo-evaluacion-rescate-prediccion.md` y `tarea-rescate-prediccion.md`** (Fase 2) para no partir el cluster. | Bajo si van todos juntos |
| `docs/diagnostico-senal-etiqueta-auditoria.md` | `docs/clasificador-retirado/` o `docs/experimentos/` | Enlace a `docs/tobeer/LEEME-procedencia.md` (depende de la decisión B). | Bajo |
| `docs/limitaciones-ingesta-respiratoria.md`, `docs/propuesta-coordinador-cierre-ingesta-respiratoria.md`, `docs/protocolo-exploracion-respiratorios.md` | `docs/exploraciones-respiratorias/` | `protocolo-exploracion-respiratorios.md` es citado por `exploracion-vigilancia-virus-boletines-minsal.md` (mover juntos). | Bajo |

### Fase 2 — referenciados desde código / manifiestos / SQL / web (riesgo medio)

| Origen | Destino | Referencias a actualizar | Riesgo |
|--------|---------|--------------------------|--------|
| `docs/protocolo-evaluacion-rescate-prediccion.md` | `docs/rescate-prediccion/` | **4 manifiestos Vía congelados** (`backend/ingestion/via_{cero,uno,dos,tres,menos_uno}_manifesto_congelado.json`) campo `"protocolo"`; `backend/ingestion/validar_via_menos_uno.py:4`; enlaces desde `respuesta-*` y `borrador-*`. Los manifiestos NO hashean su propio contenido (solo `seed_sha256` del seed) → editar el string `protocolo` no invalida los tests `test_validar_via_*.py` (verificar: ninguno *asserta* sobre `fuente.protocolo`). | Medio |
| `docs/tarea-rescate-prediccion.md` | `docs/rescate-prediccion/` | Manifiestos `via_{uno,dos,tres}_manifesto_congelado.json` campo `"tarea"`. Mismo criterio que arriba. | Medio |
| `docs/experimento-ventana-climatica-ampliada.md` | `docs/experimentos/` | `backend/ingestion/construir_dataset_modelado.py:68` (comentario); `docs/adr/0008`. | Medio |
| `docs/experimento-validacion-leadtime-camino-ancho.md` | `docs/experimentos/` | `backend/api/idoneidad.py:3`; `backend/api/main.py:524,536`; `backend/ingestion/validar_leadtime_camino_ancho.py:2`; `backend/ingestion/inicio_temporada_departamental.py:3`; `web/src/content.config.ts:15` **+ `web/src/pages/biblioteca/index.astro:19` (`ORDEN_BIBLIOTECA` id)** → ver nota biblioteca abajo. | Alto (biblioteca) |
| `docs/modulo-3-presion-epidemiologica.md` | `docs/` (dejar en raíz) o `docs/modulos-camino-ancho/` | `backend/api/{presion,ira,main}.py`; `AGENTS.md:490`; **`web/src/content.config.ts:16` + biblioteca id**. | Alto (biblioteca) |
| `docs/informe-cierre-rescate-prediccion.md` | `docs/` (dejar en raíz) o `docs/rescate-prediccion/` | `AGENTS.md:482`; `docs/contexto/{00,01,02}.md`; **`web/src/components/MetricasModelo.astro:53` — URL de GitHub *hardcodeada* `blob/main/docs/informe-cierre-rescate-prediccion.md`**; `web/src/content.config.ts:14` + biblioteca id. | Alto (biblioteca + URL hardcodeada) |
| `docs/exploracion-ira-boletines-minsal.md` | `docs/exploraciones-respiratorias/` | `backend/api/{cobertura,ira}.py` (`cobertura.py:45` como valor de dict `fuente_informe`), `backend/ingestion/{cargar_ira,corrida_ira}.py`, `backend/ingestion/tests/{fixtures/minsal/README.md,test_corrida_ira.py}`, **`db/migrations/0007_clasificacion_notificado_ira.sql:37` (string dentro de un `INSERT`)**. | Medio-alto (string en migración ya aplicada) |
| `docs/exploracion-neumonias-boletines-minsal.md` | `docs/exploraciones-respiratorias/` | `backend/api/cobertura.py:25`; **`db/migrations/0008_*.sql:12` (string en `INSERT`)**; `docs/contexto/01`. | Medio-alto |
| `docs/exploracion-vigilancia-virus-boletines-minsal.md` | `docs/exploraciones-respiratorias/` | `backend/api/cobertura.py:38`; `docs/adr/0012`; `docs/contexto/01`. | Medio |
| `docs/corrida-canal-endemico-nacional.md`, `docs/corrida-canal-endemico-nacional-4zonas.md` | `docs/clasificador-retirado/` | `AGENTS.md:455–456` (bloque de estructura `docs/` — hay que actualizar el árbol de ejemplo). | Bajo-medio |
| `docs/despliegue-render.md` | `docs/` (dejar en raíz) | `render.yaml:2,10` (2 comentarios). Poco valor mover; recomendado **dejarlo**. | Bajo |
| `docs/levantamiento-gaps-stack-web.md` | `docs/` (dejar en raíz) o `docs/web/` | `docs/contexto/{01,02}.md`. | Bajo |

### Fase 3 — limpieza puntual

| Acción | Referencias | Riesgo |
|--------|-------------|--------|
| **Borrar** `db/migrations/seed_datos_reales.sql` (0 bytes) | Ninguna directa. Verificación previa obligatoria en §4. | Bajo |
| `backend/ingestion/clima/`: mover `prueba2_*`, `prueba3_*`, `prueba4_*` a subcarpetas `prueba2_14deptos/`, etc. (consistencia con `prueba1_ecmwf_ifs/`) | Ninguna en código (los loaders leen `geo/` y `data/`, no `clima/`; `clima/` es solo evidencia). Verificar `hallazgos_*.md` internos. | Bajo |
| `docs/tobeer/` → decisión del usuario (§ follow-ups) | `docs/diagnostico-senal-etiqueta-auditoria.md` enlaza a `tobeer/LEEME-procedencia.md` con hash. | — |

### Nota crítica — pestaña Biblioteca (web)

`web/src/content.config.ts` usa `glob({ pattern: [...], base: '../../docs' })`.
El `id` de cada entrada de la colección **incluye la ruta relativa a `base`**.
Si `informe-cierre-rescate-prediccion.md` pasa a `docs/rescate-prediccion/`,
su `id` pasa de `informe-cierre-rescate-prediccion` a
`rescate-prediccion/informe-cierre-rescate-prediccion`, lo que cambia:
1. el `pattern` en `content.config.ts`,
2. los `id` en `ORDEN_BIBLIOTECA` (`web/src/pages/biblioteca/index.astro:12–26`),
3. la ruta pública `/biblioteca/<id>` (`web/src/pages/biblioteca/[...slug].astro`).

Los tests e2e (`web/tests/e2e/*.spec.ts`) **no** tocan `/biblioteca`, así que no
bloquean, pero cualquier verificación de `preview` debe correr en **puerto 4321**
(CORS del backend local — ver `docker-compose.yml` `e2e` y `render.yaml`).

**Recomendación:** los 3 docs de biblioteca
(`informe-cierre-rescate-prediccion.md`, `experimento-validacion-leadtime-camino-ancho.md`,
`modulo-3-presion-epidemiologica.md`) **se quedan en `docs/` raíz**. Son los de
mayor costo de movimiento y el beneficio de agruparlos es marginal.

---

## 4. Verificación previa a borrar `db/migrations/seed_datos_reales.sql`

`docker-compose.yml` monta **dos** cosas en el mismo path del contenedor:
```
- ./db/migrations:/docker-entrypoint-initdb.d
- ./db/seed/seed_datos_reales.sql:/docker-entrypoint-initdb.d/seed_datos_reales.sql:ro
```
El archivo vacío `db/migrations/seed_datos_reales.sql` se monta primero (vía el
directorio) y luego el bind-mount del seed real lo **sobreescribe** en el
contenedor. Hoy funciona por ese orden. Aun así:
- CI (`.github/workflows/backend-tests.yml:60`) hace `for f in db/migrations/*.sql`
  → hoy ejecuta `psql -f db/migrations/seed_datos_reales.sql` (vacío, no-op) y
  **luego** `psql -f db/seed/seed_datos_reales.sql`. Borrar el vacío solo quita
  el no-op.
- `db/aplicar_migraciones.py` — verificar su glob antes de borrar.

**Pasos:** (1) `grep -rn "migrations/seed_datos_reales\|migrations.*seed" .`;
(2) revisar `db/aplicar_migraciones.py`; (3) `git rm db/migrations/seed_datos_reales.sql`;
(4) correr `backend-tests.yml` localmente o en una rama antes de merge.

---

## 5. Fuera de alcance de ejecución — `backend/ingestion/`

**Dos razones, ambas duras:**

1. **Namespace plano sin paquete.** No existe **ningún** `__init__.py` en
   `backend/`. Los módulos se importan planos: `from db import get_connection`,
   `from entrenar_clasificador import CLASES`, `from common import ...`. Los
   tests hacen `sys.path.insert(0, <dir de ingestion>)` y luego
   `from experimento_multipais import ...`. La suite corre con
   `working-directory: backend` + `python -m pytest ingestion/tests/ api/tests/`
   (sin `pytest.ini` ni `pyproject.toml`). Mover cualquier `.py` a una subcarpeta
   rompe todos esos imports y obliga a convertir `ingestion/` en paquete real
   (con `__init__.py` y reescritura de **todos** los imports internos + los
   `sys.path` de los tests). Es un cambio grande, propenso a fallar solo tras
   merge en CI, y de bajo retorno.

2. **Decisión abierta explícita.** `docs/contexto/02-decisiones-abiertas.md:55`
   ("Archivar/mover el código del clasificador retirado, pendiente de decidir")
   dice textualmente: *"No mover nada sin que el coordinador decida el criterio
   — mover código real de producción sin cuidado podría romper imports."*
   Afecta a `entrenar_clasificador.py`, `construir_dataset_modelado.py`,
   `corrida_canal_endemico_nacional.py`, `corrida_canal_endemico_4zonas.py` y
   los experimentos descartados.

→ **`backend/ingestion/` no entra en ninguna fase ejecutable.** Sube a §6.

---

## 6. Follow-ups (requieren decisión / ADR antes de tocar)

### 6.1 `variables_ambientales` — requiere ADR
Tabla EAV (`db/migrations/0001_init_schema.sql:79`) que hoy mezcla:
- observaciones climáticas **departamentales** por variable (`temperature_2m_*`,
  `relative_humidity_2m_mean`, `dew_point_2m_mean` de `era5_land`;
  `precipitation_sum`, `precipitation_hours` de `era5`), y
- el índice **ONI nacional** (`oni_anom`, ADR 0008), sin resolución subnacional,
  guardado bajo `regiones.codigo='SV'`.

Además el ADR 0006 y el ADR 0003 ya anotan como *candidato futuro* añadir a esta
tabla una columna `modelo` / centro de celda por observación. Cualquier
separación (tabla aparte para índices no-departamentales, o columna de
procedencia) **es cambio de esquema** → exige ADR aceptado en `docs/adr/` antes
de la migración (regla no negociable, `docs/contexto/01-decisiones-cerradas.md:56`).
**No se toca en #60.**

### 6.2 Código del clasificador retirado en `backend/ingestion/`
Ver §5.2. Necesita que la coordinación fije el criterio (subcarpeta
`_retirado/`, nota en docstring, o dejar y confiar en `AGENTS.md`). Cuando se
decida, es un cambio propio con conversión a paquete.

### 6.3 `docs/tobeer/`
Drop de entrega sin referencias en código. Opciones para el usuario:
(a) borrar (el `.py` es una variante obsoleta del de `backend/ingestion/`, corrió
con versiones distintas a las fijadas); (b) archivar en
`docs/clasificador-retirado/entrega-isaac/`; (c) dejar. Si se borra/mueve,
actualizar el enlace + hash en `docs/diagnostico-senal-etiqueta-auditoria.md`.

### 6.4 Reescritura de enlaces históricos en `docs/contexto/CHANGELOG.md`
Varias entradas del CHANGELOG citan rutas `docs/*.md` que se moverían. Reescribir
un registro histórico para que apunte a rutas nuevas es discutible (el enlace
describe el estado *de entonces*). **Decisión del usuario:** reescribir por
higiene de enlaces, o dejar y aceptar que apuntan a rutas movidas. Recomendación:
reescribir solo si el enlace es puramente de navegación, no si documenta "dónde
estaba en esa fecha".

---

## 7. Orden de ejecución recomendado

Cada fase = un PR contra `dev`, con CI verde antes del siguiente.

1. **PR 0 — limpieza trivial** (riesgo bajo, sin dependencias)
   - Borrar `db/migrations/seed_datos_reales.sql` (tras verificación §4).
   - Consolidar `backend/ingestion/clima/pruebaN_*` en subcarpetas (opcional).
   - Verificar: `backend-tests.yml` local + `docker compose up` limpio.

2. **PR 1 — docs sin referencias entrantes** (riesgo bajo)
   - Crear `docs/experimentos/`, `docs/rescate-prediccion/`,
     `docs/exploraciones-respiratorias/`, `docs/clasificador-retirado/`
     (+ `entrenamientos/`).
   - Mover los 24 archivos con 0 refs **+ sus clusters completos** (incluyendo
     los de Fase 2 que pertenecen al mismo cluster, para no partir enlaces).
   - Actualizar enlaces relativos entre docs movidos (§2).
   - Actualizar `entrenar_clasificador.py:301,306` (f-string) + su test.
   - Actualizar el árbol de ejemplo en `AGENTS.md:451–457`.
   - Verificar: `backend-tests.yml` (toca `test_entrenar_clasificador.py`).

3. **PR 2 — docs referenciados desde backend / SQL / manifiestos** (riesgo medio)
   - Mover `protocolo-evaluacion-rescate-prediccion.md`,
     `tarea-rescate-prediccion.md`, `experimento-ventana-climatica-ampliada.md`,
     `experimento-validacion-leadtime-camino-ancho.md`,
     `exploracion-{ira,neumonias,vigilancia-virus}-*.md`,
     `corrida-canal-endemico-*.md`.
   - Actualizar: comentarios y strings en `backend/api/*.py`,
     `backend/ingestion/*.py`, los **4 manifiestos Vía** (campos `protocolo` /
     `tarea` — NO afecta `seed_sha256`), strings en
     `db/migrations/0007_*.sql` y `0008_*.sql` (comentarios en `INSERT`; la
     migración ya aplicada no se re-ejecuta, pero instalaciones limpias sí — el
     string es documental, no funcional), `backend/ingestion/tests/`.
   - Verificar: `backend-tests.yml` completo (incluye `test_validar_via_*`,
     `test_corrida_ira`, `test_corrida_respiratorios`). Confirmar que ningún
     `test_validar_via_*.py` *asserta* sobre `fuente.protocolo` / `fuente.tarea`.

4. **PR 3 — (opcional, solo si se decide mover los 3 de biblioteca)** (riesgo alto)
   - Solo si el usuario quiere agrupar los 3 docs de biblioteca.
   - Actualizar `web/src/content.config.ts` (`pattern`),
     `web/src/pages/biblioteca/index.astro` (`ORDEN_BIBLIOTECA` ids),
     `web/src/components/MetricasModelo.astro:53` (URL de GitHub hardcodeada).
   - Verificar: `pnpm build` + `pnpm preview` en **puerto 4321** + navegar
     `/biblioteca` y `/biblioteca/<nuevo-id>`.
   - **Recomendación: NO hacer este PR.** Dejar los 3 en `docs/` raíz.

5. **Follow-ups (fuera de #60):** ADR de `variables_ambientales`; decisión de
   coordinación sobre el clasificador retirado en `backend/ingestion/`; decisión
   del usuario sobre `docs/tobeer/`.

---

## 8. Decisiones del usuario (resueltas 2026-09-06)

1. **`docs/tobeer/`**: **BORRAR** toda la carpeta; quitar el enlace en `diagnostico-senal-etiqueta-auditoria.md`.
2. **Los 3 docs de biblioteca**: **MOVER** (PR 3 se ejecuta) — actualizar `content.config.ts`, `ORDEN_BIBLIOTECA`, rutas `/biblioteca/<id>` y la URL de GitHub hardcodeada en `MetricasModelo.astro:53`; verificar con `preview` en puerto 4321.
3. **Nombres de subcarpetas**: OK — `experimentos/`, `rescate-prediccion/`, `exploraciones-respiratorias/`, `clasificador-retirado/` (+ `entrenamientos/`).
4. **`CHANGELOG.md`**: actualizar enlaces por coherencia.
5. **Strings en migraciones `0007`/`0008`**: actualizar la ruta.
6. **`backend/ingestion/`**: **fuera de #60**. Confirmado.
7. **`variables_ambientales`**: fuera de #60, follow-up con ADR. Confirmado.

### Planteo original

1. **`docs/tobeer/`**: ¿borrar, archivar en `docs/clasificador-retirado/entrega-isaac/`, o dejar?
2. **Los 3 docs de biblioteca**: ¿se quedan en `docs/` raíz (recomendado) o se mueven con actualización de `content.config.ts` + rutas + URL hardcodeada?
3. **Nombres de las subcarpetas** propuestas: `experimentos/`, `rescate-prediccion/`, `exploraciones-respiratorias/`, `clasificador-retirado/`. ¿OK?
4. **`docs/contexto/CHANGELOG.md`**: ¿reescribir enlaces a rutas nuevas o dejar los históricos apuntando a las rutas de su fecha?
5. **Strings en migraciones `0007`/`0008`**: son comentarios dentro de `INSERT` de catálogo. ¿Actualizar la ruta (coherencia en instalaciones limpias) o dejarlos (la migración ya aplicada no cambia)?
6. **`backend/ingestion/`**: se deja **fuera de #60** (namespace plano + decisión abierta 02-decisiones-abiertas.md:55). ¿Confirmado?
7. **`variables_ambientales`**: fuera de #60, follow-up con ADR. ¿Confirmado?

---

*Claude-Session: https://claude.ai/code/session_018DEbMYkeqCW2y6gmkzM22r*
