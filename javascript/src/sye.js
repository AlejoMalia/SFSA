/**
 * sfsa.sye — Symbolic Simplification & Equivalence Engine (SYE)
 * ============================================================
 * Formal algebraic simplification and equivalence detection on scientific expressions.
 *
 * Expressions are parsed into a restricted syntax tree (+ - * / ** ^, unary signs, numbers, names and a
 * whitelist of one-argument functions; nothing else is ever evaluated) and handled structurally, not with
 * text substitution. Identities that need real algebra (log(v1/v0) + log(v2/v1) == log(v2/v0)) are decided
 * with a seeded numerical check on many points of the declared domain (positive reals by default). The
 * result says which method decided it: only 'syntactic' is a proof; 'numeric' is strong evidence.
 * (The Python package additionally uses sympy for a symbolic proof when it is installed.)
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

const FUNCS = {
  log: Math.log, ln: Math.log, log10: Math.log10, log2: Math.log2, exp: Math.exp, sqrt: Math.sqrt,
  sin: Math.sin, cos: Math.cos, tan: Math.tan, asin: Math.asin, acos: Math.acos, atan: Math.atan,
  sinh: Math.sinh, cosh: Math.cosh, tanh: Math.tanh, abs: Math.abs
};
const CONSTS = { pi: Math.PI, e: Math.E };

const num = (v) => ({ t: 'num', v });
const name = (n) => ({ t: 'name', n });
const bin = (op, a, b) => ({ t: 'bin', op, a, b });
const neg = (a) => ({ t: 'neg', a });
const call = (f, a) => ({ t: 'call', f, a });

function tokenize(src) {
  const re = /\s*(?:(\d+\.?\d*(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?)|([A-Za-z_][A-Za-z_0-9]*)|(\*\*|\^|[-+*/()]))/y;
  const out = [];
  let pos = 0;
  const s = src.trim();
  while (pos < s.length) {
    re.lastIndex = pos;
    const m = re.exec(s);
    if (!m || re.lastIndex === pos) throw new Error(`Cannot parse expression '${src}': unexpected '${s[pos]}'`);
    if (m[1] !== undefined) out.push({ k: 'num', v: Number(m[1]) });
    else if (m[2] !== undefined) out.push({ k: 'name', v: m[2] });
    else out.push({ k: 'op', v: m[3] === '^' ? '**' : m[3] });
    pos = re.lastIndex;
  }
  return out;
}

/** Parse into a validated tree; anything outside the whitelist throws. */
export function parseExpression(src) {
  if (typeof src !== 'string' || src.trim() === '') throw new Error('Empty expression');
  const toks = tokenize(src);
  let i = 0;
  const peek = () => toks[i];
  const isOp = (v) => peek() && peek().k === 'op' && peek().v === v;
  const fail = (msg) => { throw new Error(`Cannot parse expression '${src}': ${msg}`); };
  const primary = () => {
    const t = toks[i++];
    if (!t) fail('unexpected end');
    if (t.k === 'num') return num(t.v);
    if (t.k === 'name') {
      if (isOp('(')) {
        if (!Object.prototype.hasOwnProperty.call(FUNCS, t.v)) fail(`function '${t.v}' is not allowed`);
        i++;
        const a = additive();
        if (!isOp(')')) fail("expected ')' (only one-argument calls are allowed)");
        i++;
        return call(t.v, a);
      }
      return name(t.v);
    }
    if (t.v === '(') {
      const a = additive();
      if (!isOp(')')) fail("expected ')'");
      i++;
      return a;
    }
    return fail(`unexpected '${t.v}'`);
  };
  const power = () => {                       // right-associative, binds tighter than unary minus on its left
    const base = primary();
    if (isOp('**')) { i++; return bin('**', base, unary()); }
    return base;
  };
  const unary = () => {
    if (isOp('-')) { i++; return neg(unary()); }
    if (isOp('+')) { i++; return unary(); }
    return power();
  };
  const multiplicative = () => {
    let a = unary();
    while (isOp('*') || isOp('/')) { const op = toks[i++].v; a = bin(op, a, unary()); }
    return a;
  };
  function additive() {
    let a = multiplicative();
    while (isOp('+') || isOp('-')) { const op = toks[i++].v; a = bin(op, a, multiplicative()); }
    return a;
  }
  const tree = additive();
  if (i !== toks.length) fail(`unexpected '${toks[i].v}'`);
  return tree;
}

const PREC = { '+': 1, '-': 1, '*': 2, '/': 2, neg: 3, '**': 4 };

