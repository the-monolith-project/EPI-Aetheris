# Corrida reproducible — Vía 1

**Fecha:** 2026-08-18

**Estado técnico:** completada

**Veredicto:** no adoptar

**Interpretación permitida:** estimación reconstructiva de corto plazo con casos ya observados

**Interpretación no permitida:** alerta anticipada, desempeño final independiente o modelo listo para
producción

## Resultado

Agregar casos previos no rescata la etiqueta de canal endémico bajo la validación limpia. En el único
fold con semanas `alto` reales, 2022, las dos variantes obtienen F1 macro 0,273, recall de `alto`
0,000 y **0 de 5 aciertos en las 10 semillas**. El resultado coincide con las referencias
climatológica y mayoritaria y queda muy por debajo de persistencia.

La causa inmediata estaba congelada antes de ajustar el modelo: el entrenamiento de ese fold no
contiene ningún ejemplo `alto`. Random Forest no puede emitir una clase que nunca observó. Los folds
posteriores ya contienen cinco ejemplos `alto` en entrenamiento, pero sus externos no contienen
ninguno y su recall es `N/A`.

Las variantes `solo_casos` y `casos_mas_clima` producen los mismos resultados en todos los folds. El
clima no aporta una mejora justificable sobre los casos rezagados. La vía obtiene **0 de 10 semillas
exitosas** en su único fold evaluable.

## Qué cambió respecto de producción

La etiqueta, los años externos, las referencias y el criterio permanecen iguales a la Vía −1. Se
compararon dos firmas de predictores congeladas antes de ejecutar:

- `solo_casos`: casos de lag 1, casos de lag 2 y media de las cuatro semanas anteriores;
- `casos_mas_clima`: las tres columnas anteriores más los 21 predictores climáticos de la Vía −1.

Ninguna columna incluye la semana objetivo. Las semanas 1–4 de 2021 se excluyen porque alguno de sus
rezagos de casos pertenece a 2020, año excluido de toda vía. No hubo imputación, selección de
features, ajuste de hiperparámetros ni barrido de umbral.

El experimento toca dos decisiones cerradas: el predictor oficial es únicamente climático y el
producto promete anticipación. La autorización de Eduardo habilitó la corrida experimental, pero no
modifica esas decisiones ni adopta el resultado. Aun si hubiera funcionado, esta variante requeriría
casos recientes y solo podría presentarse como estimación del presente o de muy corto plazo. La
fuente nacional disponible tampoco se actualiza semana a semana.

## Resultados por año

Las dos variantes del modelo tienen métricas idénticas. Cada recall aparece con sus aciertos
absolutos; `N/A — 0 de 0` significa que el externo no contiene semanas `alto`. `FP` son falsos
positivos de esa clase. Persistencia excluye una fila cuando no dispone de una semana anterior
comparable.

| Externo | Modelo, ambas variantes y 10 semillas | Climatológica | Mayoritaria | Siempre `alto` | Persistencia |
|---|---|---|---|---|---|
| 2019 | no entrenable; una sola clase en train | F1 0,327; recall N/A — 0 de 0; 0 FP | F1 0,327; recall N/A — 0 de 0; 0 FP | F1 0,000; recall N/A — 0 de 0; 50 FP | F1 0,319; recall N/A — 0 de 0; 0 FP |
| 2021 | F1 0,333; recall N/A — 0 de 0; 0 FP | F1 0,333; recall N/A — 0 de 0; 0 FP | F1 0,333; recall N/A — 0 de 0; 0 FP | F1 0,000; recall N/A — 0 de 0; 48 FP | F1 0,333; recall N/A — 0 de 0; 0 FP |
| **2022** | **F1 0,273; recall 0,000 — 0 de 5; 0 FP; éxito 0/10** | F1 0,273; recall 0,000 — 0 de 5; 0 FP | F1 0,273; recall 0,000 — 0 de 5; 0 FP | F1 0,058; recall 1,000 — 5 de 5; 47 FP | F1 0,766; recall 0,600 — 3 de 5; 2 FP |
| 2023 | F1 0,333; recall N/A — 0 de 0; 0 FP | F1 0,333; recall N/A — 0 de 0; 0 FP | F1 0,333; recall N/A — 0 de 0; 0 FP | F1 0,000; recall N/A — 0 de 0; 52 FP | F1 0,333; recall N/A — 0 de 0; 0 FP |
| 2024 | F1 0,333; recall N/A — 0 de 0; 0 FP | F1 0,333; recall N/A — 0 de 0; 0 FP | F1 0,333; recall N/A — 0 de 0; 0 FP | F1 0,000; recall N/A — 0 de 0; 52 FP | F1 0,333; recall N/A — 0 de 0; 0 FP |

