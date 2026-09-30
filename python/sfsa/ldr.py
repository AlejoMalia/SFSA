"""
sfsa.ldr — Laboratory Data Repository Engine (LDR)
=================================================
Synthesizes, organizes, and projects multi-dimensional reference data tables and empirical benchmark datasets.
Prevents scientific inquiries from collapsing into an isolated single number: generates structured tables,
parametric ranges, and statistical baselines from framework runs, equipping the researcher with a persistent
laboratory dataset to validate, compare, and accelerate future calculations via table interpolation.

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
import itertools
import math
import time


@dataclass
class DatasetTable:
    """A structured reference scientific dataset table."""
    table_id: str
    name: str
    description: str
    columns: List[str]
    rows: List[Dict[str, Any]] = field(default_factory=list)
    summary_stats: Dict[str, Dict[str, float]] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_markdown(self, max_rows: int = 10) -> str:
        """Renders dataset as a GitHub-flavored markdown table."""
        if not self.columns or not self.rows:
            return "_Empty Laboratory Dataset Table_"

        header = "| " + " | ".join(self.columns) + " |"
        sep = "| " + " | ".join(["---"] * len(self.columns)) + " |"
        lines = [header, sep]

        for row in self.rows[:max_rows]:
            vals = []
            for col in self.columns:
                val = row.get(col, "")
                if isinstance(val, float):
                    vals.append(f"{val:.4f}")
                else:
                    vals.append(str(val))
            lines.append("| " + " | ".join(vals) + " |")

        if len(self.rows) > max_rows:
            lines.append(f"| ... ({len(self.rows) - max_rows} additional rows in repository) |" + " |" * (len(self.columns) - 1))

        return "\n".join(lines)


class LaboratoryDataRepository:
    """
    LDR synthesizes and manages scientific data tables, providing reference datasets for models.
    """

    def __init__(self) -> None:
        self.tables: Dict[str, DatasetTable] = {}

    def synthesize_reference_table(
        self,
        table_id: str,
        name: str,
        model_fn: Callable[[Dict[str, float]], Dict[str, Any]],
        parameter_sweeps: Dict[str, List[float]],
        description: str = "",
    ) -> DatasetTable:
        """
        Synthesizes a rich multidimensional reference dataset from parameter grids.
        Ensures the scientist has a comprehensive table of results rather than an isolated point.
        """
        param_names = list(parameter_sweeps.keys())
        param_value_lists = [parameter_sweeps[k] for k in param_names]

        # Generate cartesian product of parameter sweeps
        all_combinations = list(itertools.product(*param_value_lists))
        rows: List[Dict[str, Any]] = []
        output_cols: List[str] = []

        for combo in all_combinations:
            input_row = {param_names[i]: combo[i] for i in range(len(param_names))}
            output_dict = model_fn(input_row)

            if not output_cols:
                output_cols = list(output_dict.keys())

            full_row = dict(input_row)
            full_row.update(output_dict)
            rows.append(full_row)

        all_cols = param_names + output_cols

        # Compute summary statistics for numeric columns
        stats = {}
        for col in all_cols:
            vals = [r[col] for r in rows if isinstance(r.get(col), (int, float))]
            if vals:
                mean_v = sum(vals) / len(vals)
                variance = sum((v - mean_v) ** 2 for v in vals) / len(vals)
                stats[col] = {
                    "min": min(vals),
                    "max": max(vals),
                    "mean": mean_v,
                    "std_dev": math.sqrt(variance),
                }

        table = DatasetTable(
            table_id=table_id,
            name=name,
            description=description,
            columns=all_cols,
            rows=rows,
            summary_stats=stats,
        )
        self.tables[table_id] = table
        return table

    def get_table(self, table_id: str) -> Optional[DatasetTable]:
        """Retrieves a stored dataset table."""
        return self.tables.get(table_id)

    def query_table(
        self,
        table_id: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Queries table rows matching filter criteria."""
        table = self.get_table(table_id)
        if not table:
            return []

        if not filters:
            return table.rows[:limit]

        matching = []
        for r in table.rows:
            match = True
            for k, expected in filters.items():
                if k not in r or r[k] != expected:
                    match = False
                    break
            if match:
                matching.append(r)
                if len(matching) >= limit:
                    break

        return matching

    def interpolate_from_table(
        self,
        table_id: str,
        target_point: Dict[str, float],
        target_output_key: str,
    ) -> Optional[float]:
        """
        Fast O(1)-style nearest-neighbor interpolation from the repository table.
        Accelerates future computations without re-executing heavy differential solvers.
        """
        table = self.get_table(table_id)
        if not table or not table.rows:
            return None

        param_keys = [k for k in target_point.keys() if k in table.columns]
        if not param_keys:
            return None

        # Nearest neighbor
        best_row = None
        min_dist = float("inf")

        for r in table.rows:
            sq = sum((target_point[k] - r[k]) ** 2 for k in param_keys)
            dist = math.sqrt(sq)
            if dist < min_dist:
                min_dist = dist
                best_row = r

        return best_row.get(target_output_key) if best_row else None

    def export_csv(self, table_id: str) -> str:
        """Exports dataset table as CSV string."""
        table = self.get_table(table_id)
        if not table:
            raise KeyError(f"Table '{table_id}' not found.")

        lines = [",".join(table.columns)]
        for r in table.rows:
            lines.append(",".join(str(r.get(c, "")) for c in table.columns))

        return "\n".join(lines)
