# Análisis: dónde fallan los rangos de la predicción en 2026 (2026-10-03)

> Plan fijado el 2026-10-03, antes de calcular nada, en la rama `feat/mejora-predictor-agente`.
> Es un análisis descriptivo: no elige ni compara candidatos, no tiene criterio de éxito y no
> cambia el modelo. Responde a la revisión del PR the-monolith-project/EPI-Aetheris#167.

## Pregunta

En 2026, con la serie del tablero, la cobertura del 95 % de la predicción publicada (C) queda
en 0,79 a 4 y a 8 semanas, por debajo del 0,85 que exige la prueba prospectiva. ¿En qué semanas
objetivo cae fuera lo observado, por qué lado, y cuál de los dos componentes de C (M0 o la
tendencia amortiguada T) explica el desvío?

## Datos

Solo las predicciones ya guardadas en
`docs/agentes/mejora-predictor/resultados-nuevos/rangos.json` (fase B, capa R0, que es el
método publicado: C = mezcla 0,5 en log de M0 calibrado con CQR-r y T). No se corre ningún
modelo ni se consulta Postgres. Semanas objetivo de 2026-S1 a 2026-S37; las semanas 4 a 11 no
tienen predicción porque sus rezagos tocan el hueco de 2025-S53. Ninguna semana desde
2026-S38. 2025 se reporta al lado como comparación.

Esas predicciones se hicieron sin ONI de 2025-2026 en la base (enmienda 6 del experimento de
rangos) y difieren levemente del artefacto servido; el análisis describe esta corrida.

## Qué se calcula

Para cada horizonte h = 1 a 8 y cada semana objetivo de 2025 y 2026:

- si lo observado cae dentro del rango del 95 % y del 50 % de C, y por qué lado sale;
- el nivel del cuantil de C en que cae lo observado (interpolado entre los 23 cuantiles;
  0 o 1 si queda fuera de los extremos);
- el error de la mediana en escala `log1p` (mediana menos observado; positivo = predijo de más)
  para C, M0 y T.

Agrupado por tramo de semanas objetivo: S1 a S3 (cambio de año), S19 a S22, y el resto. Por
tramo se reporta n, cobertura del 95 % y del 50 %, fallos por arriba y por abajo, y el error
medio de la mediana de C, M0 y T. Además, la cobertura del 95 % de 2026 sin los dos tramos, como
medida de cuánto pesan.

Los tramos S1-S3 y S19-S22 los señaló el ADR 0020 al documentar la cobertura de 2026; no se
eligen mirando estos datos. No se añaden tramos después de ver los resultados.

## Reproducibilidad

Script `backend/ingestion/analisis_nowcast_cobertura_2026.py`, sin base de datos. Salida en
`docs/agentes/mejora-predictor/resultados-nuevos/cobertura_2026.json`.
