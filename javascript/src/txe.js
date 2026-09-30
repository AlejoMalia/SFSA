/**
 * sfsa.txe — Transfer & Cross-Session Experience Engine (TXE)
 * ==========================================================
 * Bridges computational memory across sessions, projects, and scientific campaigns.
 * Transfers inferred constraints (CAE), response surface surrogates (SME), active subspaces (SRA),
 * and domain tags (TIL) from completed sessions to warm-start new related frameworks,
 * preventing the waste of relearning the same scientific priors from scratch.
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

export class TransferredPrior {
  constructor({
    sourceSessionName,
    priorType,
    domain,
    payload,
    confidence,
    timestamp = Date.now() / 1000
  }) {
    this.sourceSessionName = sourceSessionName;
    this.priorType = priorType;
    this.domain = domain;
    this.payload = payload;
    this.confidence = confidence;
    this.timestamp = timestamp;
  }
}

export class ExperienceSnapshot {
  constructor({
    frameworkName,
    domainTags = [],
    priors = [],
    metadata = {}
  }) {
    this.frameworkName = frameworkName;
    this.domainTags = domainTags;
    this.priors = priors;
    this.metadata = metadata;
  }
}

export class TransferExperienceEngine {
  constructor() {
    this.repository = [];
  }

  captureSessionExperience(session) {
    const priors = [];

    // 1. Capture Inferred Constraints from CAE
    if (session.cae && Array.isArray(session.cae.inferredConstraints)) {
      for (const c of session.cae.inferredConstraints) {
        priors.push(new TransferredPrior({
          sourceSessionName: session.name || 'session',
          priorType: 'CONSTRAINT',
          domain: 'general',
          payload: { param: c.parameterName, op: c.conditionOp, threshold: c.thresholdValue },
          confidence: c.confidence
        }));
      }
    }

    // 2. Capture Surrogates from SME
    if (session.sme && session.sme.surrogates) {
      for (const [mid, surr] of Object.entries(session.sme.surrogates)) {
        priors.push(new TransferredPrior({
          sourceSessionName: session.name || 'session',
          priorType: 'SURROGATE',
          domain: 'response_surface',
          payload: { modelId: mid, features: surr.featureNames, pointsCount: (surr.samplePoints || []).length },
          confidence: 0.9
        }));
      }
    }

    // 3. Capture Domain Tags from TIL
    let tags = [];
    if (session.til && typeof session.til.getPrimaryTags === 'function') {
      tags = session.til.getPrimaryTags().map(t => t.label || t.name);
    }

    const snapshot = new ExperienceSnapshot({
      frameworkName: session.name || 'session',
      domainTags: tags,
      priors,
      metadata: { activeEngines: session.name || 'sfsa_session' }
    });

    this.repository.push(snapshot);
    return snapshot;
  }

  warmStartSession(targetSession, domainKeywords = [], minConfidence = 0.5) {
    let appliedCount = 0;
    const keywordsLower = domainKeywords.map(k => k.toLowerCase());

    for (const snapshot of this.repository) {
      const match = keywordsLower.length === 0 ||
        snapshot.domainTags.some(t => keywordsLower.includes(t.toLowerCase()));

      if (!match) continue;

      for (const prior of snapshot.priors) {
        if (prior.confidence < minConfidence) continue;

        if (prior.priorType === 'CONSTRAINT' && targetSession.cae && typeof targetSession.cae.addExplicitConstraint === 'function') {
          const p = prior.payload;
          targetSession.cae.addExplicitConstraint(
            inp => {
              const val = inp[p.param];
              if (typeof val !== 'number') return [true, ''];
              const blocked = { '>=': val >= p.threshold, '<=': val <= p.threshold, '<': val >= p.threshold, '>': val <= p.threshold }[p.op] || false;
              return [!blocked, `Transferred constraint from ${prior.sourceSessionName}: ${p.param} ${p.op} ${p.threshold}`];
            }
          );
          appliedCount += 1;
        }
      }
    }

    return appliedCount;
  }
}
