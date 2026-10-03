// Comportamiento del laboratorio de la ficha de presión epidemiológica
// (LaboratorioPresion.astro). Cada cambio vuelve a calcular y a dibujar al
// instante; «Calcular paso a paso» recorre el método en orden (conjunto,
// ordenar, percentil, cortes, color) sobre un cálculo ya hecho. Con las
// animaciones apagadas se salta y se muestra el resultado.

import {
  esNoDisponible,
  renderErrorFuente,
  renderSinDato,
} from '../components/estado-async';
import { obtenerSeriePresion } from './analisis-api';
import { animacionesActivas } from './animaciones';
import { colorCategoriaPresion } from './colores';
import { obtenerDepartamento } from './departamentos';
import { formatearNumero } from './idoneidad';
import {
  calcularLaboratorio,
  rectaPresion,
  tiraPresion,
} from './laboratorio-presion';
import {
  EJEMPLO_PRESION,
  PRESETS_PRESION,
  type PresetPresion,
} from './presion';
import {
  MS_ETAPA,
  activarEtapa,
  animar,
  cerrarEtapa,
  esperar,
  limpiarEtapas,
  prepararEtapas,
} from './recorrido';
import { ANIOS_ANALISIS_DENGUE } from './tipos-analisis';

const f1 = (n: number | null) =>
  n === null ? 'sin dato' : formatearNumero(n, 1);

