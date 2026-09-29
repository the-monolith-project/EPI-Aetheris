export interface EntradaGlosario {
  clave: string;
  termino: string;
  definicion: string;
  /** Ancla de la Biblioteca donde se explica con detalle. */
  enlace: string;
}

const FUNCIONES = '/biblioteca/03-funciones';
const FUENTES = '/biblioteca/04-fuentes-de-datos';
const SENSIBILIDAD = '/biblioteca/05-sensibilidad-y-honestidad';

export const GLOSARIO: EntradaGlosario[] = [
  {
    clave: 'iv',
    termino: 'Iv (idoneidad biofísica)',
    definicion:
      'Índice de 0 a 1 que resume qué tan favorables son la temperatura, la lluvia y la humedad de una semana para el vector. Describe el clima, no casos.',
    enlace: `${FUNCIONES}#m1-idoneidad-biofísica-iv`,
  },
  {
    clave: 'anomalia',
    termino: 'Anomalía (σ)',
    definicion:
      'Cuántas desviaciones estándar se aparta el Iv de una semana de lo habitual en ese departamento y esa semana del año.',
    enlace: `${FUNCIONES}#m2-anomalía-climática-continua`,
  },
  {
    clave: 'percentil-presion',
    termino: 'Percentil de presión',
    definicion:
      'Posición de los casos de una semana entre los de otros años en el mismo departamento, de 0 a 100. No compara departamentos entre sí.',
    enlace: `${FUNCIONES}#m3-presión-epidemiológica-relativa`,
  },
  {
    clave: 'canal-endemico',
    termino: 'Canal endémico',
    definicion:
      'Los cortes P50 y P75 de la historia del departamento dibujados como bandas, con los casos observados encima.',
    enlace: `${FUNCIONES}#canal-endémico`,
  },
  {
    clave: 'probable',
    termino: 'Probable',
    definicion:
      'Caso clasificado como probable en los boletines de MINSAL. Se muestra por separado del confirmado y nunca se suma con él.',
    enlace: `${FUENTES}#boletines-epidemiológicos-de-minsal`,
  },
  {
    clave: 'confirmado',
    termino: 'Confirmado',
    definicion:
      'Caso con confirmación de laboratorio según los boletines de MINSAL. Es una serie distinta de la de probables.',
    enlace: `${FUENTES}#boletines-epidemiológicos-de-minsal`,
  },
  {
    clave: 'sospechoso',
    termino: 'Sospechoso',
    definicion:
      'Nombre que usa el tablero de MINSAL para los casos notificados desde 2025. Su serie llega ya suavizada por la fuente.',
    enlace: `${FUENTES}#tablero-de-vigilancia-de-minsal`,
  },
  {
    clave: 'semana-epidemiologica',
    termino: 'Semana epidemiológica (SE)',
    definicion:
      'Semana de domingo a sábado numerada dentro del año para comparar la vigilancia entre años. Algunos años tienen 53.',
    enlace: `${FUENTES}#opendengue`,
  },
  {
    clave: 'bandas',
    termino: 'Banda del 50 % y del 95 %',
    definicion:
      'Rango en el que caería la cifra prevista con esa probabilidad. La banda del 95 % es más ancha que la del 50 %.',
    enlace: `${SENSIBILIDAD}#predicción-de-casos-a-corto-plazo`,
  },
  {
    clave: 'conteo-notificado',
    termino: 'Conteo notificado',
    definicion:
      'Casos que las unidades de salud reportaron a MINSAL. Depende de cuánto se notifica, no solo de cuánto se enferma.',
    enlace: `${FUNCIONES}#observatorio-respiratorio`,
  },
  {
    clave: 'positividad',
    termino: 'Positividad',
    definicion:
      'Proporción de muestras de laboratorio con detección de un virus en una semana.',
    enlace: `${FUNCIONES}#observatorio-respiratorio`,
  },
  {
    clave: 'integridad',
    termino: 'Integridad de la vigilancia',
    definicion:
      'Qué tan completa y puntual es la información publicada de un departamento. Indica cuánto confiar en la cifra, no la cantidad de casos.',
    enlace: `${FUNCIONES}#m4-integridad-de-la-vigilancia`,
  },
];

export function entradaGlosario(clave: string): EntradaGlosario | undefined {
  return GLOSARIO.find((e) => e.clave === clave);
}
