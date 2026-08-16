"""
Tarjeta 22 -- parser de produccion de boletines MINSAL. Escribe a Postgres
(bitacora + casos_epidemiologicos), a diferencia de la corrida exploratoria
(backend/ingestion/corrida_distribucion.py, 264 PDF, verificacion 4/4) de la
que reutiliza sin reescribir la extraccion (paso 1) y la desacumulacion
(paso 2) -- ver docs/contexto/03-fuentes-de-datos.md, trampa 8/11, para la
evidencia detras de esa logica.

Alimenta unicamente la capa descriptiva del mapa (tarjeta 25) por ahora --
el clasificador de la primera entrega es nacional (pivote "Opcion C"), no
depende de esto. Si la vía departamental se activa como segundo
clasificador queda condicionado al reconteo del punto H de
docs/contexto/02-decisiones-abiertas.md tras rescatar los boletines con
tabla-imagen (tarjeta 26) -- no adelantado aqui.

Requiere migracion 0005 aplicada (ADR 0007, estado 'sin_texto_extraible').

Limitacion deliberada de esta primera version: solo se registra en la
bitacora el archivo VIGENTE de cada (anio, semana_archivo) -- las versiones
descartadas por resolver_versiones() (ej. _v1 cuando existe _v2) no generan
fila propia todavia, aunque el ADR 0004 las contempla como parte de la
auditoria. Ampliar esto es trabajo futuro, no bloquea la tarjeta 22.

Uso:
    python3 parser.py                  # corpus completo (264 PDF)
    python3 parser.py --limite 20      # solo los primeros N PDF por anio (pruebas)
    python3 parser.py --dry-run        # corre extraccion+desacumulacion, no escribe a Postgres
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from corrida_distribucion import (
    DEPARTAMENTOS,
    PuntoSemanal,
    ResultadoBoletin,
    descubrir_archivos,
    paso1_extraer,
    paso2_desacumular,
    resolver_versiones,
)
from db import get_connection
from psycopg2.extras import execute_values

INDEX_URL_TEMPLATE = "https://www.salud.gob.sv/boletines-epidemiologicos-{anio}/"

# Colapsa los estados de diagnostico de la corrida exploratoria a los 6
# valores que admite boletines_procesados.estado (ADR 0004 + ADR 0007).
# ausencia_esperada_vacacion/_multisemana -> ausencia_esperada (la
# distincion vive en `notas`, no amerita una rama nueva del CHECK).
# sin_tabla_no_vacacional -> revision_manual (anomalia real, alguien debe
# mirarla a mano -- misma semantica que ya cubre ese valor).
MAPA_ESTADO = {
    "ok": "ok",
    "revision_manual": "revision_manual",
    "ausencia_esperada_vacacion": "ausencia_esperada",
    "ausencia_esperada_multisemana": "ausencia_esperada",
    "sin_texto_extraible": "sin_texto_extraible",
    "sin_tabla_no_vacacional": "revision_manual",
    "error_extraccion": "error",
    # Identidad: REVISIONES_MANUALES (abajo) escribe directamente un estado ya
    # final de boletines_procesados sobre r.estado, no un estado crudo de
    # paso1_extraer -- necesita mapear a si mismo aqui.
    "ausencia_esperada": "ausencia_esperada",
}

# Overrides de revision manual real (tarjeta 26, 2026-08-16) sobre boletines
# que la clasificacion automatica de corrida_distribucion.py no puede resolver
# por si sola -- cada uno requirio evidencia externa (OCR exhaustivo pagina
# por pagina, o comparar contra las tablas departamentales de OTRAS
# enfermedades del mismo boletin) que el heuristico de paso1 no ejecuta.
# No es una lista para silenciar advertencias: cada entrada documenta la
# evidencia puntual que la respalda. Se aplica sobre el resultado de paso1,
# antes de paso2_desacumular, para que "ok" (cuando corresponda) SI alimente
# la desacumulacion.
REVISIONES_MANUALES: dict[str, tuple[str, str]] = {
    # OCR exhaustivo (todas las paginas, pdfplumber page.to_image + pytesseract
    # lang='spa') confirma 0 ocurrencias de tabla departamental de dengue, ni en
    # texto ni en imagen -- el boletin reporta dengue solo a nivel nacional y por
    # grupo de edad esa semana, nunca publico desglose departamental. No es una
    # tabla-imagen sin OCR (hipotesis original del ADR 0007): es ausencia real de
    # contenido, igual de valida que cualquier otra semana sin tabla.
    "Boletin_epidemiologico_SE232019.pdf": (
        "ausencia_esperada",
        "OCR exhaustivo (todas las paginas) confirma 0 tablas departamentales de "
        "dengue en texto o imagen -- revision tarjeta 26 (2026-08-16)",
    ),
    "Boletin_epidemiologico_SE322019.pdf": (
        "ausencia_esperada",
        "OCR exhaustivo (todas las paginas) confirma 0 tablas departamentales de "
        "dengue en texto o imagen -- revision tarjeta 26 (2026-08-16)",
    ),
    "Boletin_epidemiologico_SE352019_v2.pdf": (
        "ausencia_esperada",
        "OCR exhaustivo (todas las paginas) confirma 0 tablas departamentales de "
        "dengue en texto o imagen -- revision tarjeta 26 (2026-08-16)",
    ),
    # Boletin abierto sin error; el documento SI trae tablas departamentales esa
    # semana, solo que de otras enfermedades (parotiditis/fiebre tifoidea/
    # chikungunya/zika/IRA/neumonias/EDAS segun el boletin) -- dengue
    # especificamente no publico desglose departamental esa semana. Confirmado
    # revisando cada tabla con nombres de departamento como ancla, no solo
    # buscando "dengue".
    "Boletin_epidemiologico_SE182023.pdf": (
        "ausencia_esperada",
        "el boletin SI tiene tablas departamentales esa semana (zika/chikungunya, "
        "IRA, neumonias, EDAS) pero dengue no publico desglose departamental -- "
        "revision tarjeta 26 (2026-08-16)",
    ),
    "Boletin_epidemiologico_SE282019_v2.pdf": (
        "ausencia_esperada",
        "el boletin SI tiene tablas departamentales esa semana (parotiditis, "
        "fiebre tifoidea, chikungunya) pero dengue no publico desglose "
        "departamental -- revision tarjeta 26 (2026-08-16)",
    ),
    "Boletin_epidemiologico_SE292019_v2.pdf": (
        "ausencia_esperada",
        "el boletin SI tiene tablas departamentales esa semana (parotiditis, "
        "fiebre tifoidea, chikungunya) pero dengue no publico desglose "
        "departamental -- revision tarjeta 26 (2026-08-16)",
    ),
    # Discrepancia real de MINSAL, no de extraccion: probable cuadra exacto
    # (suma14+otros=386=impreso); confirmado difiere en exactamente 1 caso
    # (suma14+otros=88, impreso=89). El desglose departamental esta completo
    # (14/14) y es internamente consistente -- se acepta con
    # validacion_cuadra=false documentado en notas, en vez de descartar 14 filas
    # de dato real y verificado por 1 caso de diferencia en un total que ni
    # siquiera es el dato que se ingesta (casos_epidemiologicos guarda el
    # desglose por departamento, no el total nacional impreso).
    "Boletin_epidemiologico_SE302019_v2.pdf": (
        "ok",
        "confirmado difiere en 1 caso del total impreso (suma14+otros=88, "
        "impreso=89); probable cuadra exacto (386=386). Desglose departamental "
        "completo y consistente, aceptado tras revision manual -- tarjeta 26 "
        "(2026-08-16)",
    ),
}


def aplicar_revisiones_manuales(resultados: list[ResultadoBoletin]) -> None:
    """Aplica REVISIONES_MANUALES in-place, antes de paso2_desacumular."""
    for r in resultados:
        override = REVISIONES_MANUALES.get(r.archivo)
        if override is None:
            continue
        nuevo_estado, nota = override
        r.estado = nuevo_estado
        r.nota = f"{r.nota} | {nota}" if r.nota else nota


def _semana_archivo_db(semana_archivo: str | None) -> int | None:
    """boletines_procesados.semana_archivo es SMALLINT, nullable (ADR 0004).
    Un boletin de semanas combinadas ("1-2") no tiene una semana unica que
    registrar -- se deja NULL en vez de fabricar un valor, tal como fija el
    ADR."""
    if semana_archivo is None or "-" in semana_archivo:
        return None
    return int(semana_archivo)


def _validacion_cuadra(r: ResultadoBoletin) -> bool | None:
    if r.validacion_tabla is True or r.validacion_nacional is True:
        return True
    if r.validacion_tabla is False and r.validacion_nacional is False:
        return False
    return None


def cargar_bitacora(resultados: list[ResultadoBoletin]) -> dict[str, int]:
    """Upsert de un boletin por fila (nombre_archivo UNIQUE, ADR 0004).
    Devuelve {nombre_archivo: id} para trazar casos_epidemiologicos.boletin_id."""
    conn = get_connection()
    archivo_a_id: dict[str, int] = {}
    try:
        with conn.cursor() as cur:
            for r in resultados:
                estado_db = MAPA_ESTADO[r.estado]
                url_origen = INDEX_URL_TEMPLATE.format(anio=r.anio)
                suma_prob = r.suma14[0] if len(r.suma14) > 0 else None
                suma_conf = r.suma14[1] if len(r.suma14) > 1 else None
                total_prob = r.total_impreso[0] if len(r.total_impreso) > 0 else None
                total_conf = r.total_impreso[1] if len(r.total_impreso) > 1 else None

                cur.execute(
                    """
                    INSERT INTO boletines_procesados
                        (nombre_archivo, version, anio, semana_archivo, url_origen,
                         familia_esquema, suma_departamental_probable, suma_departamental_confirmado,
                         total_nacional_publicado_probable, total_nacional_publicado_confirmado,
                         validacion_cuadra, estado, notas)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (nombre_archivo) DO UPDATE SET
                        version = EXCLUDED.version,
                        semana_archivo = EXCLUDED.semana_archivo,
                        familia_esquema = EXCLUDED.familia_esquema,
                        suma_departamental_probable = EXCLUDED.suma_departamental_probable,
                        suma_departamental_confirmado = EXCLUDED.suma_departamental_confirmado,
                        total_nacional_publicado_probable = EXCLUDED.total_nacional_publicado_probable,
                        total_nacional_publicado_confirmado = EXCLUDED.total_nacional_publicado_confirmado,
                        validacion_cuadra = EXCLUDED.validacion_cuadra,
                        estado = EXCLUDED.estado,
                        notas = EXCLUDED.notas,
                        fecha_procesado = now()
                    RETURNING id
                    """,
                    (
                        r.archivo, r.version, r.anio, _semana_archivo_db(r.semana_archivo), url_origen,
                        r.familia, suma_prob, suma_conf, total_prob, total_conf,
                        _validacion_cuadra(r), estado_db, r.nota,
                    ),
                )
                archivo_a_id[r.archivo] = cur.fetchone()[0]
        conn.commit()
    finally:
        conn.close()
    return archivo_a_id


def construir_origen(resultados: list[ResultadoBoletin], serie: str) -> dict[tuple[int, str, int], str]:
    """Para cada (anio, departamento, semana_de_corte) que sale 'ok', registra
    que archivo la reporto -- espeja intencionalmente el mismo orden de
    iteracion y la misma regla "ultimo gana" que
    corrida_distribucion._serie_por_depto_anio, para que la traza de
    boletin_id apunte siempre al archivo que de verdad aporto el valor que
    paso2_desacumular uso en el calculo (no se reimplementa la desacumulacion
    en si, solo el mapeo de procedencia, que la corrida exploratoria no
    necesitaba por no escribir a una base relacional con FK)."""
    idx = 0 if serie == "probable" else 1
    semana_attr = "semana_probable" if serie == "probable" else "semana_confirmado"

    origen: dict[tuple[int, str, int], str] = {}
    for r in resultados:
        if r.estado != "ok":
            continue
        semana = getattr(r, semana_attr)
        if semana is None:
            continue
        for fila in r.filas:
            if len(fila.valores) <= idx:
                continue
            origen[(r.anio, fila.departamento, semana)] = r.archivo
    return origen


def cargar_casos(
    desacumulado: dict[str, list[PuntoSemanal]],
    resultados: list[ResultadoBoletin],
    archivo_a_id: dict[str, int],
) -> tuple[int, dict[str, int]]:
    conn = get_connection()
    contadores = {"huecos_omitidos": 0, "correcciones_omitidas": 0, "insertadas": 0}
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, nombre FROM regiones WHERE nivel_admin = 1")
            region_id_por_nombre = {nombre: rid for rid, nombre in cur.fetchall()}
            if len(region_id_por_nombre) != len(DEPARTAMENTOS):
                faltan = set(DEPARTAMENTOS) - set(region_id_por_nombre)
                raise RuntimeError(
                    f"regiones (nivel_admin=1) no tiene los 14 departamentos esperados -- "
                    f"faltan: {faltan}. Revisar acentos/nombres contra db/migrations/0001_init_schema.sql."
                )

            cur.execute("SELECT id FROM tipos_evento WHERE codigo = 'dengue'")
            tipo_evento_id = cur.fetchone()[0]

            cur.execute("SELECT id FROM fuentes_datos WHERE codigo = 'minsal_pdf'")
            fuente_id = cur.fetchone()[0]

            valores = []
            for serie in ("probable", "confirmado"):
                origen = construir_origen(resultados, serie)
                for p in desacumulado[serie]:
                    if p.valor is None:
                        if "correccion retroactiva" in p.nota:
                            contadores["correcciones_omitidas"] += 1
                        else:
                            contadores["huecos_omitidos"] += 1
                        continue
                    region_id = region_id_por_nombre.get(p.departamento)
                    if region_id is None:
                        continue
                    archivo = origen.get((p.anio, p.departamento, p.semana))
                    boletin_id = archivo_a_id.get(archivo) if archivo else None
                    valores.append((
                        region_id, tipo_evento_id, p.anio, p.semana, serie,
                        round(p.valor), fuente_id, boletin_id,
                    ))

            if valores:
                execute_values(
                    cur,
                    """
                    INSERT INTO casos_epidemiologicos
                        (region_id, tipo_evento_id, anio, semana_epi, clasificacion, conteo, fuente_id, boletin_id)
                    VALUES %s
                    ON CONFLICT (region_id, tipo_evento_id, anio, semana_epi, clasificacion, fuente_id)
                    DO UPDATE SET conteo = EXCLUDED.conteo, boletin_id = EXCLUDED.boletin_id, fecha_ingesta = now()
                    """,
                    valores,
                    page_size=len(valores),
                )
                # Mismo cuidado que cargar_opendengue.py: sin page_size=len(valores),
                # cur.rowcount solo refleja la ultima pagina interna de execute_values.
                contadores["insertadas"] = len(valores)
        conn.commit()
    finally:
        conn.close()
    return contadores["insertadas"], contadores


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limite", type=int, default=None, help="limitar a los primeros N PDF por anio (pruebas rapidas)")
    ap.add_argument("--dry-run", action="store_true", help="correr extraccion+desacumulacion sin escribir a Postgres")
    args = ap.parse_args()

    resultados = paso1_extraer(limite=args.limite)
    aplicar_revisiones_manuales(resultados)
    desacumulado = paso2_desacumular(resultados)

    resumen_estados = Counter(r.estado for r in resultados)
    print("\nResumen de estados (mapeados a boletines_procesados.estado):")
    for estado_exploratorio, n in resumen_estados.most_common():
        print(f"  {estado_exploratorio} -> {MAPA_ESTADO[estado_exploratorio]}: {n}")

    if args.dry_run:
        print("\n--dry-run: no se escribió nada a Postgres.")
        return

    archivo_a_id = cargar_bitacora(resultados)
    print(f"\nOK: {len(archivo_a_id)} filas insertadas/actualizadas en boletines_procesados.")

    insertadas, contadores = cargar_casos(desacumulado, resultados, archivo_a_id)
    print(f"OK: {insertadas} filas insertadas/actualizadas en casos_epidemiologicos "
          f"(fuente=minsal_pdf, series probable+confirmado, desacumuladas).")
    print(f"  Huecos entre cortes omitidos (sin dato, no repartidos): {contadores['huecos_omitidos']}")
    print(f"  Correcciones retroactivas negativas excluidas de la serie: {contadores['correcciones_omitidas']}")


if __name__ == "__main__":
    main()
