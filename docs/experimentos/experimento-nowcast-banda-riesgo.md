# Experimento: banda de riesgo para M0 y C, un límite alto que depende del crecimiento (2026-10-03)

> Protocolo fijado el 2026-10-03, antes de escribir y de correr el script, en la rama
> `feat/mejora-tablero-banda-alta`, que sale de `feat/mejora-tablero-fase0`. Es la Fase 3 del plan
> de mejora del predictor para la serie del tablero. No toca la prueba prospectiva firmada en
> `experimento-nowcast-tendencia.md` (script congelado en 40b6ebb, semanas objetivo desde
> 2026-S38). Ninguna decisión de este documento usa una semana objetivo posterior a 2026-S37.
> No modifica `nowcast_estimacion_dengue.py` ni los artefactos publicados.

## Pregunta

El producto pasaría a tener dos bandas. La banda central queda como está (intervalos del 50 % y
del 95 %, sin ningún cambio). La banda de riesgo es un único límite superior por semana de
horizonte, pensado para planificar cuando los casos están subiendo, con su propio puntaje. Este
experimento decide con qué regla se calcularía ese límite, si alguna sirve.

1. El cuantil 0,975 que hoy publica M0, ¿se queda corto cuando el crecimiento es alto? Se mide
   con la cobertura unilateral al 97,5 % por tercio de crecimiento.
2. Un factor que ensancha el semiancho superior con los errores pasados, sin winsorizar y sin
   tope, ¿corrige esa cobertura a un costo de ancho aceptable? Y condicionar ese factor al
   régimen de crecimiento, ¿aporta algo sobre un factor global?
3. Una tabla de factores fijada con la historia de OpenDengue, ¿sirve para C en la serie del
   tablero (dentro de muestra)?

## Exploración previa, declarada

- Un sub agente leyó la transcripción de una revisión externa del modelo y calculó, de forma
  descriptiva y sin protocolo, la cobertura del intervalo central del 95 % por tercio de
  crecimiento a 3 semanas (serie sin suavizar, cortes de los tercios con todas las filas
  evaluadas). En M0 sobre OpenDengue (objetivos 2019, 2021 a 2024) el tercio alto cubre 0,78 a
  h = 4; en C sobre el tablero (2025 a 2026-S37) cubre entre 0,93 y 0,96, con n = 27. Esas cifras
  motivan el experimento y no se usan para decidir: aquí el crecimiento se mide sobre la serie
  suavizada que ve T, los cortes usan solo datos anteriores a cada origen y el objeto es la
  cobertura unilateral.
- Se leyó la estructura de `rangos.json` y el código de CQR-r (score simétrico, winsorización al
  p90, factor en [0; 4]). No se calculó ninguna métrica de esta fase.
- Antecedente en `experimento-nowcast-rangos.md`: la calibración asimétrica R1 (un factor por lado,
  winsorizada al p90, 52 pares) bajó la cobertura del 95 % a 0,77 y 0,79, porque con tan pocos
  pares la winsorización estrecha el factor de cada lado. Las capas de abajo no winsorizan, no
  topan y acumulan todos los pares pasados. Las variantes sin winsorizar del script
  `experimento_nowcast_tablero.py` (`V3_sin_winsor`, `V4_ventana_sin_winsor`) no tienen resultados
  documentados en `docs/`; su salida no se usa aquí.
- No se añaden pruebas después de ver los resultados. Lo que se mire después se rotula
  exploratorio.

## Datos

- Filas guardadas en `docs/agentes/mejora-predictor/resultados-nuevos/rangos.json`: bloques
  `A_h1` a `A_h8` (M0 con R0, `q_R0`, objetivos 2019, 2021, 2022, 2023 y 2024; 256 filas a h = 4)
  y `B_h1` a `B_h8` (objetivos 2024, 2025 y 2026-S1 a S37; M0 en `q_R0` y C en `q_C_R0`). Cada fila
  trae origen, año y semana del objetivo, `y` y 23 cuantiles en casos, ordenados, con 3 decimales.
  Los cuantiles 0,5, 0,975 y 0,99 son los índices 11, 21 y 22.
