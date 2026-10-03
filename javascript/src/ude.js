/**
 * sfsa.ude — Unit & Dimensional Analysis Engine (UDE)
 * ==================================================
 * Guarantees formal dimensional homogeneity across all layer transfers and scientific computations.
 * Tracks SI base dimension exponents [M, L, T, Theta, N, I, J], verifying compatibility in O(1)
 * and preventing silent scale/unit conversion disasters (e.g., Pascal vs. Bar, Joule vs. eV).
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

const EPS = 1e-9;
const NAMES = ['mass', 'length', 'time', 'temp', 'amount', 'current', 'luminous'];
const SYMBOLS = ['kg', 'm', 's', 'K', 'mol', 'A', 'cd'];

export class DimensionVector {
  constructor({ mass = 0, length = 0, time = 0, temp = 0, amount = 0, current = 0, luminous = 0 } = {}) {
    // exponents may be rational (sqrt(Hz) has time^-1/2); tiny float noise is rounded away
    const r = (v) => Math.round(v * 1e9) / 1e9;
    this.mass = r(mass);
    this.length = r(length);
    this.time = r(time);
    this.temp = r(temp);
    this.amount = r(amount);
    this.current = r(current);
    this.luminous = r(luminous);
  }

  _combine(other, sign) {
    const o = {};
    for (const n of NAMES) o[n] = this[n] + sign * other[n];
    return new DimensionVector(o);
  }

  add(other) { return this._combine(other, +1); }
  sub(other) { return this._combine(other, -1); }
  mul(other) { return this._combine(other, +1); }
  div(other) { return this._combine(other, -1); }

  pow(p) {
    const o = {};
    for (const n of NAMES) o[n] = this[n] * p;
    return new DimensionVector(o);
  }

  equals(other) {
    return NAMES.every((n) => Math.abs(this[n] - other[n]) < EPS);
  }

  isDimensionless() {
    return NAMES.every((n) => Math.abs(this[n]) < EPS);
  }

  label() {
    const parts = NAMES.map((n, i) => (Math.abs(this[n]) < EPS ? null : `${SYMBOLS[i]}^${this[n]}`)).filter(Boolean);
    return parts.length ? parts.join(' ') : '1';
  }
}

export class UnknownUnitError extends Error {
  constructor(message) { super(message); this.name = 'UnknownUnitError'; }
}

export class UnitSyntaxError extends Error {
  constructor(message) { super(message); this.name = 'UnitSyntaxError'; }
}

const D = (o) => new DimensionVector(o);
const ONE = D({});
const PRESSURE = D({ mass: 1, length: -1, time: -2 });
const ENERGY = D({ mass: 1, length: 2, time: -2 });
const POWER = D({ mass: 1, length: 2, time: -3 });
const FORCE = D({ mass: 1, length: 1, time: -2 });
const CURRENT = D({ current: 1 });
const CHARGE = D({ time: 1, current: 1 });
const VOLTAGE = D({ mass: 1, length: 2, time: -3, current: -1 });
const YEAR_S = 31557600.0;
const AU_M = 149597870700.0;

// Legacy lowercase aliases (v0.2.0 registry): consulted only after the case-sensitive SI lookup.
export const CANONICAL_DIMENSIONS = {
  dimensionless: [ONE, 1.0], fraction: [ONE, 1.0], percent: [ONE, 0.01],
  m: [D({ length: 1 }), 1.0], meter: [D({ length: 1 }), 1.0], km: [D({ length: 1 }), 1e3],
  mm: [D({ length: 1 }), 1e-3], cm: [D({ length: 1 }), 1e-2],
  kg: [D({ mass: 1 }), 1.0], g: [D({ mass: 1 }), 1e-3], tonne: [D({ mass: 1 }), 1e3],
  s: [D({ time: 1 }), 1.0], second: [D({ time: 1 }), 1.0], min: [D({ time: 1 }), 60.0],
  hour: [D({ time: 1 }), 3600.0], year: [D({ time: 1 }), YEAR_S],
  k: [D({ temp: 1 }), 1.0], kelvin: [D({ temp: 1 }), 1.0],
  pa: [PRESSURE, 1.0], pascal: [PRESSURE, 1.0], bar: [PRESSURE, 1e5], atm: [PRESSURE, 101325.0],
  kpa: [PRESSURE, 1e3], mpa: [PRESSURE, 1e6],
  j: [ENERGY, 1.0], joule: [ENERGY, 1.0], kj: [ENERGY, 1e3], ev: [ENERGY, 1.602176634e-19],
  n: [FORCE, 1.0], newton: [FORCE, 1.0],
  w: [POWER, 1.0], watt: [POWER, 1.0], kw: [POWER, 1e3], mw: [POWER, 1e6]
};

const T1 = D({ temp: 1 });
const SI_UNITS = {
  dimensionless: [ONE, 1.0], fraction: [ONE, 1.0], percent: [ONE, 0.01], '%': [ONE, 0.01],
  ppm: [ONE, 1e-6], ppb: [ONE, 1e-9], rad: [ONE, 1.0], sr: [ONE, 1.0],
  deg: [ONE, Math.PI / 180], arcsec: [ONE, Math.PI / 648000],
  m: [D({ length: 1 }), 1.0], meter: [D({ length: 1 }), 1.0], metre: [D({ length: 1 }), 1.0], AU: [D({ length: 1 }), AU_M],
  ly: [D({ length: 1 }), 299792458.0 * YEAR_S], pc: [D({ length: 1 }), (AU_M * 648000.0) / Math.PI],
  in: [D({ length: 1 }), 0.0254], ft: [D({ length: 1 }), 0.3048], mile: [D({ length: 1 }), 1609.344],
  nmi: [D({ length: 1 }), 1852.0], angstrom: [D({ length: 1 }), 1e-10],
  kg: [D({ mass: 1 }), 1.0], g: [D({ mass: 1 }), 1e-3], tonne: [D({ mass: 1 }), 1e3], lb: [D({ mass: 1 }), 0.45359237],
  u: [D({ mass: 1 }), 1.6605390666e-27], Da: [D({ mass: 1 }), 1.6605390666e-27],
  s: [D({ time: 1 }), 1.0], second: [D({ time: 1 }), 1.0], min: [D({ time: 1 }), 60.0], minute: [D({ time: 1 }), 60.0],
  h: [D({ time: 1 }), 3600.0], hour: [D({ time: 1 }), 3600.0], day: [D({ time: 1 }), 86400.0], d: [D({ time: 1 }), 86400.0],
  week: [D({ time: 1 }), 604800.0], month: [D({ time: 1 }), YEAR_S / 12], year: [D({ time: 1 }), YEAR_S], yr: [D({ time: 1 }), YEAR_S],
  Hz: [D({ time: -1 }), 1.0], hertz: [D({ time: -1 }), 1.0],
  K: [T1, 1.0], kelvin: [T1, 1.0], degC: [T1, 1.0], '°C': [T1, 1.0], celsius: [T1, 1.0],
  degF: [T1, 5.0 / 9.0], '°F': [T1, 5.0 / 9.0],
  mol: [D({ amount: 1 }), 1.0], mole: [D({ amount: 1 }), 1.0], A: [CURRENT, 1.0], ampere: [CURRENT, 1.0], cd: [D({ luminous: 1 }), 1.0],
  N: [FORCE, 1.0], newton: [FORCE, 1.0],
  Pa: [PRESSURE, 1.0], pascal: [PRESSURE, 1.0], bar: [PRESSURE, 1e5], atm: [PRESSURE, 101325.0],
  torr: [PRESSURE, 101325.0 / 760.0], mmHg: [PRESSURE, 133.322387415], psi: [PRESSURE, 6894.757293168],
  J: [ENERGY, 1.0], joule: [ENERGY, 1.0], eV: [ENERGY, 1.602176634e-19], cal: [ENERGY, 4.184], Wh: [ENERGY, 3600.0],
  W: [POWER, 1.0], watt: [POWER, 1.0],
  L: [D({ length: 3 }), 1e-3], liter: [D({ length: 3 }), 1e-3], litre: [D({ length: 3 }), 1e-3],
  C: [CHARGE, 1.0], V: [VOLTAGE, 1.0], volt: [VOLTAGE, 1.0],
  ohm: [VOLTAGE.div(CURRENT), 1.0], 'Ω': [VOLTAGE.div(CURRENT), 1.0], S: [CURRENT.div(VOLTAGE), 1.0],
  F: [CHARGE.div(VOLTAGE), 1.0], H: [VOLTAGE.mul(D({ time: 1 })).div(CURRENT), 1.0],
  Wb: [VOLTAGE.mul(D({ time: 1 })), 1.0], T: [VOLTAGE.mul(D({ time: 1 })).div(D({ length: 2 })), 1.0]
};

const PREFIXABLE = new Set(['m', 'g', 's', 'Hz', 'K', 'mol', 'A', 'cd', 'N', 'Pa', 'bar', 'J', 'eV', 'cal', 'Wh', 'W', 'L', 'C', 'V',
  'ohm', 'Ω', 'S', 'F', 'H', 'Wb', 'T', 'pc', 'u', 'Da', 'rad']);
const PREFIXES = {
  Y: 1e24, Z: 1e21, E: 1e18, P: 1e15, T: 1e12, G: 1e9, M: 1e6, k: 1e3, h: 1e2, da: 1e1,
  d: 1e-1, c: 1e-2, m: 1e-3, 'µ': 1e-6, 'μ': 1e-6, u: 1e-6, n: 1e-9, p: 1e-12, f: 1e-15, a: 1e-18, z: 1e-21, y: 1e-24
};
const TO_KELVIN = {
  K: (v) => v, kelvin: (v) => v,
  degC: (v) => v + 273.15, '°C': (v) => v + 273.15, celsius: (v) => v + 273.15,
  degF: (v) => ((v - 32) * 5) / 9 + 273.15, '°F': (v) => ((v - 32) * 5) / 9 + 273.15
};
const FROM_KELVIN = {
  K: (k) => k, kelvin: (k) => k,
  degC: (k) => k - 273.15, '°C': (k) => k - 273.15, celsius: (k) => k - 273.15,
  degF: (k) => ((k - 273.15) * 9) / 5 + 32, '°F': (k) => ((k - 273.15) * 9) / 5 + 32
};

const TOKEN = /\s*(?:(\d+\.?\d*(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?)|([A-Za-zµμ°%Ω_][A-Za-zµμ°%Ω_]*)|(\*\*|\^)|([*/·])|(\()|(\))|([+-]))/y;
const KINDS = ['num', 'name', 'pow', 'op', 'lp', 'rp', 'sign'];

