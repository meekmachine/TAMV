# Intrinsic TAMV Reproducibility

This note records the commands and artifact locations for the intrinsic TAMV validation track.

The intrinsic package has two different evaluation modes:

- Curated TAMV gold suites: single-verb and phrase-level regression/stress tests.
- TMV alignment sample: a small GitHub-published Mate/TMV comparison sample from Ramm et al.'s TMV-annotator repository.

## Commands

Run the single-verb validation:

```bash
cd code
python -m tests.validate_tamv --no-show
```

Run the phrase-level validation:

```bash
cd code
python -m tests.validate_phrases --no-show
```

Run the GitHub-sample TMV alignment check:

```bash
python code/scripts/tmv_alignment_test.py
```

## Expected artifacts

The validation scripts write their outputs under `code/output/`:

- `validation_report.txt`
- `confusion_tense.png`
- `confusion_aspect.png`
- `confusion_mood.png`
- `confusion_voice.png`
- `confusion_matrices_combined.png`
- `phrase_validation_report.txt`
- `phrase_confusion_tense.png`
- `phrase_confusion_aspect.png`
- `phrase_confusion_mood.png`
- `phrase_confusion_voice.png`
- `phrase_confusion_matrices_combined.png`
- `tmv_alignment_report.txt`
- `tmv_alignment_mismatches.tsv`

## Interpretation notes

- The single-verb report is the primary intrinsic evaluation summary.
- The phrase-level report is the stricter structural check for multi-verb and span-matching cases.
- The TMV alignment report is an external compatibility check against the GitHub-published TMV-annotator sample. It is not a human-gold TAMV benchmark.
- The main known failure modes remain subjunctive, conditional, and a few non-finite or negation-heavy constructions.
- The GitHub TMV sample is small (`25` sentences, `35` TMV rows, `27` finite comparable rows) and should be treated as a sanity check, not as a statistically strong standalone benchmark.

## Paper-facing file set

When the intrinsic outputs are packaged for the manuscript, the bundle should include the reports above plus the corresponding confusion-matrix figures in a stable directory layout.