- Serie mixta nacional (`cargar_serie_mixta`) con la historia suavizada de k = 7 hasta 2023
  (`historia`), la misma que usa T. Semanas sin dato, como 2025-S53, quedan como NaN y las filas
  que las necesitan se descartan, igual para todas las capas.
- Todo se hace sobre cuantiles guardados, sin reentrenar nada. El cómputo es de segundos.

## Régimen de crecimiento

Para un origen o, el crecimiento es g_o = z_o − z_(o−3), con z el log1p de la serie suavizada. Los
cortes son los percentiles 33,3 y 66,7 de todos los g con fecha menor o igual a la del origen,
desde el inicio de la serie y sin excluir 2020. Por eso los cortes cambian con el origen y no usan
el futuro. El régimen es bajo (cae), medio (plano) o alto (sube). Cada origen recibe su etiqueta
con los cortes calculados hasta ese origen y la conserva: un par pasado lleva la etiqueta que tuvo
en su propio origen.

## Capas

Todas actúan sobre el cuantil 0,975 y sus vecinos superiores, en escala log1p, y vuelven a escala
natural. Con m = log1p(mediana), u = log1p(cuantil 0,975) y l = log1p(y), el score de un par es
s = (l − m) / max(u − m, 0,001). Para una fila se usan los pares pasados del mismo horizonte y del
mismo bloque con fecha objetivo anterior a la del origen de la fila (misma convención que
`experimento-nowcast-rangos.md`). El factor es el cuantil conforme de nivel
min(ceil((n + 1) · 0,975) / n; 1) de los n scores, con el máximo cuando el nivel llega a 1 y
`method="higher"` en el resto, y se aplica así: límite = m + max(1; f) · (u − m). Con ese
piso el límite de riesgo nunca queda por debajo del límite central publicado.

| Capa | Definición |
|---|---|
| L0 | Referencia: el cuantil 0,975 guardado (M0 en la parte A, C en la parte B). |
| L1 | Factor global: f sobre todos los pares pasados del horizonte. Con menos de 40 pares, L0. |
| L2 | Factor por régimen: f sobre los pares pasados del mismo régimen que la fila. Con menos de 40 pares en ese régimen, L1. |

La ventana es expansiva y no se afina. El mínimo de 40 pares es el entero siguiente a 39, el menor
n con el que el máximo de los scores da el nivel conforme del 97,5 %. Con menos de 80 pares el
factor es, en la práctica, el máximo de los scores, y se informa la fracción de filas en que cada
capa opera con su factor propio y no con el de reserva.

Las filas de evaluación son las que tienen al menos 40 pares pasados (las primeras semanas de 2019
quedan fuera del puntaje de todas las capas por igual). El nivel 0,99 se calcula con el mismo
factor aplicado al semiancho hasta el cuantil 0,99 y se informa como secundario, sin peso en la
decisión, porque con estos tamaños de muestra no se puede verificar.

## Fases

Parte A, validación (decide): M0 sobre OpenDengue, bloques A, h = 1 a 8, capas L0, L1 y L2 con
calibración hacia adelante dentro del propio bloque.

Parte B, serie del tablero (se mira una vez, dentro de muestra): objetivos de 2025-S1 a 2026-S37
sobre el bloque B, h = 1 a 8, con la capa elegida en la parte A. La tabla de factores se ajusta
una sola vez con todos los pares del bloque A (L1: un factor por horizonte; L2: uno por horizonte
y régimen) y se aplica sin reajuste al semiancho superior de C. Las filas de B reciben su régimen
con los cortes de su propio origen, como en A. La tabla usa pares con objetivo hasta 2024-S52, de
modo que los orígenes de las primeras semanas de 2025 con h grande la ven con a lo sumo 8 semanas
de adelanto; se declara y no se corrige. Se informa además, como descriptivo,
la misma capa con calibración hacia adelante dentro del bloque B y la tabla aplicada a M0.

## Métricas

Sobre las mismas filas para todas las capas:

1. Cobertura unilateral al 97,5 %: fracción con y menor o igual al límite. Por horizonte, agregada
   en h = 1 a 8 y por régimen (el del origen de la fila), con el número de excedencias.
