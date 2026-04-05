# Experiment Execution Plan

Last updated: 2026-04-05

This plan converts the current repository state into a single execution order for experiments, analysis, and write-up. The guiding principle is to finish the shortest path to defensible results before opening another partially implemented track.

## Recommended order

1. close out intrinsic packaging
2. close out register packaging
3. formalize toxicity as the next real experiment
4. build VAD as a fresh implementation track
5. write results and analysis once toxicity and VAD both have stable outputs

## Why this order

Intrinsic and register already have concrete artifacts. Toxicity has partial work and can become a formal experiment with less effort than starting VAD from nothing. VAD should not be treated as "analysis remaining"; it is still a build-and-run task.

## Issue-by-issue execution checklist

### Intrinsic validation (`#20`, `#40-#46`)

Target: convert existing validation outputs into paper-ready and reproducible artifacts.

Checklist:

- verify the exact commands that produced the current validation reports and confusion matrices
- export or regenerate the final figures in a stable location if needed
- summarize the main failure categories from `validation_report.txt`
- record the artifact paths and run commands for reproducibility
- update the paper with the actual intrinsic numbers instead of placeholders

Definition of done:

- paper-ready intrinsic table and figure set exists
- the run commands are documented
- the tracker reflects execution rather than planning

### Register (`#21`, `#47-#56`)

Target: turn the existing Brown experiment into a paper-ready result.

Checklist:

- verify that `code/scripts/exp_register.py` is the authoritative execution script
- document the Brown split, seed, feature normalization, and rare-label handling
- summarize final reported metrics from `results_summary.csv`
- create the Longman sanity analysis from the top TAMV features and confusion patterns
- add explicit reproducibility notes for the register run
- update the paper's register results subsection with actual numbers and a short interpretation

Definition of done:

- register metrics, confusion matrices, and interpretability artifacts are packaged
- the Longman comparison is explicitly written up
- the paper no longer treats register results as a placeholder

### Toxicity (`#22`, `#57-#66`)

Target: make toxicity the next fully formalized experiment.

Checklist:

- decide and document the analysis unit: utterance, turn, or thread
- define the final split protocol and leakage controls
- implement shared baselines needed from `#24`
- train the TAMV-based toxicity classifier with imbalance-aware settings
- evaluate with AUC, macro-F1, and PR-oriented metrics
- run slice analysis for derailed vs. civil and by thread position
- export the final figures and summary tables
- run robustness checks across seeds and threshold choices
- package reproducibility notes

Definition of done:

- toxicity results are based on the full intended dataset or a clearly documented final sample
- baselines and TAMV models are compared under the same split protocol
- exported artifacts are ready for direct insertion into the paper

### VAD (`#23`, `#67-#76`)

Target: treat VAD as a new build rather than a near-finished analysis.

Checklist:

- ingest and validate EmoBank
- decide the VAD analysis unit and split protocol
- construct TAMV feature vectors for that unit
- implement the mean-value and lexicon-only baselines
- train TAMV-based regression models for valence, arousal, and dominance
- evaluate with MAE, RMSE, Pearson, and Spearman per dimension
- export predicted-vs-true plots and residual plots
- run per-dimension error analysis and robustness checks
- package reproducibility notes

Definition of done:

- there is a runnable VAD pipeline in code
- all three dimensions are evaluated under the same protocol
- baseline comparisons are exported and ready for the paper

## Write-up sequencing (`#25`, `#30-#32`)

### Results section (`#30`)

Write only after:

- intrinsic numbers are stabilized
- register is packaged
- toxicity has formal metrics
- VAD has at least one TAMV model and one baseline

Suggested structure:

- intrinsic extraction reliability
- register prediction
- toxicity prediction
- VAD prediction

### Analysis section (`#31`)

Focus areas:

- why TAMV helps register more clearly than the other tasks
- which TAMV dimensions carry interpretable signal
- known extraction failures, especially mood/subjunctive cases
- where lexical or trajectory features appear necessary beyond TAMV alone

### Publication-ready artifacts (`#32`)

Bundle once the experiments are stable:

- intrinsic confusion matrices and summary table
- register confusion matrix and top-feature tables
- toxicity evaluation plots and slice analyses
- VAD per-dimension metric tables and regression plots

## Short operational recommendation

The next implementation cycle should be spent on toxicity, not VAD. Intrinsic and register should be documented and packaged immediately, because they already produce publishable evidence. VAD should start only after the toxicity protocol is fixed and baseline utilities are in place.
