import { describe, it } from 'node:test';
import assert from 'node:assert';
import {
  formatearSigma,
  formatearPercentil,
  formatearCategoria,
  encontrarUltimaSemanaM1M2,
  encontrarUltimaSemanaPresion,
  type SemanaM1M2,
  type SemanaPresion,
} from '../../src/lib/ficha-departamental.ts';

describe('formatearSigma', () => {
  describe('null, undefined and invalid numbers', () => {
    it('returns "Sin dato" when input is null', () => {
      assert.strictEqual(formatearSigma(null), 'Sin dato');
    });

    it('returns "Sin dato" when input is undefined', () => {
      assert.strictEqual(formatearSigma(undefined), 'Sin dato');
    });

    it('returns "Sin dato" when input is NaN', () => {
      assert.strictEqual(formatearSigma(NaN), 'Sin dato');
    });

    it('returns "Sin dato" when input is Number.NaN', () => {
      assert.strictEqual(formatearSigma(Number.NaN), 'Sin dato');
    });
  });

  describe('positive numbers', () => {
    it('formats positive float with + prefix and 2 decimals', () => {
      assert.strictEqual(formatearSigma(1.5), '+1.50 σ');
    });

    it('formats positive integer with + prefix and 2 decimal zeroes', () => {
      assert.strictEqual(formatearSigma(2), '+2.00 σ');
    });

    it('rounds positive numbers to 2 decimal places', () => {
      assert.strictEqual(formatearSigma(1.23456), '+1.23 σ');
      assert.strictEqual(formatearSigma(1.236), '+1.24 σ');
    });

    it('formats small positive decimal values', () => {
      assert.strictEqual(formatearSigma(0.001), '+0.00 σ');
      assert.strictEqual(formatearSigma(0.005), '+0.01 σ');
    });
  });

  describe('negative numbers', () => {
    it('formats negative float without + prefix and 2 decimals', () => {
      assert.strictEqual(formatearSigma(-1.5), '-1.50 σ');
    });

    it('formats negative integer without + prefix', () => {
      assert.strictEqual(formatearSigma(-3), '-3.00 σ');
    });

    it('rounds negative numbers to 2 decimal places', () => {
      assert.strictEqual(formatearSigma(-2.456), '-2.46 σ');
      assert.strictEqual(formatearSigma(-0.001), '-0.00 σ');
    });
  });

  describe('zero edge cases', () => {
    it('formats positive zero (0) without + prefix', () => {
      assert.strictEqual(formatearSigma(0), '0.00 σ');
    });

    it('formats negative zero (-0) without + prefix', () => {
      assert.strictEqual(formatearSigma(-0), '0.00 σ');
    });
  });
});

describe('formatearPercentil', () => {
  it('returns "Sin dato" for null, undefined, or NaN', () => {
    assert.strictEqual(formatearPercentil(null), 'Sin dato');
    assert.strictEqual(formatearPercentil(undefined), 'Sin dato');
    assert.strictEqual(formatearPercentil(NaN), 'Sin dato');
  });

  it('formats percentile correctly with 1 decimal place', () => {
    assert.strictEqual(formatearPercentil(50), 'P50.0');
    assert.strictEqual(formatearPercentil(75.5), 'P75.5');
    assert.strictEqual(formatearPercentil(75.56), 'P75.6');
    assert.strictEqual(formatearPercentil(0), 'P0.0');
  });
});

describe('formatearCategoria', () => {
  it('returns "Sin clasificación" for null or undefined', () => {
    assert.strictEqual(formatearCategoria(null), 'Sin clasificación');
    assert.strictEqual(formatearCategoria(undefined), 'Sin clasificación');
  });

  it('formats categories correctly', () => {
    assert.strictEqual(formatearCategoria('baja'), 'Baja (≤ P50 histórico)');
    assert.strictEqual(
      formatearCategoria('media'),
      'Media (P50–P75 histórico)',
    );
    assert.strictEqual(formatearCategoria('alta'), 'Alta (> P75 histórico)');
  });
});

describe('encontrarUltimaSemanaM1M2', () => {
  it('returns null when array is empty or no data available', () => {
    assert.strictEqual(encontrarUltimaSemanaM1M2([]), null);
    const result = encontrarUltimaSemanaM1M2([
      {
        semana_epi: 1,
        iv_real: null,
        p25_baseline: null,
        mediana_baseline: null,
        p75_baseline: null,
        anomaly_sigma: null,
      },
    ]);
    assert.strictEqual(result, null);
  });

  it('finds last week with iv_real or anomaly_sigma data', () => {
    const semanas: SemanaM1M2[] = [
      {
        semana_epi: 1,
        iv_real: 0.5,
        p25_baseline: null,
        mediana_baseline: null,
        p75_baseline: null,
        anomaly_sigma: null,
      },
      {
        semana_epi: 2,
        iv_real: null,
        p25_baseline: null,
        mediana_baseline: null,
        p75_baseline: null,
        anomaly_sigma: 1.2,
      },
      {
        semana_epi: 3,
        iv_real: null,
        p25_baseline: null,
        mediana_baseline: null,
        p75_baseline: null,
        anomaly_sigma: null,
      },
    ];
    const result = encontrarUltimaSemanaM1M2(semanas);
    assert.notStrictEqual(result, null);
    assert.strictEqual(result?.semana_epi, 2);
  });
});

describe('encontrarUltimaSemanaPresion', () => {
  it('returns null when array is empty or no valid percentil', () => {
    assert.strictEqual(encontrarUltimaSemanaPresion([], 'probable'), null);
  });

  it('finds last week for requested series', () => {
    const semanas: SemanaPresion[] = [
      {
        semana_epi: 1,
        probable: {
          casos_observados: 5,
          percentil: 50,
          categoria: 'media',
          p50_baseline: 4,
          p75_baseline: 8,
          n_obs_baseline: 10,
          anios_baseline: 5,
        },
        confirmado: {
          casos_observados: null,
          percentil: null,
          categoria: null,
          p50_baseline: null,
          p75_baseline: null,
          n_obs_baseline: 0,
          anios_baseline: 0,
        },
      },
      {
        semana_epi: 2,
        probable: {
          casos_observados: null,
          percentil: null,
          categoria: null,
          p50_baseline: null,
          p75_baseline: null,
          n_obs_baseline: 0,
          anios_baseline: 0,
        },
        confirmado: {
          casos_observados: 2,
          percentil: 80,
          categoria: 'alta',
          p50_baseline: 1,
          p75_baseline: 3,
          n_obs_baseline: 10,
          anios_baseline: 5,
        },
      },
    ];

    const resultProbable = encontrarUltimaSemanaPresion(semanas, 'probable');
    assert.strictEqual(resultProbable?.semana_epi, 1);

    const resultConfirmado = encontrarUltimaSemanaPresion(
      semanas,
      'confirmado',
    );
    assert.strictEqual(resultConfirmado?.semana_epi, 2);
  });
});
