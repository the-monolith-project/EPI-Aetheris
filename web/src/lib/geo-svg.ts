// Proyecta la geometría de los departamentos (GeoJSON) a trazados SVG. Usa una
// proyección equirectangular con el ancho corregido por la latitud media, que
// a la escala de un país pequeño se ve igual que cualquier otra. Sirve a la
// ficha de idoneidad, que dibuja un solo departamento relleno sobre el resto
// del país en contorno.

type Anillo = number[][];

interface GeometriaDepartamento {
  type: 'Polygon' | 'MultiPolygon';
  coordinates: Anillo[] | Anillo[][];
}

export interface GeoDepartamentos {
  features: {
    properties: { codigo: string };
    geometry: GeometriaDepartamento;
  }[];
}

export interface DepartamentoSvg {
  codigo: string;
  d: string;
}

export interface MapaSvg {
  ancho: number;
  alto: number;
  departamentos: DepartamentoSvg[];
}

function anillos(g: GeometriaDepartamento): Anillo[] {
  return g.type === 'Polygon'
    ? (g.coordinates as Anillo[])
    : (g.coordinates as Anillo[][]).flat();
}

/**
 * `ancho` fija el ancho del dibujo; el alto sale de la proporción real del
 * país. `tolerancia` descarta vértices a menos de esos píxeles del anterior.
 */
export function proyectarDepartamentos(
  geo: GeoDepartamentos,
  ancho: number,
  margen = 6,
  tolerancia = 0.5,
): MapaSvg {
  let lonMin = Infinity;
  let lonMax = -Infinity;
  let latMin = Infinity;
  let latMax = -Infinity;
  for (const f of geo.features) {
    for (const anillo of anillos(f.geometry)) {
      for (const [lon, lat] of anillo) {
        lonMin = Math.min(lonMin, lon);
        lonMax = Math.max(lonMax, lon);
        latMin = Math.min(latMin, lat);
        latMax = Math.max(latMax, lat);
      }
    }
  }
  const factor = Math.cos((((latMin + latMax) / 2) * Math.PI) / 180);
  const anchoGeo = (lonMax - lonMin) * factor;
  const altoGeo = latMax - latMin;
  const escala = (ancho - 2 * margen) / anchoGeo;
  const alto = Math.round(altoGeo * escala + 2 * margen);

  const x = (lon: number) => margen + (lon - lonMin) * factor * escala;
  const y = (lat: number) => margen + (latMax - lat) * escala;
  const redondear = (n: number) => Math.round(n * 10) / 10;

  const departamentos = geo.features.map((f) => {
    let d = '';
    for (const anillo of anillos(f.geometry)) {
      let ultimo: [number, number] | null = null;
      let trazo = '';
      for (const [lon, lat] of anillo) {
        const px = x(lon);
        const py = y(lat);
        if (ultimo && Math.hypot(px - ultimo[0], py - ultimo[1]) < tolerancia) {
          continue;
        }
        trazo += `${trazo === '' ? 'M' : 'L'}${redondear(px)} ${redondear(py)}`;
        ultimo = [px, py];
      }
      if (trazo !== '') d += `${trazo}Z`;
    }
    return { codigo: f.properties.codigo, d };
  });
  return { ancho, alto, departamentos };
}
