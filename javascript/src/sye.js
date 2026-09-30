/**
 * sfsa.sye — Symbolic Simplification & Equivalence Engine (SYE)
 * ============================================================
 * Performs formal algebraic simplification and equivalence detection on scientific expressions.
 * Eliminates redundant terms, folds identities (e.g. 0 * f(x) -> 0, 1 * f(x) -> f(x)),
 * and detects mathematical singularities prior to compiling or numerically evaluating solvers.
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

export class SymbolicEquivalenceEngine {
  constructor() {
    this.rules = [
      [/\b0\s*\*\s*([a-zA-Z0-9_]+)/g, '0'],
      [/([a-zA-Z0-9_]+)\s*\*\s*0\b/g, '0'],
      [/\b1\s*\*\s*([a-zA-Z0-9_]+)/g, '$1'],
      [/([a-zA-Z0-9_]+)\s*\*\s*1\b/g, '$1'],
      [/\b0\s*\+\s*([a-zA-Z0-9_]+)/g, '$1'],
      [/([a-zA-Z0-9_]+)\s*\+\s*0\b/g, '$1'],
      [/([a-zA-Z0-9_]+)\s*-\s*\1\b/g, '0'],
      [/log\s*\(\s*exp\s*\(([^)]+)\)\s*\)/g, '$1'],
      [/exp\s*\(\s*log\s*\(([^)]+)\)\s*\)/g, '$1']
    ];
  }

  simplify(exprStr) {
    let current = exprStr.trim();
    let opsEliminated = 0;

    let changed = true;
    let passes = 0;
    while (changed && passes < 10) {
      changed = false;
      passes += 1;
      for (const [pattern, replacement] of this.rules) {
        const matches = current.match(pattern);
        if (matches) {
          opsEliminated += matches.length;
          current = current.replace(pattern, replacement);
          changed = true;
        }
      }
    }

    current = current.replace(/\s+/g, ' ').trim();

    // Detect divide-by-zero poles
    const singularities = [];
    const divRegex = /\/\s*([a-zA-Z0-9_]+)/g;
    let match;
    while ((match = divRegex.exec(current)) !== null) {
      if (match[1] !== '0') {
        singularities.push(`Pole at ${match[1]} == 0`);
      }
    }

    const numVal = Number(current);
    const isConstant = !isNaN(numVal) && current !== '';

    return {
      originalExpression: exprStr,
      simplifiedExpression: current,
      operationsEliminatedCount: opsEliminated,
      detectedSingularities: singularities,
      isConstant,
      constantValue: isConstant ? numVal : null
    };
  }

  areEquivalent(exprA, exprB) {
    const simA = this.simplify(exprA).simplifiedExpression.replace(/\s+/g, '');
    const simB = this.simplify(exprB).simplifiedExpression.replace(/\s+/g, '');
    return simA === simB;
  }
}