function closeMatches(name, candidates) {
  const dist = (a, b) => {
    const dp = Array.from({ length: a.length + 1 }, (_, i) => [i, ...Array(b.length).fill(0)]);
    for (let j = 1; j <= b.length; j++) dp[0][j] = j;
    for (let i = 1; i <= a.length; i++) {
      for (let j = 1; j <= b.length; j++) {
        dp[i][j] = Math.min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
      }
    }
    return dp[a.length][b.length];
  };
  return candidates.map((c) => [c, dist(name.toLowerCase(), c.toLowerCase())]).filter(([, d]) => d <= 2)
    .sort((x, y) => x[1] - y[1]).slice(0, 3).map(([c]) => c);
}

export class UnitDimensionalEngine {
  constructor() {
    this.registry = { ...CANONICAL_DIMENSIONS };
    this._cache = new Map();
  }

  _resolveName(name, expr) {
    if (Object.prototype.hasOwnProperty.call(SI_UNITS, name)) return SI_UNITS[name];
    const parses = [];
    for (const [pre, factor] of Object.entries(PREFIXES)) {
      const rest = name.slice(pre.length);
      if (name.startsWith(pre) && rest.length > 0 && PREFIXABLE.has(rest)) {
        const [dim, scale] = SI_UNITS[rest];
        parses.push([dim, scale * factor, `${pre}+${rest}`]);
      }
    }
    const distinct = new Set(parses.map(([d, s]) => `${d.label()}|${s.toPrecision(12)}`));
    if (distinct.size > 1) {
      throw new UnknownUnitError(`Ambiguous unit '${name}' in '${expr}': ${parses.map((p) => p[2]).join(', ')}`);
    }
    if (parses.length) return [parses[0][0], parses[0][1]];
    const legacy = Object.prototype.hasOwnProperty.call(this.registry, name.toLowerCase()) ? this.registry[name.toLowerCase()] : null;
    if (legacy) return legacy;
    const close = closeMatches(name, Object.keys(SI_UNITS));
    throw new UnknownUnitError(`Unknown unit '${name}' in '${expr}'.${close.length ? ` Did you mean: ${close.join(', ')}?` : ''}`);
  }

