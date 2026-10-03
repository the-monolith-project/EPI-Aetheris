# 0023 - Clima y dengue: análisis descriptivo por año y por país

**Estado:** Propuesto (2026-10-03)

## Contexto

La ablación del clima en el predictor de dengue (ADR 0020) mostró que el aporte de las variables climáticas cambia de un año a otro. Con horizonte de 4 semanas, la diferencia de skill atribuible al clima fue de −0,040 en 2019, +0,075 en 2021, +0,314 en 2022, −0,029 en 2023 y −0,227 en 2024. Dos análisis descriptivos posteriores, con protocolo fechado el 2026-10-03 y escrito antes de correr el código, miden la relación entre el clima y la serie de casos:

- Por año, para El Salvador (2014 a 2019 y 2021 a 2023): correlación entre la anomalía climática y la anomalía del crecimiento de los casos a 4 semanas, ciclo medio y desfase, perfil de cada año y consistencia entre años.
- Por país, para 18 países de las Américas con serie semanal de OpenDengue (OPS): señal regional y posición de El Salvador, la misma asociación semanal en cada país, ciclo medio y lectura de las corridas multipaís del clasificador retirado.

La investigación forma parte del producto. Mostrar estos datos permite que otras personas ubiquen a El Salvador frente a los otros países y que un análisis posterior parta de cifras con procedencia.

## Decisión

A. Dos artefactos JSON versionados en `backend/api/datos/`: `clima_dengue_por_anio.json` y `clima_dengue_multipais.json`. Se sirven tal cual por `GET /api/clima-dengue/por-anio` y `GET /api/clima-dengue/multipais`, con el contrato de `/api/nowcast-dengue`: sin el archivo responde 200 con `disponible: false` y `motivo`. Los dos endpoints llevan `RATE_LIMIT_HEAVY` y caché de una hora.

B. Procedencia dentro del archivo. Cada artefacto guarda sus parámetros. El multipaís guarda además el SHA-256 de las dos entradas que no se versionan (el CSV de OpenDengue y el caché climático de Open-Meteo). Los scripts son `analisis_clima_por_anio.py` y `analisis_clima_multipais.py`; no están en esta rama y se incorporarán cuando se integre la rama de experimentos.

C. Alcance del contenido. Las cifras describen datos de 2014 a 2024. No atribuyen causa a las diferencias entre años ni entre países, y no alimentan el predictor ni la capa de alertas. La posición de El Salvador entre los 18 países se presenta con su intervalo y con la sensibilidad de 9 años: la regla fijada en el protocolo permite decir que tiene la menor correlación solo si ocurre en las dos medidas, y en la de 9 años queda en la posición 5.

D. Una página, `/analisis/clima`, consume los dos endpoints. Se decide en el repositorio del frontend y no añade dependencias.

## Consecuencias

- Los dos artefactos pesan 135 KB y 323 KB sin comprimir. El segundo va en un endpoint aparte para que la página por año no lo cargue.
- Un cambio en los datos de entrada exige volver a correr los scripts y revisar las cifras citadas en el texto de la página.
- No cambia el esquema ni los contratos existentes.
- Los scripts de origen quedan fuera de esta rama, así que el archivo versionado no se puede regenerar desde `dev` hasta que se integren.
