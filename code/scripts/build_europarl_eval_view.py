#!/usr/bin/env python3
"""
Build a sentence-level Europarl evaluation view.

Output format (JSONL):
- index: sentence index from Europarl source
- sentence: full untokenized sentence text
- gold_annotations: list of TAMV gold rows for that sentence

This file is intended as the input index for running spaCy parsing and then
comparing system predictions against sentence-aligned TAMV gold labels.
"""

import argparse
import csv
import json
from pathlib import Path


DATA_DIR = Path(__file__).parent.parent / "data"
DEFAULT_SENTENCES = DATA_DIR / "europarl_sentences.txt"
DEFAULT_GOLD = DATA_DIR / "europarl_tamv.tsv"
DEFAULT_OUTPUT = DATA_DIR / "europarl_eval.jsonl"


def load_sentences(path: Path) -> dict[int, str]:
    with open(path, "r", encoding="utf-8") as handle:
        return {
            idx: line.strip()
            for idx, line in enumerate(handle, start=1)
            if line.strip()
        }


def load_gold(path: Path) -> dict[int, list[dict[str, str]]]:
    grouped: dict[int, list[dict[str, str]]] = {}
    with open(path, "r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            sent_idx = int(row["index"])
            grouped.setdefault(sent_idx, []).append(
                {
                    "verb": row["verb"],
                    "tense": row["tense"],
                    "aspect": row["aspect"],
                    "mood": row["mood"],
                    "voice": row["voice"],
                    "category": row["category"],
                    "source": row["source"],
                }
            )
    return grouped


def build_eval_rows(
    sentences: dict[int, str],
    gold: dict[int, list[dict[str, str]]],
    include_all_sentences: bool = True,
) -> list[dict]:
    indices = sorted(sentences) if include_all_sentences else sorted(gold)
    rows: list[dict] = []
    for idx in indices:
        if idx not in sentences:
            raise ValueError(f"Sentence index {idx} missing from sentence source file")
        rows.append(
            {
                "index": idx,
                "sentence": sentences[idx],
                "gold_annotations": gold.get(idx, []),
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Build sentence-level Europarl evaluation JSONL.")
    parser.add_argument("--sentences", type=Path, default=DEFAULT_SENTENCES)
    parser.add_argument("--gold", type=Path, default=DEFAULT_GOLD)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--gold-only",
        action="store_true",
        help="Only include sentence indices that have TAMV gold annotations.",
    )
    args = parser.parse_args()

    sentences = load_sentences(args.sentences)
    gold = load_gold(args.gold)
    rows = build_eval_rows(
        sentences=sentences,
        gold=gold,
        include_all_sentences=not args.gold_only,
    )

    with open(args.output, "w", encoding="utf-8") as out:
        for row in rows:
            out.write(json.dumps(row, ensure_ascii=True) + "\n")

    print(f"Wrote {len(rows)} rows to {args.output}")
    print(f"Gold-bearing sentences: {len(gold)}")
    print(f"Total sentence lines available: {len(sentences)}")


if __name__ == "__main__":
    main()