  _tokens(expr) {
    const s = expr.trim();
    const out = [];
    TOKEN.lastIndex = 0;
    let pos = 0;
    while (pos < s.length) {
      TOKEN.lastIndex = pos;
      const m = TOKEN.exec(s);
      if (!m || TOKEN.lastIndex === pos) throw new UnitSyntaxError(`Unexpected character '${s[pos]}' in unit '${expr}'`);
      const idx = m.slice(1).findIndex((g) => g !== undefined);
      out.push([KINDS[idx], m[idx + 1]]);
      pos = TOKEN.lastIndex;
    }
    return out;
  }

  /** Resolves a unit expression ("m/s", "1/year", "kg*m/s^2", "J/(kg*K)") to [DimensionVector, SI scale]. */
  parseUnit(unitStr) {
    const key = String(unitStr).trim();
    if (key === '') throw new UnitSyntaxError('Empty unit string');
    if (this._cache.has(key)) return this._cache.get(key);
    const toks = this._tokens(key);
    let pos = 0;
    const peek = () => (pos < toks.length ? toks[pos] : ['end', '']);
    const take = () => { const t = peek(); pos += 1; return t; };
    const literal = () => {
      let [kind, val] = take();
      let sign = 1;
      if (kind === 'sign') { sign = val === '-' ? -1 : 1; [kind, val] = take(); }
      if (kind !== 'num') throw new UnitSyntaxError(`Exponent must be a number in '${key}'`);
      return sign * Number(val);
    };
    const exponent = () => {
      if (peek()[0] === 'lp') {
        take();
        let num = literal();
        if (peek()[0] === 'op' && peek()[1] === '/') { take(); num /= literal(); }
        if (take()[0] !== 'rp') throw new UnitSyntaxError(`Unbalanced parentheses in exponent of '${key}'`);
        return num;
      }
      return literal();
    };
    const factor = () => {
      const [kind, val] = take();
      let res;
      if (kind === 'lp') {
        const [d, s] = expr();
        if (take()[0] !== 'rp') throw new UnitSyntaxError(`Unbalanced parentheses in unit '${key}'`);
        res = [d, s];
      } else if (kind === 'num') {
        res = [ONE, Number(val)];
      } else if (kind === 'name') {
        res = this._resolveName(val, key);
      } else {
        throw new UnitSyntaxError(`Unexpected '${val || kind}' in unit '${key}'`);
      }
      if (peek()[0] === 'pow') {
        take();
        const e = exponent();
        return [res[0].pow(e), res[1] ** e];
      }
      return res;
    };
    const expr = () => {
      let [d, s] = factor();
      for (;;) {
        const [kind, val] = peek();
        if (kind === 'op') {
          take();
          const [d2, s2] = factor();
          if (val === '/') { d = d.div(d2); s /= s2; } else { d = d.mul(d2); s *= s2; }
        } else if (kind === 'name' || kind === 'lp') {
          const [d2, s2] = factor();                       // implicit product: "kg m s^-2"
          d = d.mul(d2); s *= s2;
        } else if (kind === 'num') {
          throw new UnitSyntaxError(`Missing operator before number '${val}' in unit '${key}' (write m^2, not m2; s^-1, not s-1)`);
        } else {
          return [d, s];
        }
      }
    };
    const [dim, scale] = expr();
    if (pos !== toks.length) throw new UnitSyntaxError(`Unexpected trailing '${toks[pos][1]}' in unit '${key}'`);
    this._cache.set(key, [dim, scale]);
    return [dim, scale];
  }

