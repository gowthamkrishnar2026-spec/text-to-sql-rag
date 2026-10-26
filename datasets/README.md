# Datasets

The app itself does **not** need anything here: its demo database is created from `database/init.sql`.
The Spider files are only used by the optional evaluation scripts, so they are not stored in Git (about 900 MB).

To reproduce the Spider benchmark in the paper:

1. Download Spider from https://yale-lily.github.io/spider and unzip it so that
   `datasets/spider/dev.json`, `datasets/spider/dev_gold.sql` and `datasets/spider/database/<db_id>/<db_id>.sqlite` exist.
2. Run `python backend/benchmarks/rag_spider_eval.py --dry-run` to check the files are found.

`huggingface_spider/*.json` is a small copy of the Spider train/validation questions used to build the optional
Spider example index. `model_evaluation_50_test_cases.md` is the report of the earlier 50-question model comparison.
