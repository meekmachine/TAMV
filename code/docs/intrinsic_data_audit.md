# Intrinsic Data Audit

This note records what intrinsic data is actually available in the repository, what came from the TMV-annotator project, and why the current external comparison is useful but limited.

## Available intrinsic sources

### 1. Curated TAMV gold suites

- `code/data/synthetic_expected.tsv`: `83` labeled verb instances
  - `40` rows labeled `User test data`
  - `25` rows labeled `Brown corpus`
  - `18` rows labeled `Longman Grammar (Ch. 5-6)`
- `code/data/phrase_test_expected.json`: `32` phrase-level cases

These files are the current direct TAMV gold resources in the repo.

### 2. TMV-annotator GitHub sample

The upstream TMV-annotator GitHub repository publishes a small English Mate-parsed sample and TMV output:

- `example-outputs/en.parsed`
- `tmv-annotator-tool/output/en.parsed.verbs`

The local repo vendors that sample as:

- `code/data/europarl_sentences.txt`
- `code/data/europarl_expected.tsv`
- `code/data/europarl_tamv.tsv`

This sample contains:

- `25` sentences
- `35` TMV rows total
- `27` finite rows after local TMV->TAMV conversion

Important: this is a comparison against TMV-annotator output, not a direct human-gold TAMV corpus.

## Why the old “full Europarl” path is not reproducible

The upstream GitHub repo points to a separate Dropbox archive for a larger Europarl corpus. That archive is no longer accessible from the original URL, and the local repo never versioned the reference bundle itself.

The repo also ignores `tmv_annotator_reference/` at the root, so any local copy of the upstream reference materials would not have been committed by default.

## Is the GitHub sample statistically strong enough?

No, not as a headline intrinsic benchmark.

Current TMV alignment figures on the GitHub sample:

- Detection: `27/35 = 77.1%`
  - 95% Wilson CI: `61.0%` to `87.9%`
- Full TAMV match among matched finite rows: `26/27 = 96.3%`
  - 95% Wilson CI: `81.7%` to `99.3%`

Why this is not strong enough on its own:

- Only `27` finite comparable rows are available after conversion.
- The sample is small and not demonstrably representative.
- The comparison target is TMV-annotator system output, not independent human TAMV gold.

So the GitHub sample is useful as an external compatibility check, but not sufficient as the sole intrinsic claim.

## Other realistic data sources

### Universal Dependencies English treebanks

Official index: <https://universaldependencies.org/en/index.html>

Pros:

- Openly accessible
- Broad genre coverage
- Gold syntax and morphology

Cons:

- Not already labeled with this project’s TAMV scheme
- Requires manual TAMV annotation or a carefully reviewed conversion layer

### PropBank / OntoNotes-style inflection fields

The Ramm et al. paper notes that PropBank includes inflectional information for tense, aspect, and voice, but not all moods; subjunctive constructions are especially under-covered. These resources are also distributed through LDC rather than openly mirrored on GitHub.

Pros:

- Larger and more systematic than the current GitHub TMV sample
- Useful for partial validation of tense/aspect/voice

Cons:

- Not a full TAMV benchmark in the current label scheme
- Access is license-gated
- Mood coverage is incomplete

### TimeBank / TimeML-style corpora

These are useful for tense/aspect and event-time evaluation, but they are not direct TAMV resources and are weaker for voice and mood.

## Recommended interpretation

- Keep the curated single-verb and phrase suites as direct TAMV stress tests.
- Keep the GitHub TMV sample as a separate external compatibility check.
- Do not present the GitHub sample as if it were a large hand-annotated gold corpus.
- If a stronger benchmark is needed, the best next open path is to annotate a new TAMV subset from UD English treebanks.
