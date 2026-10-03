import assert from 'assert';
import { UnitDimensionalEngine, DimensionVector, UnknownUnitError, UnitSyntaxError } from '../src/ude.js';
import { SymbolicEquivalenceEngine } from '../src/sye.js';
import { AdaptiveSamplingEngine } from '../src/asg.js';
import { DiscrepancyIntelligenceEngine, DiscrepancyCause } from '../src/die.js';

console.log('Running SFSA audit-fix regression suite (UDE, SYE, ASG, DIE)...');
const close = (a, b, t = 1e-9) => Math.abs(a - b) <= t * Math.max(1, Math.abs(a), Math.abs(b));

// ---- UDE
const ude = new UnitDimensionalEngine();
for (const [expr, dim, scale] of [
  ['1/year', { time: -1 }, 1 / 31557600], ['m/s', { length: 1, time: -1 }, 1], ['month', { time: 1 }, 31557600 / 12],
  ['km/h', { length: 1, time: -1 }, 1000 / 3600], ['kg*m/s^2', { mass: 1, length: 1, time: -2 }, 1],
  ['J/(kg*K)', { length: 2, time: -2, temp: -1 }, 1], ['kWh', { mass: 1, length: 2, time: -2 }, 3.6e6],
  ['mW', { mass: 1, length: 2, time: -3 }, 1e-3], ['MW', { mass: 1, length: 2, time: -3 }, 1e6],
  ['Pa^(1/2)', { mass: 0.5, length: -0.5, time: -1 }, 1]
]) {
  const [d, s] = ude.parseUnit(expr);
  assert.ok(d.equals(new DimensionVector(dim)), `dimension of ${expr}`);
  assert.ok(close(s, scale), `scale of ${expr}`);
}
for (const bad of ['furlongz', 'kg*bananas', 'xyz']) {
  assert.throws(() => ude.parseUnit(bad), UnknownUnitError);
  assert.strictEqual(ude.verifyCompatibility(bad, 'm')[0], false);
}
assert.strictEqual(ude.verifyCompatibility('bananas', 'dimensionless')[0], false);
for (const bad of ['m2', 's-1', 'm/', '(m', '']) assert.throws(() => ude.parseUnit(bad), UnitSyntaxError);
assert.ok(close(ude.convert(36, 'km/h', 'm/s'), 10) && close(ude.convert(1, 'year', 'month'), 12));
assert.ok(close(ude.convert(25, 'degC', 'K'), 298.15) && close(ude.convert(100, 'degC', 'degF'), 212));
assert.ok(close(ude.convert(200000, 'pa', 'bar'), 2));
assert.throws(() => ude.convert(1, 'm/s', 'm'), /mismatch/);
assert.strictEqual(ude.checkSum(['J', 'N*m'])[0], true);
assert.strictEqual(ude.checkSum(['J', 'W'])[0], false);

// ---- SYE
const sye = new SymbolicEquivalenceEngine();
assert.ok(sye.areEquivalent('log(v1/v0) + log(v2/v1)', 'log(v2/v0)'));
for (const [a, b] of [['(a + b)^2', 'a^2 + 2*a*b + b^2'], ['exp(a + b)', 'exp(a)*exp(b)'], ['(x^2 - 1)/(x - 1)', 'x + 1'],
  ['sin(t)^2 + cos(t)^2', '1'], ['log(x^3)', '3*log(x)']]) assert.ok(sye.areEquivalent(a, b), `${a} == ${b}`);
for (const [a, b] of [['x + 1', 'x + 2'], ['log(a*b)', 'log(a)*log(b)'], ['(a + b)^2', 'a^2 + b^2'], ['sin(x)', 'x']]) {
  const r = sye.checkEquivalence(a, b);
  assert.ok(!r.equivalent && r.counterexample !== null, `${a} != ${b}`);
}
assert.strictEqual(sye.checkEquivalence('log(x*x)', '2*log(x)', 'real').equivalent, false);
assert.strictEqual(sye.simplify('x * 0.5').simplifiedExpression.replace(/ /g, ''), 'x*0.5');   // old regex produced "0.5"
assert.strictEqual(sye.areEquivalent('x * 0.5', '0.5'), false);
assert.strictEqual(sye.simplify('0 * x + 1 * y + 0').simplifiedExpression, 'y');
assert.ok(sye.simplify('0 * x + 1 * y + 0').operationsEliminatedCount >= 2);
assert.ok(sye.simplify('a / (b - c) + 1 / x').detectedSingularities.includes('Pole at b - c == 0'));
assert.ok(sye.simplify('x / x').domainRestrictions.includes('x != 0'));
for (const bad of ["__import__('os')", 'x.y', '[1]', 'f(x)', 'log(x, 2)', '']) assert.throws(() => sye.simplify(bad));

// ---- ASG
{
  const grid = [{ x: 0.5, y: 0.5 }, { x: 0.52, y: 0.5 }];
  assert.strictEqual(new AdaptiveSamplingEngine(0.1).filterGrid(grid, null, () => 0.01).length, 1);
  assert.strictEqual(new AdaptiveSamplingEngine(0.1).filterGrid(grid, null, () => 0.9).length, 2);
  assert.strictEqual(new AdaptiveSamplingEngine(0.1, 0.6, { uncertaintyEstimator: () => 0.9 }).filterGrid(grid).length, 2);
  const eng = new AdaptiveSamplingEngine(0.001);
  eng.recordEvaluation({ x: 0.0 }, 1.0);
  const chosen = eng.filterGrid([{ x: 0.0 }, { x: 0.01 }, { x: 0.5 }, { x: 1.0 }], 2);
  assert.strictEqual(chosen[0].x, 1.0);
  assert.strictEqual(new AdaptiveSamplingEngine().filterGrid(grid, 0).length, 0);
  assert.throws(() => new AdaptiveSamplingEngine().filterGrid(grid, -1));
  const e2 = new AdaptiveSamplingEngine();
  e2.filterGrid([{ x: 0 }, { x: 1 }]);
  assert.ok(e2.pointValues.every(Number.isNaN));
}

// ---- DIE
{
  const die = new DiscrepancyIntelligenceEngine();
  const euler = (h) => { let y = 1; for (let i = 0; i < Math.round(1 / h); i++) y += h * y; return y; };
  assert.strictEqual(die.analyze('h=.1', euler(0.1), 'h=.05', euler(0.05), null, { sameModel: true }).probableCause,
    DiscrepancyCause.NUMERICAL_DISCRETIZATION);
  assert.strictEqual(die.analyze('e', 2.5937, 'r', 2.7183, null, { discretizationError: 0.2 }).probableCause,
    DiscrepancyCause.NUMERICAL_DISCRETIZATION);
  assert.strictEqual(die.analyze('e', 2.5937, 'r', 2.7183, null, { discretizationError: 0.01 }).probableCause,
    DiscrepancyCause.MODELING_ASSUMPTION);
  const r = die.analyzeRefinement('h=.01', euler(0.01), 'h=.005', euler(0.005), 1);
  assert.ok(Math.abs(r.reconciledValue - Math.E) < 1e-3);
  assert.strictEqual(die.analyze('a', 100, 'b', 100.5).probableCause, DiscrepancyCause.NUMERICAL_TOLERANCE);
  assert.strictEqual(die.analyze('a', 100, 'b', 250, () => 245).probableCause, DiscrepancyCause.REGIME_BREAKDOWN);
  assert.throws(() => DiscrepancyIntelligenceEngine.richardson(1, 1.1, 0));
}

console.log('✅ AUDIT FIXES VERIFIED IN JAVASCRIPT (UDE, SYE, ASG, DIE)');