export function unparse(n, parent = 0, right = false) {
  let s;
  let p;
  if (n.t === 'num') {
    return Number.isInteger(n.v) ? String(n.v) : String(n.v);
  }
  if (n.t === 'name') return n.n;
  if (n.t === 'call') return `${n.f}(${unparse(n.a)})`;
  if (n.t === 'neg') {
    p = PREC.neg;
    s = `-${unparse(n.a, p)}`;
  } else {
    p = PREC[n.op];
    const l = unparse(n.a, p, false);
    const r = unparse(n.b, p, true);
    s = `${l} ${n.op} ${r}`;
  }
  const needs = p < parent || (p === parent && right && n.t === 'bin' && n.op !== '**' && (n.op === '-' || n.op === '/'));
  return needs ? `(${s})` : s;
}

const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const isConst = (n, v = null) => n.t === 'num' && (v === null || n.v === v);

function countOps(n) {
  if (n.t === 'num' || n.t === 'name') return 0;
  if (n.t === 'neg' || n.t === 'call') return 1 + countOps(n.a);
  return 1 + countOps(n.a) + countOps(n.b);
}

function freeNames(n, acc = new Set()) {
  if (n.t === 'name' && !(n.n in CONSTS)) acc.add(n.n);
  else if (n.t === 'neg' || n.t === 'call') freeNames(n.a, acc);
  else if (n.t === 'bin') { freeNames(n.a, acc); freeNames(n.b, acc); }
  return acc;
}

/** Evaluate a validated tree; returns NaN/Infinity where the expression is undefined over the reals. */
function evaluate(n, env) {
  switch (n.t) {
    case 'num': return n.v;
    case 'name':
      if (n.n in env) return env[n.n];
      if (n.n in CONSTS) return CONSTS[n.n];
      return NaN;
    case 'neg': return -evaluate(n.a, env);
    case 'call': return FUNCS[n.f](evaluate(n.a, env));
    default: {
      const a = evaluate(n.a, env);
      const b = evaluate(n.b, env);
      if (n.op === '+') return a + b;
      if (n.op === '-') return a - b;
      if (n.op === '*') return a * b;
      if (n.op === '/') return b === 0 ? NaN : a / b;
      return a ** b;
    }
  }
}

