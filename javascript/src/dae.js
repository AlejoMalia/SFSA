/**
 * sfsa.dae — Data Assimilation & Calibration Engine (DAE)
 * ======================================================
 * Solves the scientific inverse problem: calibrates unknown theoretical parameters by assimilating
 * empirical lab observations, sensor logs, or benchmark tables without brute-force grid searches.
 * Applies bounded coordinate descent optimization to minimize discrepancy against real data.
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

export class DataAssimilationEngine {
  constructor(tolerance = 1e-4, maxIterations = 100) {
    this.tolerance = tolerance;
    this.maxIterations = maxIterations;
  }

  calibrate({
    experimentalData,
    modelFn,
    initialParams,
    targetKey = 'observed',
    paramBounds = null
  }) {
    const params = { ...initialParams };
    const bounds = paramBounds || {};

    const computeRmse = (currParams) => {
      const residuals = [];
      for (const row of experimentalData) {
        const inputs = {};
        for (const [k, v] of Object.entries(row)) {
          if (k !== targetKey) inputs[k] = v;
        }
        const yTrue = row[targetKey];
        const yPred = modelFn(inputs, currParams);
        residuals.push(yPred - yTrue);
      }
      const mse = residuals.reduce((sum, r) => sum + r * r, 0) / residuals.length;
      return { rmse: Math.sqrt(mse), residuals };
    };

    const initialEval = computeRmse(params);
    let bestRmse = initialEval.rmse;
    let bestParams = { ...params };
    let bestResiduals = initialEval.residuals;

    let iterations = 0;
    let converged = false;

    while (iterations < this.maxIterations) {
      iterations += 1;
      let improved = false;

      for (const pName of Object.keys(params)) {
        const currentVal = bestParams[pName];
        const step = Math.max(Math.abs(currentVal) * 0.05, 0.01);

        for (const delta of [step, -step, step * 0.2, -step * 0.2]) {
          let testVal = currentVal + delta;
          if (bounds[pName]) {
            const [lo, hi] = bounds[pName];
            testVal = Math.max(lo, Math.min(hi, testVal));
          }

          const testParams = { ...bestParams, [pName]: testVal };
          const { rmse, residuals } = computeRmse(testParams);

          if (rmse < bestRmse - this.tolerance) {
            bestRmse = rmse;
            bestParams = testParams;
            bestResiduals = residuals;
            improved = true;
            break;
          }
        }
      }

      if (!improved) {
        converged = true;
        break;
      }
    }

    // Compute R-squared
    const yValues = experimentalData.map(r => r[targetKey]);
    const yMean = yValues.reduce((a, b) => a + b, 0) / yValues.length;
    const ssTot = yValues.reduce((sum, y) => sum + (y - yMean) ** 2, 0);
    const ssRes = bestResiduals.reduce((sum, r) => sum + r * r, 0);
    const rSquared = ssTot > 1e-12 ? Math.max(0.0, 1.0 - (ssRes / ssTot)) : 1.0;

    return {
      calibratedParameters: bestParams,
      initialRmse: initialEval.rmse,
      finalRmse: bestRmse,
      rSquared,
      iterationsUsed: iterations,
      converged,
      residuals: bestResiduals
    };
  }
}
