/**
 * sfsa.ldr — Laboratory Data Repository Engine (LDR)
 * =================================================
 * Synthesizes, organizes, and projects multi-dimensional reference data tables and empirical benchmark datasets.
 * Prevents scientific inquiries from collapsing into an isolated single number: generates structured tables,
 * parametric ranges, and statistical baselines from framework runs, equipping the researcher with a persistent
 * laboratory dataset to validate, compare, and accelerate future calculations via table interpolation.
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

export class DatasetTable {
  constructor({
    tableId,
    name,
    description = '',
    columns = [],
    rows = [],
    summaryStats = {},
    createdAt = Date.now()
  }) {
    this.tableId = tableId;
    this.name = name;
    this.description = description;
    this.columns = columns;
    this.rows = rows;
    this.summaryStats = summaryStats;
    this.createdAt = createdAt;
  }

  toMarkdown(maxRows = 10) {
    if (!this.columns || this.columns.length === 0 || !this.rows || this.rows.length === 0) {
      return '_Empty Laboratory Dataset Table_';
    }

    const header = '| ' + this.columns.join(' | ') + ' |';
    const sep = '| ' + this.columns.map(() => '---').join(' | ') + ' |';
    const lines = [header, sep];

    const displayRows = this.rows.slice(0, maxRows);
    for (const r of displayRows) {
      const vals = this.columns.map(col => {
        const val = r[col];
        if (typeof val === 'number') {
          return val.toFixed(4);
        }
        return val !== undefined && val !== null ? String(val) : '';
      });
      lines.push('| ' + vals.join(' | ') + ' |');
    }

    if (this.rows.length > maxRows) {
      lines.push(`| ... (${this.rows.length - maxRows} additional rows in repository) |` + ' |'.repeat(this.columns.length - 1));
    }

    return lines.join('\n');
  }
}

export class LaboratoryDataRepository {
  constructor() {
    this.tables = new Map();
  }

  synthesizeReferenceTable({
    tableId,
    name,
    modelFn,
    parameterSweeps,
    description = ''
  }) {
    const paramNames = Object.keys(parameterSweeps);
    const paramValueLists = paramNames.map(k => parameterSweeps[k]);

    // Cartesian product of sweeps
    const cartesian = (arrays) => {
      return arrays.reduce((acc, curr) => {
        return acc.flatMap(c => curr.map(item => [...c, item]));
      }, [[]]);
    };

    const combinations = cartesian(paramValueLists);
    const rows = [];
    let outputCols = [];

    for (const combo of combinations) {
      const inputRow = {};
      for (let i = 0; i < paramNames.length; i++) {
        inputRow[paramNames[i]] = combo[i];
      }

      const outputDict = modelFn(inputRow);

      if (outputCols.length === 0) {
        outputCols = Object.keys(outputDict);
      }

      rows.push({ ...inputRow, ...outputDict });
    }

    const allCols = [...paramNames, ...outputCols];

    // Compute summary statistics for numeric columns
    const stats = {};
    for (const col of allCols) {
      const vals = rows.map(r => r[col]).filter(v => typeof v === 'number');
      if (vals.length > 0) {
        const meanV = vals.reduce((a, b) => a + b, 0) / vals.length;
        const variance = vals.reduce((sum, v) => sum + (v - meanV) ** 2, 0) / vals.length;
        stats[col] = {
          min: Math.min(...vals),
          max: Math.max(...vals),
          mean: meanV,
          stdDev: Math.sqrt(variance)
        };
      }
    }

    const table = new DatasetTable({
      tableId,
      name,
      description,
      columns: allCols,
      rows,
      summaryStats: stats
    });

    this.tables.set(tableId, table);
    return table;
  }

  getTable(tableId) {
    return this.tables.get(tableId) || null;
  }

  queryTable(tableId, filters = null, limit = 50) {
    const table = this.getTable(tableId);
    if (!table) return [];

    if (!filters) {
      return table.rows.slice(0, limit);
    }

    const matching = [];
    for (const r of table.rows) {
      let match = true;
      for (const [k, expected] of Object.entries(filters)) {
        if (r[k] !== expected) {
          match = false;
          break;
        }
      }
      if (match) {
        matching.push(r);
        if (matching.length >= limit) break;
      }
    }

    return matching;
  }

  interpolateFromTable(tableId, targetPoint, targetOutputKey) {
    const table = this.getTable(tableId);
    if (!table || !table.rows || table.rows.length === 0) {
      return null;
    }

    const paramKeys = Object.keys(targetPoint).filter(k => table.columns.includes(k));
    if (paramKeys.length === 0) {
      return null;
    }

    let bestRow = null;
    let minDist = Infinity;

    for (const r of table.rows) {
      let sq = 0;
      for (const k of paramKeys) {
        sq += (targetPoint[k] - r[k]) ** 2;
      }
      const dist = Math.sqrt(sq);
      if (dist < minDist) {
        minDist = dist;
        bestRow = r;
      }
    }

    return bestRow ? bestRow[targetOutputKey] : null;
  }

  exportCsv(tableId) {
    const table = this.getTable(tableId);
    if (!table) {
      throw new Error(`Table '${tableId}' not found.`);
    }

    const lines = [table.columns.join(',')];
    for (const r of table.rows) {
      lines.push(table.columns.map(c => (r[c] !== undefined ? r[c] : '')).join(','));
    }

    return lines.join('\n');
  }
}
