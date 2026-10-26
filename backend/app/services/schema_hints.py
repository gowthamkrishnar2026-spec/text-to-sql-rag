"""
Schema annotations for the prompt: table descriptions and the allowed values of small-choice columns.

Why: the model cannot see the data, so it guesses spellings (status = 'completed' vs 'Completed') and
cannot tell which of two similarly named tables is meant (departments vs corp_departments). A short
description per table and the list of values for low-cardinality text columns removes both guesses.

`collect_value_hints` takes a `fetch(sql) -> rows` callable, so it is independent of SQLAlchemy and testable.
"""
import copy
import json
import logging
import os
import re
from typing import Any, Callable, Dict, List, Optional, Sequence

logger = logging.getLogger(__name__)

_TEXT = re.compile(r"CHAR|TEXT|STRING|CLOB", re.I)
_DESC_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "schema_descriptions.json")


def _quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _clean(value: Any, max_len: int) -> str:
    # data values end up in the prompt: flatten whitespace and cap length
    return re.sub(r"\s+", " ", str(value)).strip()[:max_len]


def _text_columns(info: Dict[str, Any]) -> List[str]:
    pk = set(info.get("primary_keys") or [])
    fk_cols = {c for fk in info.get("foreign_keys_struct") or [] for c in fk.get("columns", [])}
    out = []
    for detail in info.get("detailed_columns") or []:
        parts = detail.split(None, 1)
        if len(parts) == 2 and _TEXT.search(parts[1]) and parts[0] not in pk and parts[0] not in fk_cols:
            out.append(parts[0])
    return out


def collect_value_hints(schema: Dict[str, Dict[str, Any]], fetch: Callable[[str], Sequence[Sequence[Any]]],
                        max_values: int = 12, max_len: int = 40,
                        quote: Callable[[str], str] = _quote) -> Dict[str, Dict[str, List[str]]]:
    """{table: {column: [distinct values]}} for text columns with at most `max_values` distinct values
    that repeat (distinct count below the row count), so identifiers, e-mails and names are skipped."""
    hints: Dict[str, Dict[str, List[str]]] = {}
    for table, info in schema.items():
        cols = _text_columns(info)
        if not cols:
            continue
        try:
            nrows = int(fetch(f"SELECT COUNT(*) FROM {quote(table)}")[0][0])
        except Exception:
            continue
        for col in cols:
            try:
                rows = fetch(f"SELECT DISTINCT {quote(col)} FROM {quote(table)} "
                             f"WHERE {quote(col)} IS NOT NULL LIMIT {max_values + 1}")
            except Exception:
                continue
            values = sorted({_clean(r[0], max_len) for r in rows if r[0] is not None} - {""})
            if 0 < len(values) <= max_values and len(rows) < nrows:
                hints.setdefault(table, {})[col] = values
    return hints


def load_descriptions(path: Optional[str] = None) -> Dict[str, str]:
    try:
        with open(path or _DESC_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {k: str(v) for k, v in data.items()} if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def annotate_schema(schema: Dict[str, Dict[str, Any]], descriptions: Optional[Dict[str, str]] = None,
                    hints: Optional[Dict[str, Dict[str, List[str]]]] = None) -> Dict[str, Dict[str, Any]]:
    """Copy of `schema` with `description` and `value_hints` added per table (input is not modified)."""
    out = copy.deepcopy(schema)
    for table, info in out.items():
        if descriptions and descriptions.get(table):
            info["description"] = descriptions[table]
        if hints and hints.get(table):
            info["value_hints"] = hints[table]
    return out