  dimensionOf(unitStr) { return this.parseUnit(unitStr)[0]; }

  isKnown(unitStr) {
    try { this.parseUnit(unitStr); return true; } catch (e) { return false; }
  }

  describe(unitStr) {
    const [d, s] = this.parseUnit(unitStr);
    return `${d.label()} (x${s})`;
  }

  convert(value, fromUnit, toUnit) {
    const f = String(fromUnit).trim();
    const t = String(toUnit).trim();
    if (f !== t && TO_KELVIN[f] && FROM_KELVIN[t]) return FROM_KELVIN[t](TO_KELVIN[f](value));
    const [dimFrom, scaleFrom] = this.parseUnit(fromUnit);
    const [dimTo, scaleTo] = this.parseUnit(toUnit);
    if (!dimFrom.equals(dimTo)) {
      throw new Error(`Dimensional mismatch: cannot convert '${fromUnit}' [${dimFrom.label()}] to '${toUnit}' [${dimTo.label()}]`);
    }
    return (value * scaleFrom) / scaleTo;
  }

  /** [true, null] or [false, reason]. An unknown or malformed unit is reported incompatible, never dimensionless. */
  verifyCompatibility(unitA, unitB) {
    let dimA;
    let dimB;
    try {
      [dimA] = this.parseUnit(unitA);
      [dimB] = this.parseUnit(unitB);
    } catch (e) {
      return [false, e.message];
    }
    if (dimA.equals(dimB)) return [true, null];
    return [false, `Incompatible dimensions: '${unitA}' has [${dimA.label()}] vs '${unitB}' has [${dimB.label()}]`];
  }

  /** Dimensional homogeneity of an additive expression: every term must share one dimension. */
  checkSum(units) {
    if (!units.length) return [true, null];
    for (const u of units.slice(1)) {
      const [ok, why] = this.verifyCompatibility(units[0], u);
      if (!ok) return [false, why];
    }
    return [true, null];
  }
}
