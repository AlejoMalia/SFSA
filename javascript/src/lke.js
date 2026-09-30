/**
 * sfsa.lke — Literature & Knowledge Engine (LKE)
 * =============================================
 * Curated typed registry of external scientific sources and contextual proposal emitter.
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

export const SourceType = {
  PREPRINT: 'PREPRINT',
  INDEXED_LITERATURE: 'INDEXED_LITERATURE',
  DATASET_PROPERTIES: 'DATASET',
  CODE_METHODS: 'CODE_METHODS'
};

export const DEFAULT_SOURCES = [
  { sourceId: "arxiv", name: "arXiv", sourceType: SourceType.PREPRINT, domainTags: ["physics", "math", "astrophysics", "computer_science"], url: "https://arxiv.org", isOpenAccess: true },
  { sourceId: "chemrxiv", name: "ChemRxiv", sourceType: SourceType.PREPRINT, domainTags: ["chemical_kinetics", "chemistry", "materials_science"], url: "https://chemrxiv.org", isOpenAccess: true },
  { sourceId: "openalex", name: "OpenAlex", sourceType: SourceType.INDEXED_LITERATURE, domainTags: ["multidisciplinary"], url: "https://openalex.org", isOpenAccess: true },
  { sourceId: "semantic_scholar", name: "Semantic Scholar", sourceType: SourceType.INDEXED_LITERATURE, domainTags: ["multidisciplinary", "computer_science"], url: "https://www.semanticscholar.org", isOpenAccess: true },
  { sourceId: "nist", name: "NIST WebBook", sourceType: SourceType.DATASET_PROPERTIES, domainTags: ["thermodynamics", "chemical_kinetics"], url: "https://webbook.nist.gov", isOpenAccess: true },
  { sourceId: "materials_project", name: "Materials Project", sourceType: SourceType.DATASET_PROPERTIES, domainTags: ["materials_science", "crystallography"], url: "https://materialsproject.org", isOpenAccess: true },
  { sourceId: "biorxiv", name: "bioRxiv", sourceType: SourceType.PREPRINT, domainTags: ["biology", "biophysics", "biochemistry"], url: "https://biorxiv.org", isOpenAccess: true },
  { sourceId: "nasa_ads", name: "NASA ADS", sourceType: SourceType.INDEXED_LITERATURE, domainTags: ["astrophysics_space", "planetary"], url: "https://ui.adsabs.harvard.edu", isOpenAccess: true },
  { sourceId: "pubmed", name: "PubMed / Europe PMC", sourceType: SourceType.INDEXED_LITERATURE, domainTags: ["biology", "biochemistry", "medical"], url: "https://europepmc.org", isOpenAccess: true },
  { sourceId: "pubchem", name: "PubChem", sourceType: SourceType.DATASET_PROPERTIES, domainTags: ["chemistry", "chemical_kinetics"], url: "https://pubchem.ncbi.nlm.nih.gov", isOpenAccess: true },
  { sourceId: "zenodo", name: "Zenodo", sourceType: SourceType.DATASET_PROPERTIES, domainTags: ["multidisciplinary", "experimental_validation"], url: "https://zenodo.org", isOpenAccess: true },
  { sourceId: "papers_with_code", name: "Papers with Code", sourceType: SourceType.CODE_METHODS, domainTags: ["numerical_optimization", "machine_learning"], url: "https://paperswithcode.com", isOpenAccess: true }
];

export class LiteratureKnowledgeEngine {
  constructor(customSources = null) {
    this.sources = customSources || DEFAULT_SOURCES;
  }

  proposeResources(primaryDomains = ["multidisciplinary"], limit = 5, sourceTypes = null) {
    const scored = [];
    for (const s of this.sources) {
      if (sourceTypes && sourceTypes.length > 0 && !sourceTypes.includes(s.sourceType)) continue;
      let score = 0;
      if (s.domainTags.includes("multidisciplinary")) score += 0.5;
      for (const d of primaryDomains) {
        if (s.domainTags.includes(d)) score += 1.0;
      }
      if (sourceTypes && sourceTypes.length > 0 && score === 0) score = 0.25;
      if (score > 0) scored.push({ source: s, score });
    }

    scored.sort((a, b) => b.score - a.score);
    return scored.slice(0, limit).map(({ source, score }) => ({
      title: `External ${source.sourceType}: ${source.name}`,
      sourceName: source.name,
      sourceType: source.sourceType,
      url: source.url,
      confidence: Math.min(1.0, score / 2.0),
      isOpenAccess: source.isOpenAccess,
      rationale: `Matched domain tags: ${primaryDomains.join(', ')}`
    }));
  }
}
