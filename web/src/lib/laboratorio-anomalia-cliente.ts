// Comportamiento del laboratorio de la ficha de anomalía climática
// (LaboratorioAnomalia.astro). Cada cambio vuelve a calcular y a dibujar al
// instante; «Calcular paso a paso» recorre el método en orden (conjunto,
// mediana, desviación, división, color) sobre un cálculo ya hecho. Con las
// animaciones apagadas se salta y se muestra el resultado.

import {
  esNoDisponible,
  renderErrorFuente,
  renderSinDato,
} from '../components/estado-async';
import { obtenerSerieIdoneidad } from './analisis-api';
import { animacionesActivas } from './animaciones';
import {
  ANIOS_LABORATORIO,
  PRESETS_ANOMALIA,
  calcularSigma,
  resumirPool,
} from './anomalia';
import { colorAnomalia } from './colores';
import { obtenerDepartamento } from './departamentos';
import { formatearNumero } from './idoneidad';
import { tiraAnomalia } from './laboratorio-anomalia';
import {
  MS_ETAPA,
  activarEtapa,
  animar,
  cerrarEtapa,
  esperar,
  limpiarEtapas,
  prepararEtapas,
} from './recorrido';
import { aniosClimaPresentacion } from './tipos-analisis';

const f2 = (n: number) => formatearNumero(n, 2);
// Signo menos tipográfico, como en la escala de la ficha.
const conSigno = (n: number) => (n > 0 ? `+${f2(n)}` : f2(n).replace('-', '−'));

