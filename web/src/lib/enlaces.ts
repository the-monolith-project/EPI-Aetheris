/** Aviso de sensibilidad de la Biblioteca (ADR 0016, docs/biblioteca/05-sensibilidad-y-honestidad.md).
 *  Reúne los límites del sistema; enlazar aquí en vez de repetir el deslinde en cada vista. */
export const RUTA_SENSIBILIDAD = '/biblioteca/05-sensibilidad-y-honestidad';

/** Sección del tablero de MINSAL en la página de fuentes: cobertura, forma
 *  promediada de la serie y semanas sin publicar (ADR 0021). */
export const RUTA_FUENTE_TABLERO =
  '/biblioteca/04-fuentes-de-datos#tablero-de-vigilancia-de-minsal';

/** Fuentes de datos de la Biblioteca: cobertura, ventanas por serie y la
 *  exclusión de 2020 en la comparación departamental. */
export const RUTA_FUENTES = '/biblioteca/04-fuentes-de-datos';

/** Predicción de casos a corto plazo. Vive solo en su página, no dentro de la
 *  vista de análisis de /dengue. */
export const RUTA_PREDICCION = '/prediccion';

/** Clima y dengue: aporte del clima al pronóstico por año y comparación de El
 *  Salvador con otros 17 países (ADR 0023 del monorepo). */
export const RUTA_CLIMA = '/analisis/clima';

/** Documento de la Biblioteca con el método, los resultados y los datos que
 *  faltan para avanzar el análisis de clima y dengue. */
export const RUTA_CLIMA_DOC = '/biblioteca/07-clima-y-dengue';
