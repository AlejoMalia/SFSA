/**
 * sfsa.til — Tag Index & Linking Engine (TIL)
 * ==========================================
 * Living taxonomy and search profile generator.
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

export const TagType = {
  DOMAIN: 'domain',
  METHOD: 'method',
  VARIABLE: 'variable',
  REGIME: 'regime',
  VALIDATION: 'validation',
  DATA: 'data',
  SOFTWARE: 'software'
};

export class TagIndexLinkingEngine {
  constructor() {
    this.tags = new Map();
  }

  addOrUpdateTag(tagId, label, tagType = TagType.DOMAIN, weightIncrement = 0.1, source = "internal", aliases = {}) {
    if (this.tags.has(tagId)) {
      const tag = this.tags.get(tagId);
      if (tag.status !== "pinned") {
        tag.weight += weightIncrement;
      }
      tag.lastUpdated = Date.now();
      tag.evidence.push({ source, timestamp: Date.now() });
      return tag;
    }

    const tag = {
      id: tagId,
      label,
      type: tagType,
      weight: weightIncrement,
      confidence: 0.85,
      status: "active",
      evidence: [{ source, timestamp: Date.now() }],
      externalAliases: aliases,
      firstSeen: Date.now(),
      lastUpdated: Date.now()
    };
    this.tags.set(tagId, tag);
    return tag;
  }

  pinTag(tagId) {
    if (this.tags.has(tagId)) {
      this.tags.get(tagId).status = "pinned";
      return true;
    }
    return false;
  }

  getPrimaryTags(topK = 5) {
    const list = Array.from(this.tags.values()).filter(t => t.status !== "deprecated");
    list.sort((a, b) => b.weight - a.weight);
    return list.slice(0, topK);
  }

  makeSearchProfile() {
    const primary = this.getPrimaryTags(4);
    const mustInclude = primary.filter(t => t.type === TagType.DOMAIN).map(t => t.label);
    const shouldInclude = primary.filter(t => t.type !== TagType.DOMAIN).map(t => t.label);
    return {
      mustInclude,
      shouldInclude,
      timestamp: Date.now()
    };
  }

  exportTagLibrary() {
    return {
      version: "0.2.0",
      totalTags: this.tags.size,
      tags: Object.fromEntries(this.tags.entries())
    };
  }
}
