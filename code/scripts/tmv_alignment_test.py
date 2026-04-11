#!/usr/bin/env python3
"""Compare the local spaCy extractor against the GitHub-published TMV sample.

This script evaluates compatibility with the English TMV-annotator sample that
is published directly in the upstream GitHub repository:

- example-outputs/en.parsed
- tmv-annotator-tool/output/en.parsed.verbs

The local repo vendors sentence text and TMV rows derived from that sample in:

- code/data/europarl_sentences.txt
- code/data/europarl_expected.tsv
- code/data/europarl_tamv.tsv

The comparison is intentionally separate from the curated intrinsic gold suite:
it measures agreement with TMV-annotator output on a small Mate-parsed sample,
not direct agreement with human TAMV annotations.
"""

from __future__ import annotations

import argparse
import csv
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path


CODE_DIR = Path(__file__).resolve().parents[1]
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from src.tamv_extractor import TAMVExtractor, TAMVLabel  # noqa: E402


@dataclass
class TmvRow:
    sentence_index: int
    verb: str
    is_finite: bool
    tmv_tense: str
    tmv_mood: str
    tmv_voice: str
    progressive: str


@dataclass
class ConvertedRow:
    sentence_index: int
    verb: str
    tense: str
    aspect: str
    mood: str
    voice: str

    def label(self) -> str:
        return "-".join(
            [
                self.tense.lower(),
                self.aspect.lower().replace("_", "-"),
                self.mood.lower(),
                self.voice.lower(),
            ]
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run TMV alignment on the GitHub-published Mate sample.")
    parser.add_argument("--sentences", type=Path, default=CODE_DIR / "data" / "europarl_sentences.txt")
    parser.add_argument("--tmv-rows", type=Path, default=CODE_DIR / "data" / "europarl_expected.tsv")
    parser.add_argument("--converted-gold", type=Path, default=CODE_DIR / "data" / "europarl_tamv.tsv")
    parser.add_argument("--report", type=Path, default=CODE_DIR / "output" / "tmv_alignment_report.txt")
    parser.add_argument("--mismatches", type=Path, default=CODE_DIR / "output" / "tmv_alignment_mismatches.tsv")
    parser.add_argument("--model", default="en_core_web_sm")
    return parser.parse_args()


def normalize_token(text: str) -> str:
    return re.sub(r"[^a-z]+", "", text.lower())


def load_sentences(path: Path) -> dict[int, str]:
    with path.open("r", encoding="utf-8") as handle:
        return {
            index: line.strip()
            for index, line in enumerate(handle, start=1)
            if line.strip()
        }


def load_tmv_rows(path: Path) -> list[TmvRow]:
    rows: list[TmvRow] = []
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.reader(handle, delimiter="\t")
        for raw in reader:
            if not raw:
                continue
            rows.append(
                TmvRow(
                    sentence_index=int(raw[0]),
                    verb=raw[4],
                    is_finite=raw[3] == "yes" and raw[5] != "-",
                    tmv_tense=raw[5],
                    tmv_mood=raw[6],
                    tmv_voice=raw[7],
                    progressive=raw[8],
                )
            )
    return rows


def load_converted_rows(path: Path) -> list[ConvertedRow]:
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return [
            ConvertedRow(
                sentence_index=int(row["index"]),
                verb=row["verb"],
                tense=row["tense"],
                aspect=row["aspect"],
                mood=row["mood"],
                voice=row["voice"],
            )
            for row in reader
        ]


def tmv_compatible_label(label: TAMVLabel) -> str:
    mood = label.mood.value
    if mood == "modal":
        auxiliaries = {aux.lower() for aux in label.auxiliary_chain}
        if auxiliaries & {"would", "could", "should", "might"}:
            mood = "subjunctive"
        else:
            mood = "indicative"
    return "-".join([label.tense.value, label.aspect.value, mood, label.voice.value])


def match_label(verb: str, labels: list[TAMVLabel]) -> TAMVLabel | None:
    gold = normalize_token(verb)
    for label in labels:
        candidates = [
            normalize_token(label.verb_text),
            normalize_token(label.verb_lemma),
            *[normalize_token(aux) for aux in label.auxiliary_chain],
        ]
        if gold in candidates:
            return label
        if any(gold and candidate and (gold in candidate or candidate in gold) for candidate in candidates):
            return label
    return None


def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total == 0:
        return 0.0, 0.0
    phat = successes / total
    denom = 1.0 + (z * z / total)
    center = (phat + (z * z) / (2 * total)) / denom
    margin = (z * math.sqrt((phat * (1 - phat) + (z * z) / (4 * total)) / total)) / denom
    return center - margin, center + margin


def main() -> None:
    args = parse_args()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.mismatches.parent.mkdir(parents=True, exist_ok=True)

    sentences = load_sentences(args.sentences)
    tmv_rows = load_tmv_rows(args.tmv_rows)
    converted_rows = load_converted_rows(args.converted_gold)
    extractor = TAMVExtractor(model=args.model)

    sentence_labels: dict[int, list[TAMVLabel]] = {
        index: extractor.extract_from_text(sentence)
        for index, sentence in sentences.items()
    }

    matched_rows: list[tuple[ConvertedRow, TAMVLabel]] = []
    mismatches: list[dict[str, str]] = []
    missing_rows: list[ConvertedRow] = []
    dimension_correct = {"tense": 0, "aspect": 0, "mood": 0, "voice": 0, "full": 0}

    for row in converted_rows:
        labels = sentence_labels.get(row.sentence_index, [])
        label = match_label(row.verb, labels)
        if label is None:
            missing_rows.append(row)
            continue

        matched_rows.append((row, label))
        compatible = tmv_compatible_label(label)
        gold = row.label()
        predicted_parts = compatible.split("-")
        gold_parts = gold.split("-")
        tense_pred, aspect_pred = predicted_parts[0], "-".join(predicted_parts[1:-2])
        mood_pred, voice_pred = predicted_parts[-2], predicted_parts[-1]
        tense_gold, aspect_gold = gold_parts[0], "-".join(gold_parts[1:-2])
        mood_gold, voice_gold = gold_parts[-2], gold_parts[-1]

        if tense_pred == tense_gold:
            dimension_correct["tense"] += 1
        if aspect_pred == aspect_gold:
            dimension_correct["aspect"] += 1
        if mood_pred == mood_gold:
            dimension_correct["mood"] += 1
        if voice_pred == voice_gold:
            dimension_correct["voice"] += 1
        if compatible == gold:
            dimension_correct["full"] += 1
        else:
            mismatches.append(
                {
                    "sentence_index": str(row.sentence_index),
                    "sentence": sentences[row.sentence_index],
                    "verb": row.verb,
                    "gold_label": gold,
                    "predicted_label": compatible,
                    "predicted_verb_text": label.verb_text,
                    "predicted_lemma": label.verb_lemma,
                    "auxiliary_chain": " ".join(label.auxiliary_chain),
                }
            )

    detection_lo, detection_hi = wilson_interval(len(matched_rows), len(tmv_rows))
    full_lo, full_hi = wilson_interval(dimension_correct["full"], len(matched_rows))

    report_lines = [
        "TMV ALIGNMENT REPORT",
        "=" * 70,
        "",
        "Reference sample: GitHub-published English Mate/TMV sample from the TMV-annotator repository",
        "",
        f"Sentence count: {len(sentences)}",
        f"Total TMV-annotator rows: {len(tmv_rows)}",
        f"Comparable finite rows after TMV->TAMV conversion: {len(converted_rows)}",
        f"Matched verbs: {len(matched_rows)}",
        f"Detection rate: {len(matched_rows) / len(tmv_rows):.1%}",
        f"  95% Wilson CI: [{detection_lo:.1%}, {detection_hi:.1%}]",
        "",
        "Alignment by dimension on matched verbs:",
        f"  Tense:  {dimension_correct['tense'] / len(matched_rows):.1%}",
        f"  Aspect: {dimension_correct['aspect'] / len(matched_rows):.1%}",
        f"  Mood:   {dimension_correct['mood'] / len(matched_rows):.1%}",
        f"  Voice:  {dimension_correct['voice'] / len(matched_rows):.1%}",
        f"  Full:   {dimension_correct['full'] / len(matched_rows):.1%}",
        f"  Full-match 95% Wilson CI: [{full_lo:.1%}, {full_hi:.1%}]",
        "",
        "Comparison policy:",
        "- Non-finite TMV rows are excluded from the TAMV alignment denominator because the local conversion only maps finite TMV rows.",
        "- Local MODAL labels are collapsed back to TMV-compatible indicative/subjunctive values for this comparison only.",
        "",
        "ALL MISMATCHES:",
        "-" * 70,
        "",
    ]

    if mismatches:
        for row in mismatches:
            report_lines.extend(
                [
                    f"Sentence {row['sentence_index']}: {row['sentence'][:70]}",
                    f"  Verb: {row['verb']}",
                    f"  TMV (mapped):  {row['gold_label']}",
                    f"  Our extractor: {row['predicted_label']}",
                    "",
                ]
            )
    else:
        report_lines.append("None")

    report_lines.extend(
        [
            "",
            "UNMATCHED CONVERTED ROWS:",
            "-" * 70,
            "",
        ]
    )
    if missing_rows:
        for row in missing_rows:
            report_lines.append(f"Sentence {row.sentence_index}: {row.verb} ({row.label()})")
    else:
        report_lines.append("None")

    args.report.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    with args.mismatches.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "sentence_index",
                "sentence",
                "verb",
                "gold_label",
                "predicted_label",
                "predicted_verb_text",
                "predicted_lemma",
                "auxiliary_chain",
            ],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(mismatches)

    print(f"Wrote report to {args.report}")
    print(f"Wrote mismatch table to {args.mismatches}")


if __name__ == "__main__":
    main()
