/**
 * sfsa.autocomplete — Autocomplete & Model Gap-Filling Engine
 * ===========================================================
 * Autonomous gap detector and conceptual connection synthesizer for JavaScript.
 * Monitors model layers, detects missing variables, and auto-resolves gaps using rules.
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

export const GapType = Object.freeze({
  MISSING_PARAMETER: "MISSING_PARAMETER",
  UNCONNECTED_LAYER: "UNCONNECTED_LAYER",
  UNBOUND_EQUATION: "UNBOUND_EQUATION",
  INCOMPLETE_MATRIX: "INCOMPLETE_MATRIX",
});

export class Gap {
  constructor({ gapId, gapType, targetKey, requiredBy, description, context = {} }) {
    this.gapId = gapId;
    this.gapType = gapType;
    this.targetKey = targetKey;
    this.requiredBy = requiredBy;
    this.description = description;
    this.context = context;
  }
}

export class ConnectionCandidate {
  constructor({
    ruleName,
    targetKey,
    derivedValue,
    confidence = 1.0,
    sourceDependencies = [],
    derivationNotes = "",
  }) {
    this.ruleName = ruleName;
    this.targetKey = targetKey;
    this.derivedValue = derivedValue;
    this.confidence = confidence;
    this.sourceDependencies = sourceDependencies;
    this.derivationNotes = derivationNotes;
  }
}

export class AutocompleteEngine {
  constructor() {
    this._rules = new Map();
    this._history = [];
  }

  registerRule(ruleName, resolver) {
    this._rules.set(ruleName, resolver);
  }

  detectGaps(currentState, requiredSchema = {}) {
    const gaps = [];
    for (const [key, requirement] of Object.entries(requiredSchema)) {
      if (currentState[key] === undefined || currentState[key] === null) {
        gaps.push(
          new Gap({
            gapId: `gap_${key}`,
            gapType: GapType.MISSING_PARAMETER,
            targetKey: key,
            requiredBy: "schema_definition",
            description: `Missing required parameter '${key}' (${requirement})`,
            context: { requirement, currentKeys: Object.keys(currentState) },
          })
        );
      }
    }
    return gaps;
  }

  suggestConnections(gaps, availableState) {
    const candidates = [];
    for (const gap of gaps) {
      for (const [ruleName, ruleFn] of this._rules.entries()) {
        const context = { ...availableState, _targetGap: gap };
        try {
          const candidate = ruleFn(context);
          if (candidate && candidate.targetKey === gap.targetKey) {
            candidates.push(candidate);
          }
        } catch {
          // Ignore individual rule failure
        }
      }
    }
    candidates.sort((a, b) => b.confidence - a.confidence);
    return candidates;
  }

  autoFill(currentState, requiredSchema, minConfidence = 0.70) {
    const updatedState = { ...currentState };
    const gaps = this.detectGaps(updatedState, requiredSchema);
    const appliedCandidates = [];

    if (gaps.length === 0) {
      return { updatedState, appliedCandidates };
    }

    const candidates = this.suggestConnections(gaps, updatedState);
    const filledKeys = new Set();

    for (const cand of candidates) {
      if (!filledKeys.has(cand.targetKey) && cand.confidence >= minConfidence) {
        updatedState[cand.targetKey] = cand.derivedValue;
        filledKeys.add(cand.targetKey);
        appliedCandidates.push(cand);
        this._history.push({
          targetKey: cand.targetKey,
          rule: cand.ruleName,
          confidence: cand.confidence,
        });
      }
    }

    return { updatedState, appliedCandidates };
  }

  get resolutionHistory() {
    return [...this._history];
  }
}
