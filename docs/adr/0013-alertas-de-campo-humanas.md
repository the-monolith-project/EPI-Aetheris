# 0013 - Persistencia de alertas de campo humanas

**Estado:** Aceptado (2026-09-06)

> Aceptado para la sección pública `/alertas` (Expotécnica). Las alertas
> son decisiones humanas fechadas; no se derivan de M1–M3 ni del
> clasificador retirado. Migración:
> `db/migrations/0009_alertas_de_campo.sql`.

**Nota de estado (2026-09-07):** Parcialmente superado por ADR 0015
(2026-09-07): la creación autenticada y el archivo por fecha ya no
están fuera de alcance. El cuerpo de este ADR se conserva intacto.

## Contexto

La página `/alertas` es el puente entre quien revisa los módulos de
dengue o respiratorio y quien atiende en una unidad de campo. El flujo
pedido (`INDICACIONES_ALERTAS.md`) es: una persona del equipo de
vigilancia decide emitir una alerta, la redacta, y el médico ve si hay
algo vigente y qué hacer.

Eso choca con dos tentaciones ya cerradas en sentido contrario:

- M1/M2/M3 son descriptivos y **no exponen alerta binaria** (pivote
  Camino Ancho, 2026-08-18). Convertir Iv, Z-score o percentil en una
  fila de alerta reabriría lenguaje de aviso automático.
- El clasificador nacional está retirado. No hay etiqueta alto/medio/bajo
  en producción que se pueda “promover” a alerta.

Hace falta una tabla nueva: el dato no cabe en `casos_epidemiologicos`
(no es un conteo) ni en un cálculo on-request (el texto lo escribe una
persona, con autor y vigencia). Ampliar el esquema exige ADR previo.

Fuera de alcance de este ADR: autenticación, roles y formulario de
administración. La creación para la demo es inserción SQL/seed.

## Decisión

Crear la tabla `alertas` con los campos y valores controlados siguientes.
El nivel y el tipo los asigna quien emite; **no se recalculan**.

```text
id              BIGSERIAL PRIMARY KEY
tipo            TEXT NOT NULL   CHECK (dengue | respiratorio)
nivel           TEXT NOT NULL   CHECK (informativo | atencion | intensificacion)
titulo          TEXT NOT NULL
contexto        TEXT NOT NULL   -- qué muestran los datos, con la fuente
indicaciones    TEXT NOT NULL   -- qué hacer en la unidad (lista accionable)
fuente          TEXT NOT NULL   -- dataset + rango de semanas/años
autor           TEXT NOT NULL   -- rol o iniciales del equipo de vigilancia
vigente_desde   DATE NOT NULL
vigente_hasta   DATE            -- nullable
activa          BOOLEAN NOT NULL DEFAULT TRUE
```

Reglas:

- La vista pública lista solo filas con `activa = TRUE`. `activa` es el
  filtro principal; no se infiere de `vigente_hasta`. Una fila vencida
  que siga `activa` permanece visible hasta que el equipo la apague.
- No hay `POST`/`PUT`/`DELETE` de alertas en la API. El único camino
  HTTP es `GET /api/alertas` (filtro opcional `tipo`).
- Nada en esta tabla se rellena desde idoneidad, anomalía, presión,
  canal endémico ni el joblib del clasificador retirado.
- Las dos alertas de demo (una de dengue y una de respiratorio, más una
  fila inactiva para probar el filtro) se insertan en la misma
  migración, como dato de dominio. No se regenera
  `db/seed/seed_datos_reales.sql` (ADR 0010).
- `contexto` e `indicaciones` se guardan como texto (listas y
  párrafos). El frontend los escapa al renderizar; no se introduce un
  motor markdown.

### Alternativas descartadas

* Generar la alerta desde un umbral de M3 o del canal endémico —
  descartado: reintroduce alerta binaria y lenguaje de aviso automático
  que el pivote Camino Ancho retiró.
* Reutilizar `casos_epidemiologicos` o una columna de “nivel” en
  regiones — descartado: una alerta es un texto operativo firmado, no un
  conteo ni un atributo geográfico.
* Formulario de administración en este alcance — descartado: exigiría
  autenticación y una superficie de escritura HTTP que el documento
  pide no construir para la Expotécnica.

## Consecuencias

* Positivo: el médico ve un texto humano, fechado y con fuente; el
  encuadre de honestidad cabe en la misma página sin fingir tiempo real.
* Positivo: M1–M3 y el clasificador no cambian de contrato.
* Negativo: emitir o apagar una alerta exige acceso a la base (SQL o
  seed), no una pantalla. Es deliberado en este alcance.
* Neutral: `vigente_hasta` nulo significa “sin fecha de cierre
  declarada”, no vigencia infinita automática.
