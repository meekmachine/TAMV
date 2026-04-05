# Toxicity Protocol

This document defines the primary experimental protocol for toxicity prediction on the Conversations Gone Awry (CGA) corpus.

## Primary choices

- Primary dataset: `CGA-WIKI`
- Primary analysis unit: conversation/thread
- Primary target: binary derailment label from the conversation metadata
- Primary split rule: split by conversation id before any utterance- or turn-level expansion

## Rationale

The CGA derailment label is defined at the conversation level, so the primary supervised task should also be defined at the conversation level. This keeps the label aligned with the modeling unit and prevents leakage that would occur if utterances from the same conversation were scattered across train and test splits.

Utterance- and turn-level signals remain useful, but they belong in later feature engineering and exploratory analysis:

- utterance-level toxicity can support descriptive correlation studies
- turn windows can support trajectory features
- both must be derived only after the conversation-level split has already been fixed

## Label policy

Use the conversation-level derailment flag exposed by ConvoKit:

- prefer `conversation_has_personal_attack`
- fall back to `has_derailed` if needed

This produces a binary target:

- `1`: derailed
- `0`: civil

## Filtering

Exclude conversations with fewer than `2` utterances. These are too short to support a conversational derailment framing and are also poor candidates for later trajectory features.

## Split protocol

Use deterministic stratified conversation-level splits:

- train: `70%`
- dev: `15%`
- test: `15%`
- seed: `42`

Validation requirements:

- no conversation id appears in more than one split
- each split contains both derailed and civil conversations
- the emitted manifest is the authoritative source for downstream toxicity experiments

## Command

```bash
cd code
python -m src toxicity-protocol --dataset wiki
```

By default this writes artifacts under `code/output/toxicity_protocol/`:

- `cga_wiki_protocol_report.txt`
- `cga_wiki_split_manifest.tsv`
- `cga_wiki_train.tsv`
- `cga_wiki_dev.tsv`
- `cga_wiki_test.tsv`
- `cga_wiki_protocol_config.json`
- `cga_wiki_split_summary.json`

## Relationship to later issues

- `#57`: defines the protocol and produces the deterministic split manifest
- `#58`: builds TAMV features against this manifest
- `#59`: adds trajectory features within the already fixed conversation split
- `#60-#66`: train, evaluate, analyze, and package against this protocol
