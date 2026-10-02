// Comportamiento del laboratorio de la ficha de idoneidad (LaboratorioIv.astro).
// Cada cambio de un control vuelve a calcular y a dibujar al instante;
// «Calcular paso a paso» recorre el método en orden (tres funciones, la
// combinación, el color del departamento). Esa secuencia es una visualización
// del método sobre un cálculo que ya está hecho, no una espera: si las
// animaciones están apagadas se salta y se muestra el resultado.

import {
  esNoDisponible,
  renderErrorFuente,
  renderSinDato,
} from '../components/estado-async';
import { obtenerSerieIdoneidad } from './analisis-api';
import { animacionesActivas } from './animaciones';
import { colorIv } from './colores';
import {
  CURVAS_IV,
  ORDEN_FACTORES,
  curvaIv,
  textoEntrada,
  type ClaveFactor,
} from './curvas-iv-config';
import { obtenerDepartamento } from './departamentos';
import {
  EJEMPLO_IV,
  PRESETS_IV,
  desgloseIv,
  formatearNumero,
  type EntradasIv,
} from './idoneidad';
import { aniosClimaPresentacion } from './tipos-analisis';

const MS_ETAPA = 900;

function esperar(ms: number): Promise<void> {
  return new Promise((resolver) => setTimeout(resolver, ms));
}

/** Llama a `cuadro(p)` con p de 0 a 1 durante `duracion` ms. */
function animar(duracion: number, cuadro: (p: number) => void): Promise<void> {
  return new Promise((resolver) => {
    const inicio = performance.now();
    const paso = (ahora: number) => {
      const p = Math.min(1, (ahora - inicio) / duracion);
      cuadro(1 - Math.pow(1 - p, 3));
      if (p < 1) requestAnimationFrame(paso);
      else resolver();
    };
    requestAnimationFrame(paso);
  });
}

