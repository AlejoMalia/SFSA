/**
 * sfsa.mre — Model Risk & Validity Engine (MRE)
 * ============================================
 * Audits model epistemic validity and extrapolation safety prior to calculation.
 * Monitors whether candidate inputs exceed physical validity envelopes, computes
 * extrapolation risk scores, assesses cumulative assumption fragility (from AIE),
 * and issues binding recommendations: COMPUTE_SAFE, CAUTION_EXTRAPOLATION, or ABORT_INVALID_REGIME.
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

export class ModelRiskReport {
  constructor({
    isSafe,
    riskScore,
    verdict,
    extrapolationParameters = [],
    maxExtrapolationRatio = 0.0,
    warnings = []
  }) {
    this.isSafe = isSafe;
    this.riskScore = riskScore;
    this.verdict = verdict;
    this.extrapolationParameters = extrapolationParameters;
    this.maxExtrapolationRatio = maxExtrapolationRatio;
    this.warnings = warnings;
  }
}

export class ModelRiskEngine {
  constructor({ extrapolationThreshold = 0.20 } = {}) {
    this.extrapolationThreshold = extrapolationThreshold;
    this.validityEnvelopes = new Map();
    this.hardLimits = new Map();
  }

  registerEnvelope(parameterName, safeMin, safeMax, hardMin = null, hardMax = null) {
    this.validityEnvelopes.set(parameterName, [safeMin, safeMax]);
    if (hardMin !== null || hardMax !== null) {
      this.hardLimits.set(parameterName, [
        hardMin !== null ? hardMin : -Infinity,
        hardMax !== null ? hardMax : Infinity
      ]);
    }
  }

  assessRisk(inputs) {
    const warnings = [];
    const extrapolatedParams = [];
    let maxRatio = 0.0;
    let abortTriggered = false;

    for (const [pName, val] of Object.entries(inputs)) {
      // Check hard limits first
      if (this.hardLimits.has(pName)) {
        const [hMin, hMax] = this.hardLimits.get(pName);
        if (val < hMin || val > hMax) {
          abortTriggered = true;
          warnings.push(`Hard physical limit violated for '${pName}': ${val} not in [${hMin}, ${hMax}]`);
        }
      }

      // Check safe envelopes
      if (this.validityEnvelopes.has(pName)) {
        const [sMin, sMax] = this.validityEnvelopes.get(pName);
        const span = Math.max(Math.abs(sMax - sMin), 1e-6);
        if (val < sMin) {
          const ratio = (sMin - val) / span;
          maxRatio = Math.max(maxRatio, ratio);
          extrapolatedParams.push(pName);
          warnings.push(`Under-range extrapolation on '${pName}' by ${(ratio * 100).toFixed(1)}%`);
        } else if (val > sMax) {
          const ratio = (val - sMax) / span;
          maxRatio = Math.max(maxRatio, ratio);
          extrapolatedParams.push(pName);
          warnings.push(`Over-range extrapolation on '${pName}' by ${(ratio * 100).toFixed(1)}%`);
        }
      }
    }

    const riskScore = Math.min(1.0, maxRatio);
    let verdict = 'COMPUTE_SAFE';
    let isSafe = true;

    if (abortTriggered || riskScore > 0.5) {
      verdict = 'ABORT_INVALID_REGIME';
      isSafe = false;
    } else if (riskScore > this.extrapolationThreshold) {
      verdict = 'CAUTION_EXTRAPOLATION';
      isSafe = true;
    } else {
      verdict = 'COMPUTE_SAFE';
      isSafe = true;
    }

    return new ModelRiskReport({
      isSafe,
      riskScore,
      verdict,
      extrapolationParameters: extrapolatedParams,
      maxExtrapolationRatio: maxRatio,
      warnings
    });
  }
}