Los externos contienen 50 filas en 2019, 48 en 2021 y 52 en 2022–2024. La diferencia de 2021 se
debe exclusivamente a la regla predeclarada sobre rezagos que cruzan 2020.

## Controles contra fuga

Antes del primer ajuste se congelaron:

- manifiesto: `backend/ingestion/via_uno_manifesto_congelado.json`;
- firma de preparación: `314e8662fd29c08b283a3fdfc9500591e821f633fb7d1e2cf193d648080d4e8c`;
- 304 filas, variantes de 3 y 24 predictores, descartes y estados de los cinco folds;
- modelo de 300 árboles, `class_weight="balanced"`, argmax y semillas 0–9; la semilla 42 solo se
  conserva como referencia histórica.

Se ejecutaron 12 pruebas sobre el seed real. Cubren autorización y hashes, firma congelada,
construcción exacta de rezagos, exclusión de 2020, semana objetivo fuera de los predictores,
dependencia efectiva de casos anteriores, independencia frente al externo y datos posteriores,
faltantes sin imputación, persistencia y configuración fija.

Con `VIA_UNO_MUTACION_FUGA=1`, la prueba correspondiente falla al introducir deliberadamente la
semana objetivo en sus propios predictores. Sin la mutación, vuelve a `OK`.

## Reproducibilidad

Dos corridas completas produjeron los cinco artefactos sustantivos idénticos byte por byte:

| Artefacto | SHA-256 |
|---|---|
| `etiquetas.csv` | `0f2ff2f90afd09389f1e08a0cd96dce42288761232a7c116529a1b976dc17d36` |
| `dataset.csv` | `7d7230c170abcb51bfe18805098ce048a9ce3cf633a4ec0d84cbb23c9c7ddbea` |
| `predicciones.csv` | `2b1453ac59cbe0c0aa8f7c9f1c991c35126ff103774b4689688b9aa121d79089` |
| `metricas.json` | `77f541f4c02fd60d853f5244fb646f9d189524bea23ace09dba718ed8bae2fa0` |
| `firma_previa.json` | `65d044efa84f260540aaea82ff83c7043aafbb1b746aae0352f582c345a59844` |

El entorno fue Python 3.11.15, NumPy 2.4.6 y scikit-learn 1.5.1 dentro de la imagen del backend.
`manifiesto_ejecucion.json` y `ejecucion.log` incluyen hora y ruta, por lo que esa metadata no es
byte-idéntica por diseño.

## Reproducción

```bash
docker compose run --no-deps --rm \
  -v ./db:/workspace/db:ro backend \
  python ingestion/validar_via_uno.py \
  --seed-sql /workspace/db/seed/seed_datos_reales.sql

docker compose run --no-deps --rm \
  -v ./db:/workspace/db:ro \
  -e VIA_UNO_SEED_SQL=/workspace/db/seed/seed_datos_reales.sql \
  backend python -m unittest ingestion.tests.test_validar_via_uno -v
```

Los artefactos quedan en `backend/ingestion/data/interim/via_uno/`, ruta ignorada por Git. El
runner no se conecta a PostgreSQL, no guarda modelos y no toca producción.

## Cierre técnico

La Vía 1 debe cerrarse y no adoptarse. Los casos previos no pueden compensar la ausencia completa de
ejemplos `alto` en el entrenamiento del único fold decisivo, y sumar clima no cambia ninguna
métrica. El resultado tampoco satisface la promesa operativa de anticipación.

La incorporación de este cierre al registro oficial sigue a cargo del coordinador.
