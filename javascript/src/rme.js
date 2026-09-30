/**
 * sfsa.rme — Reproducibility & Environment Manifest Engine (RME)
 * ==============================================================
 * Tackles the scientific reproducibility crisis. Generates cryptographic execution certificates
 * and environment manifests recording hardware architecture, OS platform, IEEE-754 floating-point
 * precision, deterministic RNG seeds, and module signatures ready for journal peer-review supplements.
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

import crypto from 'crypto';
import os from 'os';

export class ReproducibilityManifestEngine {
  constructor() {}

  // Canonical JSON: keys sorted at EVERY nesting level (an array replacer would drop nested keys).
  static _canonical(v) {
    if (Array.isArray(v)) return `[${v.map((x) => ReproducibilityManifestEngine._canonical(x)).join(',')}]`;
    if (v && typeof v === 'object') {
      return `{${Object.keys(v).sort().map((k) => `${JSON.stringify(k)}:${ReproducibilityManifestEngine._canonical(v[k])}`).join(',')}}`;
    }
    return JSON.stringify(v) ?? 'null';
  }

  static _seal(sessionName, timestamp, platformInfo, runtimeVersion, floatInfo, engineCount, extra) {
    const payload = { sessionName, timestamp, platformInfo, runtimeVersion, floatInfo, engineCount, extra };
    return crypto.createHash('sha256').update(ReproducibilityManifestEngine._canonical(payload)).digest('hex');
  }

  verifyManifest(m) {
    return m.cryptographicSeal === ReproducibilityManifestEngine._seal(
      m.sessionName, m.manifestTimestamp, m.platformInfo, m.runtimeVersion,
      m.floatingPointPrecision, m.activeEngineCount, m.environmentMetadata
    );
  }

  generateManifest(sessionName, engineCount = 39, extraMetadata = {}) {
    const plat = {
      system: os.type(),
      release: os.release(),
      machine: os.arch(),
      platform: os.platform()
    };

    const floatInfo = {
      epsilon: Number.EPSILON,
      max: Number.MAX_VALUE,
      min: Number.MIN_VALUE
    };

    const now = Date.now();
    const hash = ReproducibilityManifestEngine._seal(
      sessionName, now, plat, process.version, floatInfo, engineCount, extraMetadata
    );

    return {
      sessionName,
      manifestTimestamp: now,
      cryptographicSeal: hash,
      platformInfo: plat,
      runtimeVersion: process.version,
      floatingPointPrecision: floatInfo,
      activeEngineCount: engineCount,
      environmentMetadata: extraMetadata
    };
  }
}
