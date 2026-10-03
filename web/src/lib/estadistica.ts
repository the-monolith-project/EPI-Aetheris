// Estadística básica que comparten las fichas de M2 y M3. Reproduce las
// funciones del backend (percentil con interpolación lineal, desviación
// estándar muestral y el redondeo de Python) para que la ficha muestre las
// mismas cifras que la API. Sin dependencias: lo importan anomalia.ts y
// presion.ts con la extensión .ts, como pide la ejecución de las pruebas.

/**
 * Percentil `p` (de 0 a 100) con interpolación lineal entre los dos valores
 * vecinos, el mismo criterio que el percentil por defecto de NumPy. Lanza si
 * no hay valores.
 */
export function percentil(valores: readonly number[], p: number): number {
  if (valores.length === 0) {
    throw new Error('percentil: el conjunto está vacío');
  }
  const ordenados = [...valores].sort((a, b) => a - b);
  const posicion = ((ordenados.length - 1) * p) / 100;
  const abajo = Math.floor(posicion);
  const arriba = Math.min(ordenados.length - 1, abajo + 1);
  const fraccion = posicion - abajo;
  return ordenados[abajo] + (ordenados[arriba] - ordenados[abajo]) * fraccion;
}

export function media(valores: readonly number[]): number {
  return valores.reduce((a, b) => a + b, 0) / valores.length;
}

/** Desviación estándar muestral (divide entre n − 1). Null con menos de dos valores. */
export function desviacionMuestral(valores: readonly number[]): number | null {
  if (valores.length < 2) return null;
  const m = media(valores);
  const suma = valores.reduce((acc, v) => acc + (v - m) ** 2, 0);
  return Math.sqrt(suma / (valores.length - 1));
}

/**
 * Redondeo a `decimales` como `round` de Python: sobre el valor exacto del
 * número y, en un empate exacto, hacia la cifra par (12,25 → 12,2). El
 * Math.round de JavaScript sube siempre en el empate y da 12,3.
 */
export function redondear(valor: number, decimales: number): number {
  if (!Number.isFinite(valor)) return valor;
  // toFixed trabaja con el valor exacto del double: con 30 cifras de más se
  // ve si lo que queda tras la cifra pedida es exactamente un medio.
  const exacto = Math.abs(valor).toFixed(decimales + 30);
  const corte = exacto.length - 30;
  const resto = exacto.slice(corte);
  const base = Number(exacto.slice(0, corte));
  const unidad = 10 ** -decimales;
  let resultado = base;
  if (resto[0] > '5' || (resto[0] === '5' && /[1-9]/.test(resto.slice(1)))) {
    resultado = base + unidad;
  } else if (resto[0] === '5') {
    const ultima = Number(
      exacto[corte - 1] === '.' ? exacto[corte - 2] : exacto[corte - 1],
    );
    if (ultima % 2 === 1) resultado = base + unidad;
  }
  resultado = Number(resultado.toFixed(decimales));
  return valor < 0 ? -resultado : resultado;
}
