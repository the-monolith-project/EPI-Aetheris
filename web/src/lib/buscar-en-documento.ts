// Búsqueda de palabras dentro de un documento: compara sin distinguir
// mayúsculas ni tildes («presion» encuentra «Presión»). `plegar` conserva la
// longitud del texto, así que los índices de la versión plegada sirven tal
// cual sobre el texto original para resaltar la coincidencia.

/** Minúsculas y sin tildes, carácter por carácter (misma longitud que el original). */
export function plegar(texto: string): string {
  let resultado = '';
  for (let i = 0; i < texto.length; i++) {
    const caracter = texto[i] as string;
    const base = caracter.normalize('NFD')[0] ?? caracter;
    resultado += base.toLowerCase()[0] ?? base;
  }
  return resultado;
}

/** Posiciones de inicio de cada coincidencia (sin solaparse) de `consulta` en `texto`. */
export function encontrar(texto: string, consulta: string): number[] {
  const buscada = plegar(consulta.trim());
  if (!buscada) return [];
  const pajar = plegar(texto);
  const posiciones: number[] = [];
  let desde = 0;
  for (;;) {
    const i = pajar.indexOf(buscada, desde);
    if (i === -1) break;
    posiciones.push(i);
    desde = i + buscada.length;
  }
  return posiciones;
}
