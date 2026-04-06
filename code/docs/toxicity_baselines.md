# Toxicity Baselines

This document defines the two baseline models for the CGA toxicity experiment.

## Models

- `majority`: predicts the most frequent label observed in the training split
- `lexicon`: counts a small set of toxicity cue words and classifies conversations using a train-tuned threshold

## Protocol

The baselines follow the conversation-level CGA split protocol from issue `#57` when that manifest is available. If the manifest is not present yet, the script generates an equivalent deterministic conversation-level split with:

- train: `70%`
- dev: `15%`
- test: `15%`
- seed: `42`
- minimum turns: `2`

The split is defined at the conversation level so that no utterance from a conversation leaks across train/dev/test.

## Command

```bash
cd code
python -m src toxicity-baselines --dataset wiki
```

Optional explicit manifest:

```bash
cd code
python -m src toxicity-baselines --dataset wiki --split-manifest output/toxicity_protocol/cga_wiki_split_manifest.tsv
```

## Outputs

- `results_summary.csv`
- `classification_report_majority.csv`
- `classification_report_lexicon.csv`
- `confusion_matrix_majority.png`
- `confusion_matrix_lexicon.png`
- `test_predictions.tsv`
- `baseline_report.txt`
- `run_info.json`
