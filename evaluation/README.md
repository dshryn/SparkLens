# SparkLens Evaluation

Internal evaluation harness for the SparkLens rule engine. It is not part of the published `sparklens` package.

SparkLens findings are scored against a fixed ground-truth dataset. The evaluation runs fully offline (no API calls, no model downloads) and is deterministic: the same inputs always give the same numbers.

## What is measured

* `dataset_expected.csv` — 50 real Spark physical plans (49 rendered with Spark 3.5 `explain("formatted")`, 1 Databricks Photon plan), each with the analysis a correct analyzer should produce, written as plain sentences (316 atomic claims)
* `dataset_predicted.csv` — what SparkLens reports for each plan (`sparklens analyze <plan> --eval`: rule engine only, AI disabled)

Both paragraphs are split into atomic claims and compared claim by claim:

* **Precision** — share of SparkLens claims backed by the ground truth (false alarms lower it)
* **Recall** — share of ground-truth claims that SparkLens states (misses lower it)
* **F1** — balance of the two
* **Final score (F0.5)** — weights precision above recall, because false alarms erode developer trust

## How claims are matched

```text
SparkLens output / ground truth
    ↓
Atomic claims (sentences split at "so / because / but"; pronouns resolved)
    ↓
Spark concept normalisation ("SMJ" = "SortMergeJoin" = "sort-merge join")
    ↓
TF-IDF vectors (Spark-concept channel + wording channel)
    ↓
Directional matching (precision: backed by the ground truth; recall: stated by SparkLens)
    ↓
Consistency rules (stage counts, numbers, polarity, exclusive alternatives, advice vs observation)
```

## Validating the evaluator

`python evaluation/evaluate_engine.py validate` measures the evaluator itself on 1,377 test cases whose correct answer is known by construction:

| Test type | Example | Correct verdict |
|---|---|---|
| Paraphrase | the same claim in different words | match |
| Number change | "3 stages" → "4 stages" | no match |
| Polarity flip | enabled ↔ disabled, required ↔ avoidable | no match |
| Concept swap | sort-merge ↔ broadcast hash join, hash ↔ range partitioning | no match |
| Cross-plan claim | a claim about an operator the plan text does not contain | no match |
| Role swap | same words, roles swapped | no match |

It also checks invariance (reordering, duplicating or re-spacing findings never changes a score) and bounds (the ground truth as prediction scores 1.0, an empty answer 0.0, another plan's output far lower).

## Results

Frozen baseline (`eval_baseline.json`), rule engine `c7daf3c`, 4 Oct 2026:

| Metric | Value |
|---|---|
| SparkLens precision / recall / F1 | 0.637 / 0.478 / 0.546 |
| SparkLens final score (F0.5) | **0.597** |
| Evaluator accuracy, 1,377 known-answer cases | **92.2%** (dev split 94.4%, test split 90.2%) |
| Evaluator false accepts / false rejects | 11.5% / 3.5% |
| Invariance checks / bounds | 200 of 200 / pass |

After the rule-engine update merged in PR #1 (`c508977`, 5 Oct 2026), the same evaluator measures precision 0.651, recall 0.611, F1 0.630 and **F0.5 0.643** (+0.045). The estimated stage count is now correct in 49 of 50 plans. The baseline will be refreshed after the evaluator fix below.

Known limitations:

* Claims that use the same words with swapped roles ("orders is broadcast, customers is shuffled" vs the reverse) are not yet told apart.
* The number check requires every number in a SparkLens claim to appear in the ground truth. So "3 stages from 2 shuffle Exchange operators" is rejected when the ground truth only says "3 stages", even when the stage count is right. This under-scores the current engine; a fix is planned.

## Running the evaluation

Run the commands from the repository root:

```bash
pip install -r evaluation/requirements-eval.txt

python evaluation/evaluate_engine.py selftest    # unit checks of the matcher and metrics
python evaluation/evaluate_engine.py validate    # evaluator accuracy on known-answer cases
python evaluation/evaluate_engine.py predict     # SparkLens (--eval) on all 50 plans -> dataset_predicted.csv
python evaluation/evaluate_engine.py evaluate    # precision / recall / F1 / final score, change vs baseline
python evaluation/evaluate_engine.py baseline    # freeze the current result as eval_baseline.json
```

`predict` runs the SparkLens CLI from the repository (`python -m cli.main`). After a rule change, run `predict --force` and then `evaluate`; improved and regressed plans are listed.

To fill `dataset_predicted.csv` by hand, run `python evaluation/evaluate_engine.py export` and paste the output of `python -m cli.main analyze evaluation/eval_plans/<id>.txt --eval` into each row.

| File | Purpose |
|---|---|
| `evaluate_engine.py` | the evaluator (commands above) |
| `dataset_expected.csv` | ground truth |
| `dataset_predicted.csv` | SparkLens output being scored |
| `eval_validation.csv` | paraphrases and role swaps used by `validate` |
| `eval_baseline.json` | frozen reference result, including evaluator accuracy |
| `requirements-eval.txt` | evaluator dependencies (scikit-learn) |
| `eval_review.csv` | per-claim verdicts of the last run (generated, not tracked) |
| `eval_validation_failures.csv` | wrongly judged validation cases of the last run (generated, not tracked) |
| `eval_plans/` | plan files written by `export` (generated, not tracked) |
