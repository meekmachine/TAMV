# Experiment Status Reconciliation

Last updated: 2026-04-05

This note reconciles the current local repository state with the open GitHub issue tracker. The main mismatch is that several experiment artifacts already exist locally, while the corresponding planning and execution issues remain open on GitHub.

## High-level status

- `#20` intrinsic TAMV validation: largely implemented locally, but not yet fully packaged in the tracker.
- `#21` register prediction: implemented locally with reproducible script and exported artifacts, but still needs tracker reconciliation and paper-ready packaging.
- `#22` toxicity prediction: partially implemented as exploratory and pilot analysis; not yet a finalized paper-grade experiment.
- `#23` VAD prediction: planned in the paper and issue tracker, but not yet implemented in code.
- `#25` write-up epic: blocked on formalizing toxicity and building the VAD pipeline.

## Evidence already present in the repository

### Intrinsic TAMV validation (`#20`)

Local artifacts indicate that the intrinsic evaluation pipeline has already been run:

- `code/output/validation_report.txt`
- `code/output/confusion_tense.png`
- `code/output/confusion_aspect.png`
- `code/output/confusion_mood.png`
- `code/output/confusion_voice.png`
- `code/output/confusion_matrices_combined.png`
- `code/output/phrase_validation_report.txt`
- `code/output/phrase_confusion_matrices_combined.png`

Current intrinsic snapshot from `code/output/validation_report.txt`:

- overall accuracy: `83.1%`
- tense accuracy: `94.9%`
- aspect accuracy: `98.7%`
- mood accuracy: `91.1%`
- voice accuracy: `100.0%`

Tracker interpretation:

- `#40-#43` appear effectively complete in local artifacts.
- `#44` is partially complete because the validation report already identifies failure modes, especially subjunctive and related mood errors.
- `#45-#46` still need packaging and reproducibility-oriented cleanup.

### Register prediction (`#21`)

The Brown register experiment is implemented locally:

- script: `code/scripts/exp_register.py`
- outputs: `code/output/register_experiment/`

Key local artifacts:

- `results_summary.csv`
- `classification_report_logreg.csv`
- `classification_report_majority.csv`
- `classification_report_random_forest.csv`
- `confusion_matrix_logreg.png`
- `confusion_matrix_majority.png`
- `confusion_matrix_random_forest.png`
- `logreg_top_features.csv`
- `rf_feature_importance.csv`
- `run_info.json`

Current register snapshot from `results_summary.csv`:

- random forest: test accuracy `0.34`, macro-F1 `0.214`
- logistic regression: test accuracy `0.31`, macro-F1 `0.200`
- majority baseline: test accuracy `0.16`, macro-F1 `0.018`

Tracker interpretation:

- `#47-#48` appear complete enough for execution.
- `#49-#54` appear implemented locally.
- `#55` still needs an explicit Longman-aligned sanity write-up.
- `#56` still needs packaging and reproducibility notes.

### Toxicity prediction (`#22`)

There is substantial exploratory work, but not yet a finalized experiment pipeline:

- `code/output/test_cga/toxicity_analysis_report.txt`
- `code/output/utterance_wiki_analysis.txt`
- `code/output/cga_wiki_analysis.txt`
- `code/output/cga_wiki_speakers.tsv`
- several toxicity-oriented plots under `code/output/`

Current toxicity snapshot:

- there is pilot derailment modeling and TAMV-to-toxicity correlation analysis
- one report is based on only `30` conversations, which is not a final experimental basis
- the utterance-level wiki analysis is informative, but correlational rather than the final classifier/evaluation pipeline described in the issues

Tracker interpretation:

- `#57-#59` are partially explored, but not yet locked down as a formal protocol.
- `#60-#65` remain the core implementation/evaluation work.
- `#66` remains packaging.

### VAD prediction (`#23`)

VAD currently exists in the paper design and issue tracker, not in the codebase.

Observed state:

- `main.tex` references EmoBank and the NRC VAD Lexicon
- no VAD datasets were found under `code/`
- no VAD-specific scripts or outputs were found under `code/src/`, `code/scripts/`, or `code/output/`

Tracker interpretation:

- `#67-#76` should be treated as an unstarted implementation track.

## Recommended issue-state interpretation

The most accurate reading of the tracker is not that every experiment is unstarted. It is:

- intrinsic: executed, needs packaging
- register: executed, needs packaging and Longman comparison write-up
- toxicity: partially explored, needs formal experiment pipeline
- VAD: not started in code

## Immediate tracker actions

1. Comment on `#20` with links to existing intrinsic artifacts and note that packaging/reproducibility remain open.
2. Comment on `#21` with links to the Brown register script and exported artifacts, plus the current summary metrics.
3. Comment on `#22` clarifying that existing outputs are exploratory and do not yet satisfy the issue's formal experiment criteria.
4. Comment on `#23` clarifying that VAD is still pending implementation.
5. Comment on `#25` explaining that write-up work should proceed after toxicity is formalized and the VAD pipeline exists.