2. Pérdida pinball al cuantil 0,975 en casos, rho = 0,975 · (y − l)+ + 0,025 · (l − y)+, y su
   razón contra L0 sobre las sumas, por horizonte, agregada y por año de objetivo.
3. Ensanchamiento: razón media entre (límite − mediana) y (cuantil 0,975 − mediana), en casos.
4. Diebold-Mariano sobre la diferencia de pinball sumada en los 8 horizontes por origen (solo
   orígenes con los 8 horizontes evaluables), Newey-West con rezago 7 y corrección de
   Harvey-Leybourne-Newbold con h = 8, para L1 contra L0, L2 contra L0 y L2 contra L1. Se
   ajustan los tres p con Holm.
5. Secundarias: nivel 0,99, cobertura y pérdida por año, y la cobertura del intervalo central del
   95 % por régimen, para dejar medida la brecha de partida.

## Controles

- Con las filas guardadas, la cobertura del 50 % y la del 95 % de `q_R0` (bloque A) y de
  `q_C_R0` (bloque B, 2025 y 2026) por horizonte debe coincidir con la de `rangos.json`
  (`fase_A.tablas[h].R0`, `fase_B.tablas[h].C_R0`), con diferencia menor o igual a 0,005. Si no,
  se detiene el experimento.
- Control negativo del régimen: 200 barajados de las etiquetas de régimen entre los orígenes de A
  (la misma permutación para los 8 horizontes, semilla 0), con L2 recalculada en cada uno. Si
  el régimen real aporta, la razón de pinball de L2 contra L1 queda por debajo de la mayoría de las
  barajadas. Además, L2 con todas las filas en un mismo régimen debe reproducir L1 sin diferencia.
- Pruebas unitarias de las funciones puras: factor conforme (casos de n de 39, 40 y 80), cortes de
  los tercios sin uso de datos posteriores al origen, piso de 1 en el factor.

## Regla de decisión

Parte A. Una capa X de {L1, L2} pasa si cumple todo, sobre h = 1 a 8 agregado salvo donde se dice
otra cosa:

- cobertura unilateral al 97,5 % en el tercio de crecimiento alto de al menos 0,95;
- cobertura unilateral total entre 0,96 y 0,99;
- razón de pinball de X contra L0 de a lo sumo 1,00, y menor que 1,00 en al menos 5 de los 8
  horizontes;
- razón de pinball menor o igual a 1,00 en al menos 4 de los 5 años de objetivo;
- ensanchamiento medio de a lo sumo 2,0.

Si pasan las dos, se elige L2 solo si su razón de pinball contra L1 es menor que 0,98 y queda
por debajo del percentil 10 de las razones barajadas; si no, L1, que tiene menos grados de libertad.
Si pasa una sola, esa. Si no pasa ninguna, el límite alto sigue siendo el cuantil 0,975 publicado
y la cobertura por régimen se documenta como limitación.

Los p de Diebold-Mariano se informan y no condicionan la elección: con unas pocas decenas de
orígenes independientes la prueba tiene poca potencia, y la regla de arriba ya exige consistencia
entre horizontes y años. Si una capa pasa sin significancia, el resultado se redacta como mejora
en la muestra de validación.

Parte B. La capa elegida se considera aplicable al tablero si, sobre C, cumple a la vez cobertura
unilateral total entre 0,95 y 0,99, ensanchamiento medio de a lo sumo 2,0 y razón de pinball contra
C con L0 de a lo sumo 1,03. Si no se cumple, la tabla de OpenDengue no se traslada y la banda del
tablero queda a la espera de pares propios (hoy hay menos de 40 por régimen) y de la ventana
prospectiva de la Fase 4. El resultado de B es dentro de muestra y se rotula así.

## Qué se decide y qué no

Se decide si hay una regla candidata para la banda de riesgo y si su tabla sirve para el tablero.
No se cambia la web, el backend ni la banda central. Publicar la banda exige un cambio aparte, con
su texto de lectura, y queda para después de ver los resultados.

## Salidas

- Script `backend/ingestion/experimento_nowcast_banda_riesgo.py` con `--control`, `--parte-a` y
  `--parte-b`.
- `docs/agentes/mejora-predictor/resultados-nuevos/banda_riesgo.json`.
- Sección de resultados en este documento.
