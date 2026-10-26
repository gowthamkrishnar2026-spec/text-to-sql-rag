#!/usr/bin/env python3
"""
Spider Dataset Loader & Manager
===============================
Provides an API and CLI for loading, inspecting, and querying the official Yale Spider dataset.

Features:
  - Loads train (train_spider.json, train_others.json), dev (dev.json), and schema (tables.json) splits.
  - Lists and connects to all 166 domain-specific SQLite databases in datasets/spider/database/.
  - Filters questions compatible with project domain schemas.
  - Seeds or inspects local relational databases.

Usage:
  # CLI summary and verification:
  python datasets/loader.py

  # Programmatic import:
  from datasets.loader import SpiderDatasetLoader
  loader = SpiderDatasetLoader()
  dev_data = loader.load_dev()
  print(f"Loaded {len(dev_data)} questions.")
"""

import json
import os
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SPIDER_DIR = os.path.join(PROJECT_ROOT, "datasets", "spider")

PROJECT_TABLES = {
    "students", "departments", "instructors", "courses", "enrollments",
    "customers", "products", "orders", "order_items",
    "corp_departments", "employees"
}


class SpiderDatasetLoader:
    """Manages loading and querying of the Yale Spider text-to-SQL benchmark dataset."""

    def __init__(self, spider_dir: str = SPIDER_DIR):
        self.spider_dir = os.path.abspath(spider_dir)
        self.dev_file = os.path.join(self.spider_dir, "dev.json")
        self.train_spider_file = os.path.join(self.spider_dir, "train_spider.json")
        self.train_others_file = os.path.join(self.spider_dir, "train_others.json")
        self.tables_file = os.path.join(self.spider_dir, "tables.json")
        self.databases_dir = os.path.join(self.spider_dir, "database")
        self.hf_dir = os.path.join(PROJECT_ROOT, "datasets", "huggingface_spider")

    def is_available(self) -> bool:
        """Returns True if the Spider dataset files exist and are extracted."""
        return os.path.exists(self.dev_file) and os.path.exists(self.tables_file)

    def load_huggingface_spider(self, split: str = "all", as_dataframe: bool = True):
        """
        Loads the Hugging Face format Spider dataset (xlangai/spider).
        Args:
            split: 'train', 'validation', or 'all'
            as_dataframe: if True, returns pandas.DataFrame, otherwise list of dicts
        """
        import pandas as pd
        train_path = os.path.join(self.hf_dir, "train.parquet")
        val_path = os.path.join(self.hf_dir, "validation.parquet")

        if split == "train":
            df = pd.read_parquet(train_path)
            return df if as_dataframe else df.to_dict(orient="records")
        elif split in ("validation", "val", "dev"):
            df = pd.read_parquet(val_path)
            return df if as_dataframe else df.to_dict(orient="records")
        elif split == "all":
            df_train = pd.read_parquet(train_path)
            df_val = pd.read_parquet(val_path)
            if as_dataframe:
                return {"train": df_train, "validation": df_val}
            return {"train": df_train.to_dict(orient="records"), "validation": df_val.to_dict(orient="records")}
        else:
            raise ValueError(f"Unknown split: {split}. Choose 'train', 'validation', or 'all'.")

    def load_dev(self, filter_compatible: bool = False) -> List[Dict[str, Any]]:
        """Loads the evaluation development set (1,034 examples)."""
        if not os.path.exists(self.dev_file):
            raise FileNotFoundError(f"Spider dev file not found at: {self.dev_file}")
        with open(self.dev_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if filter_compatible:
            return self._filter_compatible(data)
        return data

    def load_train(self, include_others: bool = False, filter_compatible: bool = False) -> List[Dict[str, Any]]:
        """Loads the training set (7,000 spider + optional 1,659 others)."""
        if not os.path.exists(self.train_spider_file):
            raise FileNotFoundError(f"Spider train file not found at: {self.train_spider_file}")
        with open(self.train_spider_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if include_others and os.path.exists(self.train_others_file):
            with open(self.train_others_file, "r", encoding="utf-8") as f:
                data.extend(json.load(f))
        if filter_compatible:
            return self._filter_compatible(data)
        return data

    def load_tables(self) -> List[Dict[str, Any]]:
        """Loads all database schema definitions (tables, columns, types, foreign keys)."""
        if not os.path.exists(self.tables_file):
            raise FileNotFoundError(f"Spider tables file not found at: {self.tables_file}")
        with open(self.tables_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_databases(self) -> List[str]:
        """Returns a list of all database IDs available in the dataset."""
        if not os.path.exists(self.databases_dir):
            return []
        return sorted([
            d for d in os.listdir(self.databases_dir)
            if os.path.isdir(os.path.join(self.databases_dir, d))
        ])

    def get_database_path(self, db_id: str) -> Optional[str]:
        """Returns the absolute file path to the SQLite file for a given database ID."""
        candidate = os.path.join(self.databases_dir, db_id, f"{db_id}.sqlite")
        return candidate if os.path.exists(candidate) else None

    def connect_database(self, db_id: str) -> sqlite3.Connection:
        """Opens a read-only SQLite connection to a specific Spider database."""
        db_path = self.get_database_path(db_id)
        if not db_path:
            raise FileNotFoundError(f"SQLite database '{db_id}' not found at {self.databases_dir}")
        return sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)

    def query_database(self, db_id: str, sql: str) -> Tuple[List[str], List[Tuple]]:
        """Executes a SQL query against a Spider database and returns (column_names, rows)."""
        conn = self.connect_database(db_id)
        try:
            cursor = conn.cursor()
            cursor.execute(sql)
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            return columns, rows
        finally:
            conn.close()

    def get_summary(self) -> Dict[str, Any]:
        """Returns aggregate statistics for the loaded dataset."""
        if not self.is_available():
            return {"available": False}

        dev_cases = len(self.load_dev(filter_compatible=False))
        compat_dev = len(self.load_dev(filter_compatible=True))
        train_spider = len(self.load_train(include_others=False, filter_compatible=False))
        train_all = len(self.load_train(include_others=True, filter_compatible=False))
        compat_train = len(self.load_train(include_others=True, filter_compatible=True))
        tables = len(self.load_tables())
        dbs = len(self.list_databases())

        return {
            "available": True,
            "spider_dir": self.spider_dir,
            "dev_questions": dev_cases,
            "compatible_dev_questions": compat_dev,
            "train_spider_questions": train_spider,
            "train_total_questions": train_all,
            "compatible_train_questions": compat_train,
            "schema_count": tables,
            "database_count": dbs,
        }

    def _filter_compatible(self, dataset: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filters questions whose gold SQL references tables present in this project's schema."""
        compatible = []
        for item in dataset:
            sql_lower = item.get("query", "").lower()
            if any(f" {t} " in sql_lower or f" {t};" in sql_lower or f" {t}\n" in sql_lower for t in PROJECT_TABLES):
                compatible.append(item)
        return compatible


def main():
    loader = SpiderDatasetLoader()
    print("=" * 70)
    print("  Official Yale Spider Dataset Loader & Verification")
    print("=" * 70)

    if not loader.is_available():
        print(f"Error: Dataset not found in {loader.spider_dir}")
        return

    summary = loader.get_summary()
    print(f"  • Dataset Directory          : {summary['spider_dir']}")
    print(f"  • Validation Questions (Dev) : {summary['dev_questions']:,}")
    print(f"  • Compatible Dev Questions   : {summary['compatible_dev_questions']:,}")
    print(f"  • Training Questions (Spider): {summary['train_spider_questions']:,}")
    print(f"  • Total Training Questions   : {summary['train_total_questions']:,}")
    print(f"  • Compatible Train Questions : {summary['compatible_train_questions']:,}")
    print(f"  • Database Schemas in Tables : {summary['schema_count']:,}")
    print(f"  • Relational SQLite DBs      : {summary['database_count']:,}")
    print("-" * 70)

    # Test sample query on an actual Spider database
    sample_db = "academic"
    if sample_db in loader.list_databases():
        query = "SELECT aid, name FROM author LIMIT 3;"
        cols, rows = loader.query_database(sample_db, query)
        print(f"  ✓ Live Test Query on Spider DB '{sample_db}':")
        print(f"    SQL: {query}")
        print(f"    Result ({cols}): {rows}")
    print("-" * 70)

    # Check project local SQLite database
    local_db = os.path.join(PROJECT_ROOT, "backend", "text2sql.db")
    if os.path.exists(local_db):
        conn = sqlite3.connect(local_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'query_history';")
        tbls = [r[0] for r in cursor.fetchall()]
        total_rows = 0
        for t in tbls:
            cursor.execute(f"SELECT COUNT(*) FROM {t};")
            total_rows += cursor.fetchone()[0]
        conn.close()
        print(f"  ✓ Project Seed DB (text2sql.db): {len(tbls)} tables populated, {total_rows} total rows.")
    print("=" * 70)
    print("  Dataset successfully loaded and verified!")
    print("=" * 70)


if __name__ == "__main__":
    main()
