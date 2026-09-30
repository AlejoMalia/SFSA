/**
 * sfsa.ore — Orchestration & Routing Engine (ORE)
 * ==============================================
 * The meta-brain of the SFSA framework. Analyzes query characteristics, problem dimensionality,
 * available time budget (TBE), and required precision to compose and dynamically route
 * the minimal sufficient pipeline of scientific engines, preventing architectural compute bloat.
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

export const QueryArchetype = Object.freeze({
  EXPLORATORY_SWEEP: 'EXPLORATORY_SWEEP',
  HIGH_PRECISION_SOLVE: 'HIGH_PRECISION_SOLVE',
  INVERSE_CALIBRATION: 'INVERSE_CALIBRATION',
  DAG_PROPAGATION: 'DAG_PROPAGATION',
  VERIFICATION_AUDIT: 'VERIFICATION_AUDIT'
});

export class OrchestrationRoutingEngine {
  constructor() {
    this.routingHistory = [];
  }

  planPipeline({
    queryArchetype = QueryArchetype.HIGH_PRECISION_SOLVE,
    inputCardinality = 1,
    parameterDim = 2,
    budgetRemainingSeconds = 60.0,
    tolerance = 0.05
  } = {}) {
    const engines = [];
    const rationaleParts = [];
    let estReduction = 0.0;
    let suggestedFidelity = 'ADAPTIVE';

    if (queryArchetype === QueryArchetype.EXPLORATORY_SWEEP) {
      if (inputCardinality > 100) {
        engines.push('CQE');
        rationaleParts.push('Cluster queries into centroids');
        estReduction += 40.0;
      }
      if (parameterDim >= 4) {
        engines.push('SRA');
        rationaleParts.push(`Prune insensitive dimensions from ${parameterDim}D`);
        estReduction += 25.0;
      }
      engines.push('ASG', 'CAE', 'AMF', 'MATE');
      rationaleParts.push('Filter informative points (ASG), cut unviable domains (CAE), and route multi-fidelity (AMF)');
      estReduction = Math.min(95.0, estReduction + 25.0);
      suggestedFidelity = 'CHEAP_FIRST';
    } else if (queryArchetype === QueryArchetype.HIGH_PRECISION_SOLVE) {
      engines.push('MRE', 'CAE', 'MATE', 'TRIADA', 'UQE');
      rationaleParts.push('Check model validity (MRE), bound cuts (CAE/MATE), closed-form T2 (TRIADA), and 1-pass uncertainty (UQE)');
      estReduction = 45.0;
      suggestedFidelity = 'HIGH';
    } else if (queryArchetype === QueryArchetype.INVERSE_CALIBRATION) {
      engines.push('DAE', 'SME', 'RTE', 'LDR');
      rationaleParts.push('Assimilate observations (DAE), fit surrogate (SME), test condition stability (RTE), store baseline (LDR)');
      estReduction = 85.0;
      suggestedFidelity = 'ADAPTIVE';
    } else if (queryArchetype === QueryArchetype.DAG_PROPAGATION) {
      engines.push('FLN', 'CPE', 'MATE', 'AIE');
      rationaleParts.push('Propagate deltas across layers (FLN), assess reuse (CPE), check invariants (MATE/AIE)');
      estReduction = 75.0;
      suggestedFidelity = 'ADAPTIVE';
    } else if (queryArchetype === QueryArchetype.VERIFICATION_AUDIT) {
      engines.push('UDE', 'TRIADA', 'RTE', 'RME', 'XXE');
      rationaleParts.push('Dimensional check (UDE), physical conservation (TRIADA), stress test (RTE), and audit certificate (RME/XXE)');
      estReduction = 50.0;
      suggestedFidelity = 'HIGH';
    }

    const plan = {
      queryArchetype,
      activeEngineSequence: engines,
      estimatedComputeReductionPct: estReduction,
      rationale: rationaleParts.join(' -> '),
      earlyExitAllowed: true,
      suggestedFidelity
    };

    this.routingHistory.push(plan);
    return plan;
  }
}
