# Register Longman Sanity Analysis

This analysis compares the current Brown register experiment outputs against the register tendencies documented in Longman Grammar of Spoken and Written English.

## Inputs

- `results_summary.csv`
- `logreg_top_features.csv`
- `run_info.json`

## What it checks

- whether the strongest positive coefficients for each Brown genre are compatible with the expected register family
- whether expository genres surface present/perfect/passive cues
- whether narrative genres suppress present-simple dominance and emphasize past-tense framing

## Output

Run:

```bash
python code/scripts/register_longman_sanity.py --input-dir /Users/frankabugnail/TAMV/code/output/register_experiment
```

This writes:

- `code/output/register_longman_analysis/longman_sanity_report.txt`
- `code/output/register_longman_analysis/longman_sanity_summary.csv`
- `code/output/register_longman_analysis/longman_sanity_metadata.json`

The report is intentionally conservative: it treats Longman as a register benchmark, not as a prediction target, and uses it only as a sanity check for the learned TAMV feature weights.