export function iniciarLaboratorio(raiz: HTMLElement): void {
  const q = <T extends Element>(selector: string): T => {
    const elemento = raiz.querySelector<T>(selector);
    if (!elemento) throw new Error(`Laboratorio: falta ${selector}`);
    return elemento;
  };

  const controles = q<HTMLFieldSetElement>('[data-lab-controles]');
  const selectorDepto = q<HTMLSelectElement>('[data-lab-depto]');
  const botonCalcular = q<HTMLButtonElement>('[data-lab-calcular]');
  const estado = q<HTMLElement>('[data-lab-estado]');
  const cifra = q<HTMLElement>('[data-lab-cifra]');
  const barra = q<HTMLElement>('[data-lab-barra]');
  const ivTexto = q<HTMLElement>('[data-lab-iv]');
  const real = q<HTMLElement>('[data-lab-real]');
  const mapa = q<SVGElement>('[data-mapa-iv-svg]');
  const entradas = Object.fromEntries(
    ORDEN_FACTORES.map((clave) => [
      clave,
      q<HTMLInputElement>(`[data-lab-entrada="${clave}"]`),
    ]),
  ) as Record<ClaveFactor, HTMLInputElement>;
  const salidas = Object.fromEntries(
    ORDEN_FACTORES.map((clave) => [
      clave,
      q<HTMLOutputElement>(`[data-lab-salida="${clave}"]`),
    ]),
  ) as Record<ClaveFactor, HTMLOutputElement>;
  const paneles = Object.fromEntries(
    ORDEN_FACTORES.map((clave) => [
      clave,
      q<HTMLElement>(`[data-lab-panel="${clave}"]`),
    ]),
  ) as Record<ClaveFactor, HTMLElement>;
  const combina = q<HTMLElement>('[data-lab-combina]');
  const resultado = q<HTMLElement>('[data-lab-resultado]');

  let codigo = raiz.dataset.codigoInicial ?? 'SV-SS';
  let enSecuencia = false;
  let temporizadorAnuncio: ReturnType<typeof setTimeout> | undefined;

  function leer(): EntradasIv {
    return {
      temperatura: Number(entradas.ft.value),
      lluvia: Number(entradas.fr.value),
      humedad: Number(entradas.fh.value),
    };
  }

  function escribir(valores: EntradasIv): void {
    entradas.ft.value = String(valores.temperatura);
    entradas.fr.value = String(valores.lluvia);
    entradas.fh.value = String(valores.humedad);
  }

  function anunciar(mensaje: string, retraso = 0): void {
    clearTimeout(temporizadorAnuncio);
    temporizadorAnuncio = setTimeout(() => {
      estado.textContent = mensaje;
    }, retraso);
  }

  function nombreDepto(): string {
    return obtenerDepartamento(codigo)?.nombre ?? codigo;
  }

  /** Dibuja la curva de un factor con el marcador en `x`. */
  function pintarPanel(clave: ClaveFactor, x: number): void {
    const c = CURVAS_IV[clave];
    const curva = paneles[clave].querySelector('[data-lab-curva]');
    if (curva) curva.innerHTML = curvaIv(clave, x);
    const valor = paneles[clave].querySelector('[data-lab-valor]');
    if (valor) {
      valor.textContent = `${c.nombre} = ${formatearNumero(c.f(x), 2)}`;
    }
  }

  function pintarMapa(iv: number | null): void {
    mapa.querySelectorAll<SVGPathElement>('[data-codigo]').forEach((ruta) => {
      const activo = ruta.dataset.codigo === codigo;
      ruta.classList.toggle('seleccionado', activo);
      if (activo && iv !== null)
        ruta.style.setProperty('--relleno', colorIv(iv));
      else ruta.style.removeProperty('--relleno');
    });
    mapa.setAttribute(
      'aria-label',
      iv === null
        ? `Mapa de El Salvador con ${nombreDepto()} sin valor`
        : `Mapa de El Salvador con ${nombreDepto()} pintado según un Iv de ${formatearNumero(iv, 2)}`,
    );
  }

  function pintarIv(iv: number): void {
    cifra.textContent = formatearNumero(iv, 2);
    ivTexto.textContent = `Iv ${formatearNumero(iv, 2)}`;
    barra.style.width = `${Math.round(iv * 100)}%`;
    barra.style.background = colorIv(iv);
  }

  /** Estado completo a partir de los controles. */
  function actualizar(): void {
    const e = leer();
    const d = desgloseIv(e);
    for (const clave of ORDEN_FACTORES) {
      const valor = e[CURVAS_IV[clave].entrada];
      salidas[clave].textContent = textoEntrada(clave, valor);
      entradas[clave].setAttribute(
        'aria-valuetext',
        textoEntrada(clave, valor),
      );
      pintarPanel(clave, valor);
    }
    const factores = { ft: d.fT, fr: d.fR, fh: d.fH };
    for (const clave of ORDEN_FACTORES) {
      const v = raiz.querySelector(`[data-lab-v="${clave}"]`);
      if (v) v.textContent = formatearNumero(factores[clave], 2);
    }
    pintarIv(d.iv);
    pintarMapa(d.iv);
  }

  function resumenResultado(): string {
    const e = leer();
    const d = desgloseIv(e);
    return (
      `${nombreDepto()}: temperatura ${textoEntrada('ft', e.temperatura)}, ` +
      `lluvia ${textoEntrada('fr', e.lluvia)}, humedad ${textoEntrada('fh', e.humedad)}. ` +
      `Iv de la simulación ${formatearNumero(d.iv, 2)}.`
    );
  }

  // ---- Recorrido paso a paso -------------------------------------------

  async function calcular(): Promise<void> {
    if (enSecuencia) return;
    if (!animacionesActivas()) {
      actualizar();
      anunciar(resumenResultado());
      return;
    }
    enSecuencia = true;
    controles.disabled = true;
    botonCalcular.setAttribute('aria-busy', 'true');
    const e = leer();
    const d = desgloseIv(e);

    const etapas: HTMLElement[] = [
      paneles.ft,
      paneles.fr,
      paneles.fh,
      combina,
      resultado,
    ];
    etapas.forEach((el) => {
      el.classList.remove('lab-hecho', 'lab-activo');
      el.classList.add('lab-espera');
    });
    // Punto de partida del recorrido: marcadores en el origen y mapa sin color.
    for (const clave of ORDEN_FACTORES) {
      pintarPanel(clave, CURVAS_IV[clave].desde);
    }
    pintarIv(0);
    mapa
      .querySelector<SVGPathElement>(`[data-codigo="${codigo}"]`)
      ?.style.removeProperty('--relleno');
    raiz.querySelectorAll<HTMLElement>('[data-lab-v]').forEach((v) => {
      v.textContent = '·';
    });

    const textos = [
      `Paso 1 de 5: la temperatura de ${textoEntrada('ft', e.temperatura)} pasa por fT y da ${formatearNumero(d.fT, 2)}.`,
      `Paso 2 de 5: la lluvia de ${textoEntrada('fr', e.lluvia)} pasa por fR y da ${formatearNumero(d.fR, 2)}.`,
      `Paso 3 de 5: la humedad de ${textoEntrada('fh', e.humedad)} pasa por fH y da ${formatearNumero(d.fH, 2)}.`,
      `Paso 4 de 5: los tres factores se combinan.`,
      `Paso 5 de 5: el Iv de ${formatearNumero(d.iv, 2)} pinta ${nombreDepto()}.`,
    ];
    const factores = { ft: d.fT, fr: d.fR, fh: d.fH };

    for (let i = 0; i < etapas.length; i += 1) {
      const etapa = etapas[i];
      etapa.classList.remove('lab-espera');
      etapa.classList.add('lab-activo');
      anunciar(textos[i]);
      // En pantallas angostas los paneles quedan en columna y fuera de vista:
      // se acompaña el recorrido para que se vea qué se ilumina.
      const caja = etapa.getBoundingClientRect();
      if (caja.top < 0 || caja.bottom > window.innerHeight) {
        etapa.scrollIntoView({ block: 'center', behavior: 'smooth' });
      }

      if (i < 3) {
        const clave = ORDEN_FACTORES[i];
        const c = CURVAS_IV[clave];
        const destino = e[c.entrada];
        await animar(MS_ETAPA - 150, (p) => {
          pintarPanel(clave, c.desde + (destino - c.desde) * p);
        });
        pintarPanel(clave, destino);
        const v = raiz.querySelector(`[data-lab-v="${clave}"]`);
        if (v) v.textContent = formatearNumero(factores[clave], 2);
        const termino = raiz.querySelector<HTMLElement>(
          `[data-lab-t="${clave}"]`,
        );
        termino?.classList.add('lab-activo');
        await esperar(150);
      } else if (i === 3) {
        await animar(MS_ETAPA, (p) => {
          cifra.textContent = formatearNumero(d.iv * p, 2);
          ivTexto.textContent = `Iv ${formatearNumero(d.iv * p, 2)}`;
        });
      } else {
        pintarIv(d.iv);
        pintarMapa(d.iv);
        await esperar(MS_ETAPA);
      }
      etapa.classList.remove('lab-activo');
      etapa.classList.add('lab-hecho');
    }

    etapas.forEach((el) =>
      el.classList.remove('lab-hecho', 'lab-espera', 'lab-activo'),
    );
    raiz
      .querySelectorAll('.lab-termino')
      .forEach((t) => t.classList.remove('lab-activo'));
    actualizar();
    anunciar(resumenResultado());
    controles.disabled = false;
    botonCalcular.removeAttribute('aria-busy');
    botonCalcular.focus();
    enSecuencia = false;
  }

  // ---- Iv que mide el sistema ------------------------------------------

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
        iv: number;
        p25: number | null;
        p75: number | null;
      } | null = null;
      for (const anio of anios) {
        const serie = await obtenerSerieIdoneidad(codigo, anio);
        if (actual !== peticion) return;
        if (esNoDisponible(serie)) continue;
        const ultima = [...serie.semanas]
          .reverse()
          .find((s) => s.iv_real !== null);
        if (ultima && ultima.iv_real !== null) {
          encontrado = {
            anio,
            semana: ultima.semana_epi,
            iv: ultima.iv_real,
            p25: ultima.p25_baseline,
            p75: ultima.p75_baseline,
          };
          break;
        }
      }
      if (actual !== peticion) return;
      if (!encontrado) {
        renderSinDato(real, `El sistema no tiene Iv publicado para ${nombre}.`);
        return;
      }
      real.removeAttribute('aria-busy');
      const banda =
        encontrado.p25 !== null && encontrado.p75 !== null
          ? ` La banda histórica de esa semana va de ${formatearNumero(encontrado.p25, 2)} a ${formatearNumero(encontrado.p75, 2)}.`
          : '';
      // Nodos de texto y no innerHTML: el nombre sale de la lista de
      // departamentos o, si no está, del valor del selector (CodeQL).
      const cifra = document.createElement('strong');
      cifra.textContent = formatearNumero(encontrado.iv, 2);
      const texto = document.createElement('p');
      texto.append(
        `Iv medido por el sistema en ${nombre}, SE${encontrado.semana} de ${encontrado.anio}: `,
        cifra,
        `.${banda}`,
      );
      const nota = document.createElement('small');
      nota.textContent =
        'Sale de la temperatura, la humedad y la lluvia observadas esa semana, con esta misma fórmula.';
      real.setAttribute('role', 'status');
      real.replaceChildren(texto, nota);
    } catch {
      if (actual !== peticion) return;
      renderErrorFuente(
        real,
        () => void cargarReal(),
        `No se pudo consultar el Iv medido de ${nombre}. La simulación sigue funcionando.`,
      );
    }
  }

  // ---- Eventos ----------------------------------------------------------

  for (const clave of ORDEN_FACTORES) {
    entradas[clave].addEventListener('input', () => {
      if (enSecuencia) return;
      actualizar();
      anunciar(resumenResultado(), 500);
    });
  }

  selectorDepto.addEventListener('change', () => {
    codigo = selectorDepto.value;
    pintarMapa(desgloseIv(leer()).iv);
    anunciar(resumenResultado(), 200);
    void cargarReal();
  });

  raiz.querySelectorAll<HTMLButtonElement>('[data-lab-preset]').forEach((b) => {
    b.addEventListener('click', () => {
      const preset = PRESETS_IV.find((p) => p.clave === b.dataset.labPreset);
      if (!preset || enSecuencia) return;
      escribir(preset.entradas);
      actualizar();
      anunciar(resumenResultado());
    });
  });

  botonCalcular.addEventListener('click', () => void calcular());

  escribir(EJEMPLO_IV);
  actualizar();
  void cargarReal();
}
