---
titulo: "Sensibilidad y honestidad"
descripcion: "Deslindes del sistema: no diagnostica, no predice, solo datos agregados, métricas visibles y un aporte de ingeniería — no de novedad epidemiológica."
orden: 5
categoria: "Datos y método"
---

Este es el documento canónico de los límites de EPI-Aetheris. El resto del sitio describe lo que el sistema **hace**. Aquí se declara, una vez y con el detalle que hace falta, lo que **no afirma** y por qué. Las pantallas del producto pueden enlazar aquí en vez de repetir el mismo párrafo en cada vista.

## Ayuda de priorización, no oráculo médico

EPI-Aetheris es una herramienta de **vigilancia descriptiva**. Cruza series públicas, calcula índices y percentiles contra la propia historia de cada departamento, y muestra el resultado con la procedencia a la vista.

No es:

- un **diagnóstico** de un paciente;
- un **pronóstico** de la semana que viene;
- una **certeza clínica**;
- una **recomendación médica** redactada por el sistema;
- un **descubrimiento epidemiológico** nuevo.

La interfaz no debe afirmar que un color del mapa "es" un brote, ni que un percentil alto "anticipa" un ascenso. Un valor de M1, M2 o M3 describe el clima o los casos **ya observados**. Quien prioriza fumigación, camas o campañas lo hace con ese contexto más el juicio del personal de salud — no sustituyendo ese juicio.

El coordinador precisó el 7 de septiembre de 2026 el borde fino de esta regla. **Sí está permitido** mostrar recomendaciones de prevención **ya publicadas** por OPS/OMS o MINSAL, citando la fuente: tarjetas del tipo "elimine criaderos, revise depósitos de agua". Reproducir una guía pública no es diagnosticar ni predecir. **No está permitido** que el sistema *redacte* indicaciones clínicas propias, ni que las derive automáticamente del nivel de M1–M3, de M4 o del clasificador retirado. M4 describe calidad del dato (completitud, cuadre, antigüedad), no transmisión.

Los campos clínicos de una alerta de campo (`definicion_caso`, `signos_alarma`, `criterios_referencia`, `que_notificar`, `contacto_vigilancia`) son contenedores. Los llena el equipo con transcripción atribuida. Inventar un número de teléfono o un criterio de referencia para que la tarjeta "se vea completa" sería la peor versión de esa función.

## Por qué se retiró el clasificador

El objetivo original era clasificar riesgo de brote alto/medio/bajo por semana, con clima rezagado. Se construyó, se evaluó y se cerró el **18 de agosto de 2026**.

Hechos, no atmósfera:

- El clasificador nacional de producción obtuvo **recall de "alto" = 0,000** en 2019 y en 2022, los únicos años de la ventana con semanas reales de esa clase.
- Cinco vías de rescate (fuga temporal, transferencia multipaís, casos previos, posición estacional, features con mecanismo biológico) no sostuvieron el criterio de éxito predeclarado. Vía 0: 0 de 16 países. Vías 1 y 3: 0 de 10 semillas en el único fold evaluable.
- El experimento de lead time del mismo día produjo, en los dos únicos casos comparables, **+29 y −30 semanas**, sin acuerdo de signo.

La recomendación del informe de cierre fue entregar ese resultado negativo como evidencia reproducible, no integrar una clasificación experimental al tablero como si fuera una alerta. El código (`entrenar_clasificador.py` y la línea de `docs/clasificador-retirado/`) **se conserva** para que cualquiera repita las corridas. Conservarlo no es una invitación a reactivarlo: no se extiende, no se expone en vivo, no se pinta como semáforo departamental.

Retirarlo es coherente con el Pilar 3 del marco del proyecto (márgenes de error declarados, prohibidos los atajos). Dejar un modelo con recall 0 en la clase que justifica el pitch habría sido exactamente el atajo que el estatuto prohíbe.

## Solo datos agregados, sin datos personales

El sistema trabaja con conteos por departamento-semana y con reanálisis climático. No hay nombres, documentos, historias clínicas ni geolocalización de personas.

Eso gobierna el diseño, no solo el discurso:

- No hay tabla de usuarios. La API pública de lectura (`GET /api/alertas`, módulos, series) no pide cuenta.
- La escritura de alertas (ADR 0015) usa un **secreto de entorno** (`ALERTAS_TOKEN`, cabecera Bearer, comparación con `secrets.compare_digest`). No hay cuentas, correos ni nombres de operador en la base. Si el secreto no está definido, `POST`/`PATCH` responden 503 y no escriben. No hay `DELETE`: una alerta emitida se desactiva, queda en el archivo.
- El token no se versiona. El formulario `/alertas/nueva` no aparece en la navegación; el token no se guarda en `localStorage` salvo opción explícita del operador.
- El feedback de quien usa el sitio no pasa por un formulario propio que guardaría texto de terceros: `/sugerencias` enruta a GitHub Issues, ya público y trazable.
- `regiones.nivel_admin = 2` (municipio) está reservado **sin filas**. No hay dato que sostenga una pantalla "mi municipio hoy", y titular una vista "hoy" o "esta semana" sobre una ventana que llega a 2023 sería fingir tiempo real.