function mulberry32(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export class SymbolicEquivalenceEngine {
  constructor({ nPoints = 64, relTol = 1e-9, seed = 20260101 } = {}) {
    this.nPoints = nPoints;
    this.relTol = relTol;
    this.seed = seed;
  }

  _simp(n, restr) {
    if (n.t === 'neg') {
      const a = this._simp(n.a, restr);
      if (a.t === 'num') return num(-a.v);
      if (a.t === 'neg') return a.a;
      return neg(a);
    }
    if (n.t === 'call') {
      const a = this._simp(n.a, restr);
      if (a.t === 'num') {
        const v = FUNCS[n.f](a.v);
        if (Number.isFinite(v)) return num(v);
      }
      if ((n.f === 'log' || n.f === 'ln') && a.t === 'call' && a.f === 'exp') return a.a;
      if (n.f === 'exp' && a.t === 'call' && (a.f === 'log' || a.f === 'ln')) {
        restr.add(`${unparse(a.a)} > 0`);
        return a.a;
      }
      return call(n.f, a);
    }
    if (n.t !== 'bin') return n;
    const l = this._simp(n.a, restr);
    const r = this._simp(n.b, restr);
    const op = n.op;
    if (l.t === 'num' && r.t === 'num') {
      const v = evaluate(bin(op, l, r), {});
      if (Number.isFinite(v)) return num(v);
      return bin(op, l, r);
    }
    if (op === '+') {
      if (isConst(l, 0)) return r;
      if (isConst(r, 0)) return l;
    } else if (op === '-') {
      if (isConst(r, 0)) return l;
      if (isConst(l, 0)) return neg(r);
      if (same(l, r)) return num(0);
    } else if (op === '*') {
      if (isConst(l, 0) || isConst(r, 0)) return num(0);
      if (isConst(l, 1)) return r;
      if (isConst(r, 1)) return l;
    } else if (op === '/') {
      if (isConst(r, 1)) return l;
      if (same(l, r)) { restr.add(`${unparse(l)} != 0`); return num(1); }
      if (isConst(l, 0)) { restr.add(`${unparse(r)} != 0`); return num(0); }
    } else if (op === '**') {
      if (isConst(r, 1)) return l;
      if (isConst(r, 0) || isConst(l, 1)) return num(1);
    }
    return bin(op, l, r);
  }

  _poles(n, out = []) {
    let den = null;
    if (n.t === 'bin' && n.op === '/') den = n.b;
    else if (n.t === 'bin' && n.op === '**' && n.b.t === 'num' && n.b.v < 0) den = n.a;
    else if (n.t === 'bin' && n.op === '**' && n.b.t === 'neg' && n.b.a.t === 'num') den = n.a;
    if (den) {
      if (den.t === 'num') {
        if (den.v === 0 && !out.includes('Division by the constant 0')) out.push('Division by the constant 0');
      } else {
        const msg = `Pole at ${unparse(den)} == 0`;
        if (!out.includes(msg)) out.push(msg);
      }
    }
    if (n.t === 'neg' || n.t === 'call') this._poles(n.a, out);
    if (n.t === 'bin') { this._poles(n.a, out); this._poles(n.b, out); }
    return out;
  }

  _domain(n, out = new Set()) {
    if (n.t === 'call') {
      const a = unparse(n.a);
      if (['log', 'ln', 'log10', 'log2'].includes(n.f)) out.add(`${a} > 0`);
      else if (n.f === 'sqrt') out.add(`${a} >= 0`);
      else if (n.f === 'asin' || n.f === 'acos') out.add(`-1 <= ${a} <= 1`);
      this._domain(n.a, out);
    } else if (n.t === 'neg') this._domain(n.a, out);
    else if (n.t === 'bin') { this._domain(n.a, out); this._domain(n.b, out); }
    return out;
  }

  simplify(exprStr) {
    const original = parseExpression(exprStr);
    const restr = new Set();
    let simplified = this._simp(original, restr);
    for (let k = 0; k < 4; k++) {
      const again = this._simp(simplified, restr);
      if (same(again, simplified)) break;
      simplified = again;
    }
    const isConstant = simplified.t === 'num';
    return {
      originalExpression: exprStr,
      simplifiedExpression: unparse(simplified),
      operationsEliminatedCount: Math.max(countOps(original) - countOps(simplified), 0),
      detectedSingularities: this._poles(simplified),
      isConstant,
      constantValue: isConstant ? simplified.v : null,
      domainRestrictions: [...new Set([...restr, ...this._domain(simplified)])].sort()
    };
  }

  /**
   * Decide whether two expressions are equal and report how: {equivalent, method, proven, domain, validPoints,
   * maxError, counterexample, note}. domain 'positive' (default) tests positive reals; 'real' also samples
   * negative values and requires both sides to be defined on exactly the same points.
   */
  checkEquivalence(exprA, exprB, domain = 'positive') {
    if (domain !== 'positive' && domain !== 'real') throw new Error("domain must be 'positive' or 'real'");
    const a = parseExpression(exprA);
    const b = parseExpression(exprB);
    if (this.simplify(exprA).simplifiedExpression === this.simplify(exprB).simplifiedExpression) {
      return { equivalent: true, method: 'syntactic', proven: true, domain, validPoints: 0, maxError: 0, counterexample: null,
        note: 'identical after simplification' };
    }
    const names = [...new Set([...freeNames(a), ...freeNames(b)])].sort();
    const rnd = mulberry32(this.seed);
    let valid = 0;
    let worst = 0;
    for (let i = 0; i < this.nPoints; i++) {
      const env = {};
      for (const nm of names) {
        if (i === 0) env[nm] = 1;
        else if (i === 1) env[nm] = 2;
        else {
          const mag = 10 ** (-1.3 + 2.6 * rnd());
          env[nm] = domain === 'positive' || rnd() < 0.5 ? mag : -mag;
        }
      }
      const va = evaluate(a, env);
      const vb = evaluate(b, env);
      const okA = Number.isFinite(va);
      const okB = Number.isFinite(vb);
      if (!okA && !okB) continue;
      if (okA !== okB) {
        if (domain === 'real') {
          return { equivalent: false, method: 'numeric', proven: false, domain, validPoints: valid, maxError: worst,
            counterexample: env, note: 'defined on different domains at this point' };
        }
        continue;
      }
      const err = Math.abs(va - vb) / Math.max(1, Math.abs(va), Math.abs(vb));
      valid += 1;
      worst = Math.max(worst, err);
      if (err > this.relTol) {
        return { equivalent: false, method: 'numeric', proven: false, domain, validPoints: valid, maxError: worst,
          counterexample: env, note: `values differ: ${va} vs ${vb}` };
      }
    }
    if (valid < Math.max(8, Math.floor(this.nPoints / 4))) {
      return { equivalent: false, method: 'inconclusive', proven: false, domain, validPoints: valid, maxError: worst,
        counterexample: null, note: 'too few points where both expressions are defined' };
    }
    return { equivalent: true, method: 'numeric', proven: false, domain, validPoints: valid, maxError: worst, counterexample: null,
      note: `agree on ${valid} points (max rel. error ${worst.toExponential(2)}); strong evidence, not a proof` };
  }

  areEquivalent(exprA, exprB, domain = 'positive') {
    return this.checkEquivalence(exprA, exprB, domain).equivalent;
  }
}
