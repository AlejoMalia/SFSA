/**
 * sfsa.ele — Experiment Loop Engine (ELE / Lab-in-the-Loop)
 * ========================================================
 * Closes the scientific discovery loop between theoretical simulations and physical laboratory data.
 * Iterates the complete scientific cycle:
 *     Theoretical Model -> Prediction -> Experiment Design (DoE) -> Lab Measurement (LDR) ->
 *     Data Assimilation (DAE) -> Updated State & Residual Uncertainty.
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

export class ExperimentProposal {
  constructor({
    experimentId,
    targetParameters,
    predictedTheoreticalOutput,
    expectedInformationGain,
    rationale
  }) {
    this.experimentId = experimentId;
    this.targetParameters = targetParameters;
    this.predictedTheoreticalOutput = predictedTheoreticalOutput;
    this.expectedInformationGain = expectedInformationGain;
    this.rationale = rationale;
  }
}

export class LoopIterationResult {
  constructor({
    iterationIndex,
    proposal,
    measuredLabValue,
    theoreticalPrediction,
    discrepancyDelta,
    recalibratedParameters,
    residualRmse
  }) {
    this.iterationIndex = iterationIndex;
    this.proposal = proposal;
    this.measuredLabValue = measuredLabValue;
    this.theoreticalPrediction = theoreticalPrediction;
    this.discrepancyDelta = discrepancyDelta;
    this.recalibratedParameters = recalibratedParameters;
    this.residualRmse = residualRmse;
  }
}

export class ExperimentLoopEngine {
  constructor() {
    this.iterations = [];
  }

  proposeNextExperiment(candidateSpace, theoryModel, uncertaintyEstimator) {
    let bestCandidate = null;
    let maxInfo = -1.0;
    let bestPred = 0.0;

    for (const cand of candidateSpace) {
      const unc = uncertaintyEstimator(cand);
      if (unc > maxInfo) {
        maxInfo = unc;
        bestCandidate = cand;
        bestPred = theoryModel(cand);
      }
    }

    const expId = `exp_doe_${this.iterations.length + 1}`;
    return new ExperimentProposal({
      experimentId: expId,
      targetParameters: bestCandidate || {},
      predictedTheoreticalOutput: bestPred,
      expectedInformationGain: maxInfo,
      rationale: `Maximizes epistemic uncertainty (${maxInfo.toFixed(3)}) across parameter space`
    });
  }

  closeLoop(proposal, measuredLabValue, session, parameterBounds = null) {
    const discrepancy = Math.abs(measuredLabValue - proposal.predictedTheoreticalOutput);

    // Prepare calibration row
    const calibRow = { ...proposal.targetParameters, observed: measuredLabValue };
    let calibratedParams = {};
    let rmse = discrepancy;

    if (session && session.dae && typeof session.dae.calibrate === 'function') {
      const initP = {};
      for (const k of Object.keys(proposal.targetParameters)) {
        initP[k] = 1.0;
      }
      const res = session.dae.calibrate({
        experimentalData: [calibRow],
        modelFn: (inp, p) => Object.entries(inp).reduce((sum, [k, v]) => sum + (p[k] !== undefined ? p[k] : 1.0) * (typeof v === 'number' ? v : 1.0), 0),
        initialParams: initP,
        targetKey: 'observed',
        paramBounds: parameterBounds
      });
      calibratedParams = res.calibratedParameters;
      rmse = res.finalRmse;
    }

    // Record to LDR if available
    if (session && session.ldr && typeof session.ldr.synthesizeReferenceTable === 'function') {
      const sweeps = {};
      for (const [k, v] of Object.entries(proposal.targetParameters)) {
        sweeps[k] = [v];
      }
      session.ldr.synthesizeReferenceTable({
        tableId: `ele_run_${this.iterations.length + 1}`,
        name: 'Experiment Loop Baseline',
        modelFn: () => ({ lab_measured: measuredLabValue, pred: proposal.predictedTheoreticalOutput }),
        parameterSweeps: sweeps
      });
    }

    const result = new LoopIterationResult({
      iterationIndex: this.iterations.length + 1,
      proposal,
      measuredLabValue,
      theoreticalPrediction: proposal.predictedTheoreticalOutput,
      discrepancyDelta: discrepancy,
      recalibratedParameters: calibratedParams,
      residualRmse: rmse
    });

    this.iterations.push(result);
    return result;
  }
}