Una propuesta anterior del equipo (AULA-PULSE, deserción escolar) se descartó precisamente porque exigía datos de menores y no había dataset público: fabricar uno se consideró inaceptable. Esa negativa es el mismo principio, aplicado antes de escribir código.

## Nada de datos fabricados

Estatuto no negociable: todo dato viene de una fuente pública, real, verificable y citable. Consecuencias concretas en el pipeline:

- No se simula una serie epidemiológica "para que la demo funcione".
- No se rellena un hueco de vacaciones repartiendo el conteo del boletín vecino.
- Las 19 correcciones retroactivas negativas de MINSAL se excluyen; no se "suavizan".
- Celdas vacías en la tabla departamental de dengue se ingieren como **0** porque la fuente lo establece así; no se convierten en 0 los huecos de otra naturaleza (boletín ausente, tabla no publicada).
- OpenDengue no se etiqueta como `confirmado`.
- `precipitation_hours` bajo un modelo que no sirve precipitación llega como `0.0` fabricado: el loader lo rechaza.
- El volcado `db/seed/seed_datos_reales.sql` (ADR 0010) es `pg_dump` de esas mismas tablas reales, no un dataset sintético. Pesa 4,4 MB y no incluye un PDF crudo.

Los campos clínicos de alertas, cuando existan, son transcripción literal con página y organismo. El equipo no "mejora" el texto de OPS para que suene más claro.

## Coexistencia temporal no es causalidad

M1 (`Iv`) y M3 (percentil de casos) pueden ser altos la misma semana. Eso es **coexistencia** de dos series alineadas por semana epidemiológica. No demuestra que el clima de esas dos semanas **causó** esos casos, ni que el índice anticipe el conteo.

El clasificador retirado se construyó precisamente sobre la hipótesis de que el clima rezagado clasifica el exceso de casos. Esa hipótesis no se sostuvo en los años con brote conocido. Presentar un scatter de temperatura contra casos como prueba de mecanismo sería repetir, en la interfaz, lo que la evaluación ya cerró.

El canal endémico y M3 comparan un departamento consigo mismo (leave-one-out, el año descrito no entra en su baseline). Eso evita un tipo de fuga. No convierte un percentil en una relación causal con la lluvia o con El Niño.

ONI se carga porque es un índice público de teleconexión, útil como contexto descriptivo. Se probó como feature del modelo semanal y no mejoró 2019/2022. Tener la serie en Postgres no autoriza a leerla como palanca de brote.

## Métricas y fallos a la vista

El estatuto pide que las métricas y los márgenes de error estén **siempre visibles**, nunca ocultos, y que la validación retrospectiva muestre fallos además de aciertos.

En la práctica:

- M1 y M2 exponen el valor continuo (`iv`, `anomaly_sigma`), no un semáforo.
- M3 expone el percentil crudo **y** la lectura baja/media/alta. Si el piso de ≥ 3 años no se cumple, el campo va `null` con nota; no se inventa un percentil.
- El informe de cierre, las corridas de cada vía y el experimento de lead time están en el repositorio, con recalls absolutos por año y con la recomendación de no adoptar.
- El mapa declara la semana y el año de la ventana cargada. No hay reloj de "esta semana".

Ocultar que 2019 y 2022 no fueron detectados por el clasificador, o que el lead time no tiene signo estable, convertiría esta Biblioteca en marketing. El proyecto eligió lo contrario: el resultado negativo es parte del entregable.

## El aporte es de ingeniería, y eso es el diferenciador

Dengue + aprendizaje automático + clima es un campo académico maduro (trabajos en Bangladesh, Vietnam, India, Brasil, con LightGBM, XGBoost, LSTM, SHAP). **EPI-Aetheris no presenta un modelo novedoso.** El clasificador que construyó no superó a una línea base climatológica en la clase que importaba.

Lo que el repositorio sí publica, y la literatura de papers habitualmente no entrega como software, es:

1. Un sistema **libre y contenedorizado** que un tercero clona y levanta con datos reales (`git clone` + `docker compose up`, ADR 0010).
2. Una arquitectura **agnóstica a evento y región** (catálogos, no columnas fijas por enfermedad).
3. Trazabilidad de cada fila a su boletín, su modelo climático y su definición de caso.
4. Un foco geográfico —El Salvador / Centroamérica— poco cubierto frente a la literatura asiática y brasileña.

Eso es un diferenciador legítimo de **ingeniería de software**, no una disculpa por no haber predicho brotes. Un oráculo médico fallido no se vuelve honesto por decir "es solo un piloto". Un sistema que ingiere, alinea, documenta y se replica sí se sostiene sin esa promesa.

Quien evalúe el proyecto puede auditar las corridas, repetir la ingesta y leer esta página. Esa es la forma de rigor que el equipo puede ofrecer.