export function iniciarLaboratorioPresion(raiz: HTMLElement): void {
  const q = <T extends Element>(selector: string): T => {
    const elemento = raiz.querySelector<T>(selector);
    if (!elemento) throw new Error(`Laboratorio de M3: falta ${selector}`);
    return elemento;
  };

  const controles = q<HTMLFieldSetElement>('[data-lab-controles]');
  const selectorDepto = q<HTMLSelectElement>('[data-lab-depto]');
  const selectorSerie = q<HTMLSelectElement>('[data-lab-serie]');
  const entradaCasos = q<HTMLInputElement>('[data-lab-casos]');
  const salidaCasos = q<HTMLOutputElement>('[data-lab-salida-casos]');
  const botonCalcular = q<HTMLButtonElement>('[data-lab-calcular]');
  const estado = q<HTMLElement>('[data-lab-estado]');
  const tira = q<HTMLElement>('[data-lab-tira]');
  const recta = q<HTMLElement>('[data-lab-recta]');
  const textoPercentil = q<HTMLElement>('[data-lab-percentil]');
  const textoCortes = q<HTMLElement>('[data-lab-cortes]');
  const textoCategoria = q<HTMLElement>('[data-lab-categoria]');
  const cifra = q<HTMLElement>('[data-lab-cifra]');
  const frase = q<HTMLElement>('[data-lab-frase]');
  const real = q<HTMLElement>('[data-lab-real]');
  const mapa = q<SVGElement>('[data-mapa-ficha-svg]');
  const etapas = ['pool', 'ordenar', 'percentil', 'cortes', 'color'].map(
    (nombre) => q<HTMLElement>(`[data-lab-etapa="${nombre}"]`),
  );

  let codigo = raiz.dataset.codigoInicial ?? 'SV-SS';
  let ventanas: PresetPresion['ventanas'] = EJEMPLO_PRESION.ventanas.map(
    (v) => ({ anio: v.anio, casos: [...v.casos] }),
  );
  let enSecuencia = false;
  let temporizadorAnuncio: ReturnType<typeof setTimeout> | undefined;

  const serie = () =>
    selectorSerie.value === 'confirmado' ? 'confirmado' : 'probable';
  const leer = () => calcularLaboratorio(ventanas, Number(entradaCasos.value));
  const nombreDepto = () => obtenerDepartamento(codigo)?.nombre ?? codigo;

  function anunciar(mensaje: string, retraso = 0): void {
    clearTimeout(temporizadorAnuncio);
    temporizadorAnuncio = setTimeout(() => {
      estado.textContent = mensaje;
    }, retraso);
  }

  function pintarTira(c: ReturnType<typeof leer>, conCortes = true): void {
    const t = tiraPresion(ventanas, c, conCortes);
    tira.innerHTML = t.svg;
    tira.setAttribute('aria-label', t.etiqueta);
  }

  function pintarRecta(c: ReturnType<typeof leer>, visible = true): void {
    recta.innerHTML = visible ? rectaPresion(c) : '';
    const ordenados = [...c.pool].sort((a, b) => a - b);
    recta.setAttribute(
      'aria-label',
      ordenados.length > 0
        ? `Conjunto ordenado: ${ordenados.join(', ')}. Cifra observada: ${c.observado}.`
        : 'El conjunto está vacío.',
    );
  }

  function pintarMapa(categoria: 'baja' | 'media' | 'alta' | null): void {
    mapa.querySelectorAll<SVGPathElement>('[data-codigo]').forEach((ruta) => {
      const activo = ruta.dataset.codigo === codigo;
      ruta.classList.toggle('seleccionado', activo);
      if (activo && categoria !== null) {
        ruta.style.setProperty('--relleno', colorCategoriaPresion(categoria));
      } else ruta.style.removeProperty('--relleno');
    });
    mapa.setAttribute(
      'aria-label',
      categoria === null
        ? `Mapa de El Salvador con ${nombreDepto()} sin categoría`
        : `Mapa de El Salvador con ${nombreDepto()} pintado en la categoría ${categoria}`,
    );
  }

  function textoResultado(c: ReturnType<typeof leer>): string {
    const r = c.resultado;
    if (r.percentil === null) {
      return `Solo ${r.anios_baseline} años de referencia tienen casos en la ventana y hacen falta 3: el percentil queda vacío.`;
    }
    return `${c.observado} casos ${serie() === 'probable' ? 'probables' : 'confirmados'} caen en el percentil ${f1(r.percentil)} de su historia: presión ${r.categoria}.`;
  }

  function actualizar(): void {
    const c = leer();
    const r = c.resultado;
    salidaCasos.textContent = String(c.observado);
    entradaCasos.setAttribute('aria-valuetext', `${c.observado} casos`);
    pintarTira(c);
    pintarRecta(c);
    textoPercentil.textContent = f1(r.percentil);
    cifra.textContent = f1(r.percentil);
    textoCortes.textContent =
      r.p50_baseline === null
        ? 'sin dato'
        : `${f1(r.p50_baseline)} y ${f1(r.p75_baseline)}`;
    textoCategoria.textContent = r.categoria ?? 'sin dato';
    frase.textContent = textoResultado(c);
    pintarMapa(r.categoria);
  }

  const resumen = () => `${nombreDepto()}: ${textoResultado(leer())}`;

  // ---- Recorrido paso a paso -------------------------------------------

  async function calcular(): Promise<void> {
    if (enSecuencia) return;
    if (!animacionesActivas()) {
      actualizar();
      anunciar(resumen());
      return;
    }
    enSecuencia = true;
    controles.disabled = true;
    botonCalcular.setAttribute('aria-busy', 'true');
    const c = leer();
    const r = c.resultado;
    prepararEtapas(etapas);
    pintarTira(c, false);
    pintarRecta(c, false);
    for (const t of [textoPercentil, textoCortes, textoCategoria, cifra]) {
      t.textContent = '·';
    }
    frase.textContent = '';
    pintarMapa(null);

    const sinBase = r.percentil === null;
    const textos = [
      `Paso 1 de 5: la ventana de los otros años junta ${c.pool.length} valores de ${r.anios_baseline} años.`,
      sinBase
        ? 'Paso 2 de 5: con menos de 3 años con dato no se ordena nada.'
        : `Paso 2 de 5: se ordenan los ${c.pool.length} valores.`,
      sinBase
        ? 'Paso 3 de 5: el percentil queda vacío.'
        : `Paso 3 de 5: ${c.observado} casos caen en el percentil ${f1(r.percentil)}.`,
      sinBase
        ? 'Paso 4 de 5: sin línea base no hay cortes.'
        : `Paso 4 de 5: P50 ${f1(r.p50_baseline)} y P75 ${f1(r.p75_baseline)}: presión ${r.categoria}.`,
      sinBase
        ? `Paso 5 de 5: ${nombreDepto()} queda sin color.`
        : `Paso 5 de 5: la categoría ${r.categoria} pinta ${nombreDepto()}.`,
    ];

    for (let i = 0; i < etapas.length; i += 1) {
      activarEtapa(etapas[i]);
      anunciar(textos[i]);
      if (i === 1) {
        pintarRecta(c);
        await esperar(MS_ETAPA);
      } else if (i === 2) {
        const destino = r.percentil;
        if (destino !== null) {
          await animar(MS_ETAPA, (p) => {
            textoPercentil.textContent = f1(destino * p);
          });
        }
        textoPercentil.textContent = f1(r.percentil);
      } else if (i === 3) {
        pintarTira(c);
        textoCortes.textContent =
          r.p50_baseline === null
            ? 'sin dato'
            : `${f1(r.p50_baseline)} y ${f1(r.p75_baseline)}`;
        textoCategoria.textContent = r.categoria ?? 'sin dato';
        await esperar(MS_ETAPA);
      } else if (i === 4) {
        pintarMapa(r.categoria);
        cifra.textContent = f1(r.percentil);
        await esperar(MS_ETAPA);
      } else {
        await esperar(MS_ETAPA);
      }
      cerrarEtapa(etapas[i]);
    }

    limpiarEtapas(etapas);
    actualizar();
    anunciar(resumen());
    controles.disabled = false;
    botonCalcular.removeAttribute('aria-busy');
    botonCalcular.focus();
    enSecuencia = false;
  }

  // ---- Presión que calcula el sistema ----------------------------------

  let peticion = 0;

  async function cargarReal(): Promise<void> {
    const actual = (peticion += 1);
    const nombre = nombreDepto();
    const s = serie();
    real.setAttribute('aria-busy', 'true');
    const p = document.createElement('p');
    p.className = 'lab-cargando';
    p.textContent = `Consultando la presión de ${nombre}…`;
    real.replaceChildren(p);
    try {
      const anios = [...ANIOS_ANALISIS_DENGUE].reverse().slice(0, 2);
      let encontrado: {
        anio: number;
        semana: number;
        percentil: number;
        categoria: string | null;
        casos: number | null;
        p50: number | null;
        p75: number | null;
      } | null = null;
      for (const anio of anios) {
        const datos = await obtenerSeriePresion(codigo, anio);
        if (actual !== peticion) return;
        if (esNoDisponible(datos)) continue;
        const ultima = [...datos.semanas]
          .reverse()
          .find((x) => x[s]?.percentil !== null && x[s] !== undefined);
        if (ultima && ultima[s].percentil !== null) {
          encontrado = {
            anio,
            semana: ultima.semana_epi,
            percentil: ultima[s].percentil,
            categoria: ultima[s].categoria,
            casos: ultima[s].casos_observados,
            p50: ultima[s].p50_baseline,
            p75: ultima[s].p75_baseline,
          };
          break;
        }
      }
      if (actual !== peticion) return;
      if (!encontrado) {
        renderSinDato(
          real,
          `El sistema no tiene presión ${s} calculada para ${nombre}.`,
        );
        return;
      }
      real.removeAttribute('aria-busy');
      // Nodos de texto y no innerHTML: el nombre sale de la lista de
      // departamentos o del valor del selector (CodeQL).
      const fuerte = document.createElement('strong');
      fuerte.textContent = `percentil ${f1(encontrado.percentil)}`;
      const texto = document.createElement('p');
      texto.append(
        `Presión ${s} calculada por el sistema en ${nombre}, SE${encontrado.semana} de ${encontrado.anio}: `,
        fuerte,
        encontrado.categoria ? `, ${encontrado.categoria}.` : '.',
      );
      const nota = document.createElement('small');
      const casos =
        encontrado.casos === null ? '' : `${encontrado.casos} casos; `;
      nota.textContent =
        encontrado.p50 !== null && encontrado.p75 !== null
          ? `${casos}cortes P50 ${f1(encontrado.p50)} y P75 ${f1(encontrado.p75)}.`
          : casos;
      real.setAttribute('role', 'status');
      real.replaceChildren(texto, nota);
    } catch {
      if (actual !== peticion) return;
      renderErrorFuente(
        real,
        () => void cargarReal(),
        `No se pudo consultar la presión calculada de ${nombre}. La simulación sigue funcionando.`,
      );
    }
  }

  // ---- Eventos ----------------------------------------------------------

  entradaCasos.addEventListener('input', () => {
    if (enSecuencia) return;
    actualizar();
    anunciar(resumen(), 500);
  });

  selectorDepto.addEventListener('change', () => {
    codigo = selectorDepto.value;
    pintarMapa(leer().resultado.categoria);
    anunciar(resumen(), 200);
    void cargarReal();
  });

  selectorSerie.addEventListener('change', () => {
    actualizar();
    anunciar(resumen(), 200);
    void cargarReal();
  });

  raiz.querySelectorAll<HTMLButtonElement>('[data-lab-preset]').forEach((b) => {
    b.addEventListener('click', () => {
      const preset = PRESETS_PRESION.find(
        (p) => p.clave === b.dataset.labPreset,
      );
      if (!preset || enSecuencia) return;
      ventanas = preset.ventanas.map((v) => ({
        anio: v.anio,
        casos: [...v.casos],
      }));
      entradaCasos.value = String(preset.observado);
      actualizar();
      anunciar(resumen());
    });
  });

  botonCalcular.addEventListener('click', () => void calcular());

  actualizar();
  void cargarReal();
}
