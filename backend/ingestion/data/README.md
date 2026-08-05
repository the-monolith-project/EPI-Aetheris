# Procedencia de los datos crudos

`data/raw/` no se trackea en git (ver `.gitignore`); este archivo sí, para dejar
constancia de dónde salió cada dato reunido en la Fase 0 de ingesta.

## OpenDengue (`data/raw/opendengue/`)

- **Archivo:** `opendengue_el_salvador_v1_3.csv`
- **Fuente:** OpenDengue Project, extracto de máxima resolución espacial
  `Spatial_extract_V1_3.zip`, distribuido en Figshare.
- **DOI:** `10.6084/m9.figshare.24259573` (v1.3)
- **URL de descarga directa:** `https://ndownloader.figshare.com/files/54854153`
- **Obtenido:** 2026-08-04
- **Transformación aplicada:** el CSV original (~2.8M filas, todos los países)
  se filtró a `ISO_A0 == "SLV"` (2208 filas) para mantener el repo liviano.
  Sin otra limpieza — es el dato crudo tal como lo entrega Figshare.
- **Cobertura confirmada en la muestra filtrada:** Admin0 (nacional)
  1978–2024, resolución semanal desde 2018; Admin1 (departamental) solo
  2000–2009, resolución mensual. Coincide con lo documentado en el contexto
  maestro del proyecto (sección 5.1).

## Boletines MINSAL (`data/raw/minsal/`)

- **Fuente:** boletines epidemiológicos en PDF de `salud.gob.sv`
  (`www.salud.gob.sv/boletines-epidemiologicos-{año}/`), fuente interna
  citada "VIGEPES".
- **Obtenidos con:** `descargar_minsal_{año}.py` / `minsal_common.py` (ver
  esos scripts para el mecanismo de descarga: ruta directa vs. ruta de
  respaldo, validación por firma de bytes `%PDF`).
- **Años reunidos:** 2018, 2019, 2021, 2022, 2023 (2020 queda fuera de la
  ventana de entrenamiento del modelo; ver decisión de alcance del
  proyecto).
- **Dos esquemas de tabla:** Familia A (2018–2020, columnas
  Probable/Confirmado/Tasa) y Familia B (2021–2023, columnas
  Probable/Confirmado sin tasa). El detector de esquema debe basarse en la
  presencia/ausencia de la columna de tasa por documento, no asumirse por
  año.