export function iniciarLaboratorioAnomalia(raiz: HTMLElement): void {
  const q = <T extends Element>(selector: string): T => {
    const elemento = raiz.querySelector<T>(selector);
    if (!elemento) throw new Error(`Laboratorio de M2: falta ${selector}`);
    return elemento;
  };

  const controles = q<HTMLFieldSetElement>('[data-lab-controles]');
  const selectorDepto = q<HTMLSelectElement>('[data-lab-depto]');
  const entradaValor = q<HTMLInputElement>('[data-lab-valor]');
  const salidaValor = q<HTMLOutputElement>('[data-lab-salida-valor]');
  const referencias = Array.from(
    raiz.querySelectorAll<HTMLInputElement>('[data-lab-referencia]'),
  );
  const botonCalcular = q<HTMLButtonElement>('[data-lab-calcular]');
  const estado = q<HTMLElement>('[data-lab-estado]');
  const tira = q<HTMLElement>('[data-lab-tira]');
  const textoMediana = q<HTMLElement>('[data-lab-mediana]');
  const textoDesviacion = q<HTMLElement>('[data-lab-desviacion]');
  const textoSigma = q<HTMLElement>('[data-lab-sigma]');
  const cifra = q<HTMLElement>('[data-lab-cifra]');
  const frase = q<HTMLElement>('[data-lab-frase]');
  const real = q<HTMLElement>('[data-lab-real]');
  const mapa = q<SVGElement>('[data-mapa-ficha-svg]');
  const etapa = (nombre: string) =>
    q<HTMLElement>(`[data-lab-etapa="${nombre}"]`);
  const etapas = ['conjunto', 'mediana', 'desviacion', 'sigma', 'color'].map(
    etapa,
  );

  let codigo = raiz.dataset.codigoInicial ?? 'SV-SS';
  let enSecuencia = false;
  let temporizadorAnuncio: ReturnType<typeof setTimeout> | undefined;

  function leer() {
    const valor = Number(entradaValor.value);
    const refs = referencias.map((campo) => {
      if (campo.value.trim() === '') return null;
      const n = Number(campo.value);
      return Number.isFinite(n) ? Math.min(1, Math.max(0, n)) : null;
    });
    const pool = refs.filter((v): v is number => v !== null);
    const r = resumirPool(pool);
    const sigma = calcularSigma(valor, r.mediana, r.desviacion);
    return { valor, refs, pool, r, sigma };
  }

  function nombreDepto(): string {
    return obtenerDepartamento(codigo)?.nombre ?? codigo;
  }

  function anunciar(mensaje: string, retraso = 0): void {
    clearTimeout(temporizadorAnuncio);
    temporizadorAnuncio = setTimeout(() => {
      estado.textContent = mensaje;
    }, retraso);
  }

  function pintarTira(
    c: ReturnType<typeof leer>,
    etapasTira = { mediana: true, desviacion: true },
  ): void {
    const t = tiraAnomalia(c.valor, c.refs, c.r, etapasTira);
    tira.innerHTML = t.svg;
    tira.setAttribute('aria-label', t.etiqueta);
  }

  function pintarMapa(sigma: number | null): void {
    mapa.querySelectorAll<SVGPathElement>('[data-codigo]').forEach((ruta) => {
      const activo = ruta.dataset.codigo === codigo;
      ruta.classList.toggle('seleccionado', activo);
      if (activo && sigma !== null) {
        ruta.style.setProperty('--relleno', colorAnomalia(sigma));
      } else ruta.style.removeProperty('--relleno');
    });
    mapa.setAttribute(
      'aria-label',
      sigma === null
        ? `Mapa de El Salvador con ${nombreDepto()} sin anomalía`
        : `Mapa de El Salvador con ${nombreDepto()} pintado según una anomalía de ${conSigno(sigma)} σ`,
    );
  }

  function textoResultado(c: ReturnType<typeof leer>): string {
    if (c.r.mediana === null) {
      return `Con ${c.pool.length} años de referencia no hay línea base: hacen falta al menos 3. La semana queda sin anomalía.`;
    }
    if (c.sigma === null) {
      return 'Todos los años de referencia tienen el mismo Iv: la desviación es cero y la semana queda sin anomalía.';
    }
    const lectura =
      Math.abs(c.sigma) < 0.5
        ? 'cerca de lo habitual'
        : c.sigma > 0
          ? 'por encima de lo habitual'
          : 'por debajo de lo habitual';
    return `Iv ${f2(c.valor)} frente a una mediana de ${f2(c.r.mediana)}: ${conSigno(c.sigma)} σ, ${lectura}.`;
  }

  function actualizar(): void {
    const c = leer();
    salidaValor.textContent = f2(c.valor);
    entradaValor.setAttribute('aria-valuetext', f2(c.valor));
    pintarTira(c);
    textoMediana.textContent =
      c.r.mediana === null ? 'sin dato' : f2(c.r.mediana);
    textoDesviacion.textContent =
      c.r.desviacion === null ? 'sin dato' : formatearNumero(c.r.desviacion, 3);
    const s = c.sigma === null ? 'sin dato' : conSigno(c.sigma);
    textoSigma.textContent = s;
    cifra.textContent = s;
    frase.textContent = textoResultado(c);
    pintarMapa(c.sigma);
  }

  function resumen(): string {
    return `${nombreDepto()}: ${textoResultado(leer())}`;
  }

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
    prepararEtapas(etapas);
    pintarTira(c, { mediana: false, desviacion: false });
    for (const t of [textoMediana, textoDesviacion, textoSigma, cifra]) {
      t.textContent = '·';
    }
    frase.textContent = '';
    pintarMapa(null);

    const sinBase = c.r.mediana === null;
    const textos = [
      `Paso 1 de 5: el conjunto tiene ${c.pool.length} años de referencia; 2026 queda aparte.`,
      sinBase
        ? 'Paso 2 de 5: con menos de 3 años no hay mediana.'
        : `Paso 2 de 5: la mediana del conjunto es ${f2(c.r.mediana as number)}.`,
      sinBase
        ? 'Paso 3 de 5: sin línea base no hay desviación.'
        : `Paso 3 de 5: la desviación muestral es ${formatearNumero(c.r.desviacion as number, 3)}.`,
      c.sigma === null
        ? 'Paso 4 de 5: no se puede dividir; la semana queda sin anomalía.'
        : `Paso 4 de 5: (${f2(c.valor)} − ${f2(c.r.mediana as number)}) / ${formatearNumero(c.r.desviacion as number, 3)} = ${conSigno(c.sigma)}.`,
      c.sigma === null
        ? `Paso 5 de 5: ${nombreDepto()} queda sin color.`
        : `Paso 5 de 5: ${conSigno(c.sigma)} σ pinta ${nombreDepto()}.`,
    ];

    for (let i = 0; i < etapas.length; i += 1) {
      activarEtapa(etapas[i]);
      anunciar(textos[i]);
      if (i === 1) {
        pintarTira(c, { mediana: true, desviacion: false });
        textoMediana.textContent =
          c.r.mediana === null ? 'sin dato' : f2(c.r.mediana);
        await esperar(MS_ETAPA);
      } else if (i === 2) {
        pintarTira(c);
        textoDesviacion.textContent =
          c.r.desviacion === null
            ? 'sin dato'
            : formatearNumero(c.r.desviacion, 3);
        await esperar(MS_ETAPA);
      } else if (i === 3) {
        if (c.sigma !== null) {
          const destino = c.sigma;
          await animar(MS_ETAPA, (p) => {
            textoSigma.textContent = conSigno(destino * p);
          });
        }
        textoSigma.textContent =
          c.sigma === null ? 'sin dato' : conSigno(c.sigma);
      } else if (i === 4) {
        pintarMapa(c.sigma);
        cifra.textContent = c.sigma === null ? 'sin dato' : conSigno(c.sigma);
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

  // ---- Anomalía que mide el sistema ------------------------------------

  let peticion = 0;

  async function cargarReal(): Promise<void> {
    const actual = (peticion += 1);
    const nombre = nombreDepto();
    real.setAttribute('aria-busy', 'true');
    const p = document.createElement('p');
    p.className = 'lab-cargando';
    p.textContent = `Consultando la serie de Iv de ${nombre}…`;
    real.replaceChildren(p);
    try {
      const anios = aniosClimaPresentacion().slice(-2).reverse();
      let encontrado: {
        anio: number;
        semana: number;
        sigma: number;
        iv: number | null;
        p25: number | null;
        p75: number | null;
      } | null = null;
      for (const anio of anios) {
        const serie = await obtenerSerieIdoneidad(codigo, anio);
        if (actual !== peticion) return;
        if (esNoDisponible(serie)) continue;
        const ultima = [...serie.semanas]
          .reverse()
          .find((s) => s.anomaly_sigma !== null);
        if (ultima && ultima.anomaly_sigma !== null) {
          encontrado = {
            anio,
            semana: ultima.semana_epi,
            sigma: ultima.anomaly_sigma,
            iv: ultima.iv_real,
            p25: ultima.p25_baseline,
            p75: ultima.p75_baseline,
          };
          break;
        }
      }
      if (actual !== peticion) return;
      if (!encontrado) {
        renderSinDato(
          real,
          `El sistema no tiene anomalía publicada para ${nombre}.`,
        );
        return;
      }
      real.removeAttribute('aria-busy');
      // Nodos de texto y no innerHTML: el nombre sale de la lista de
      // departamentos o del valor del selector (CodeQL).
      const fuerte = document.createElement('strong');
      fuerte.textContent = `${conSigno(encontrado.sigma)} σ`;
      const texto = document.createElement('p');
      const iv =
        encontrado.iv === null ? '' : ` con un Iv de ${f2(encontrado.iv)}`;
      texto.append(
        `Anomalía medida por el sistema en ${nombre}, SE${encontrado.semana} de ${encontrado.anio}${iv}: `,
        fuerte,
        '.',
      );
      const nota = document.createElement('small');
      nota.textContent =
        encontrado.p25 !== null && encontrado.p75 !== null
          ? `La banda histórica de esa semana (P25 a P75) va de ${f2(encontrado.p25)} a ${f2(encontrado.p75)}.`
          : 'Esa semana no tiene banda histórica publicada.';
      real.setAttribute('role', 'status');
      real.replaceChildren(texto, nota);
    } catch {
      if (actual !== peticion) return;
      renderErrorFuente(
        real,
        () => void cargarReal(),
        `No se pudo consultar la anomalía medida de ${nombre}. La simulación sigue funcionando.`,
      );
    }
  }

  // ---- Eventos ----------------------------------------------------------

  const alCambiar = () => {
    if (enSecuencia) return;
    actualizar();
    anunciar(resumen(), 500);
  };
  entradaValor.addEventListener('input', alCambiar);
  referencias.forEach((campo) => campo.addEventListener('input', alCambiar));

  selectorDepto.addEventListener('change', () => {
    codigo = selectorDepto.value;
    pintarMapa(leer().sigma);
    anunciar(resumen(), 200);
    void cargarReal();
  });

  raiz.querySelectorAll<HTMLButtonElement>('[data-lab-preset]').forEach((b) => {
    b.addEventListener('click', () => {
      const preset = PRESETS_ANOMALIA.find(
        (p) => p.clave === b.dataset.labPreset,
      );
      if (!preset || enSecuencia) return;
      entradaValor.value = String(preset.valor);
      referencias.forEach((campo, i) => {
        const v = preset.referencias[i];
        campo.value = v === null || v === undefined ? '' : String(v);
      });
      actualizar();
      anunciar(resumen());
    });
  });

  botonCalcular.addEventListener('click', () => void calcular());

  if (referencias.length !== ANIOS_LABORATORIO.length) {
    throw new Error('Laboratorio de M2: faltan años de referencia');
  }
  actualizar();
  void cargarReal();
}
