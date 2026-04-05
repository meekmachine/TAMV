#!/usr/bin/env python3
"""
Toxicity protocol curation for the CGA corpus.

Defines the primary analysis unit, label policy, and deterministic split
protocol for the toxicity experiment.

Usage:
    python -m src toxicity-protocol --dataset wiki
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd
from sklearn.model_selection import train_test_split

from .corpus_loaders import CGALoader, Conversation


@dataclass
class ProtocolConfig:
    dataset: str
    seed: int
    train_size: float
    dev_size: float
    test_size: float
    min_turns: int


@dataclass
class SplitStats:
    split: str
    conversations: int
    derailed: int
    civil: int
    derailment_rate: float
    mean_turns: float
    median_turns: float
    mean_max_toxicity: float
    toxicity_coverage_rate: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Curate the CGA toxicity protocol and emit deterministic split manifests."
    )
    parser.add_argument("--dataset", choices=["wiki", "cmv"], default="wiki")
    parser.add_argument("--output-dir", type=Path, default=Path("output/toxicity_protocol"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--train-size", type=float, default=0.7)
    parser.add_argument("--dev-size", type=float, default=0.15)
    parser.add_argument("--test-size", type=float, default=0.15)
    parser.add_argument(
        "--min-turns",
        type=int,
        default=2,
        help="Exclude conversations shorter than this many utterances.",
    )
    return parser.parse_args()


def build_protocol_frame(conversations: Iterable[Conversation], min_turns: int) -> pd.DataFrame:
    rows: list[dict] = []
    for convo in conversations:
        num_turns = len(convo.utterances)
        if num_turns < min_turns:
            continue

        rows.append(
            {
                "conversation_id": convo.id,
                "label": "derailed" if convo.has_derailed else "civil",
                "label_binary": int(convo.has_derailed),
                "num_turns": num_turns,
                "num_toxicity_scored_utterances": len(convo.toxicity_scores),
                "max_toxicity": float(convo.max_toxicity),
                "mean_toxicity": float(convo.mean_toxicity),
                "has_toxicity_scores": bool(convo.toxicity_scores),
            }
        )

    frame = pd.DataFrame(rows).sort_values("conversation_id").reset_index(drop=True)
    if frame.empty:
        raise ValueError("No conversations matched the protocol filters.")
    return frame


def assign_splits(frame: pd.DataFrame, config: ProtocolConfig) -> pd.DataFrame:
    if round(config.train_size + config.dev_size + config.test_size, 6) != 1.0:
        raise ValueError("train/dev/test sizes must sum to 1.0")

    train_ids, holdout_ids = train_test_split(
        frame["conversation_id"],
        train_size=config.train_size,
        random_state=config.seed,
        stratify=frame["label_binary"],
    )

    holdout = frame.set_index("conversation_id").loc[holdout_ids].reset_index()
    dev_fraction_of_holdout = config.dev_size / (config.dev_size + config.test_size)

    dev_ids, test_ids = train_test_split(
        holdout["conversation_id"],
        train_size=dev_fraction_of_holdout,
        random_state=config.seed,
        stratify=holdout["label_binary"],
    )

    split_map = {cid: "train" for cid in train_ids}
    split_map.update({cid: "dev" for cid in dev_ids})
    split_map.update({cid: "test" for cid in test_ids})

    manifest = frame.copy()
    manifest["split"] = manifest["conversation_id"].map(split_map)

    if manifest["split"].isna().any():
        raise ValueError("Split assignment left some conversations unassigned.")

    if manifest["conversation_id"].duplicated().any():
        raise ValueError("Conversation IDs must be unique in the split manifest.")

    return manifest.sort_values(["split", "conversation_id"]).reset_index(drop=True)


def summarize_split(frame: pd.DataFrame, split: str) -> SplitStats:
    subset = frame[frame["split"] == split].copy()
    derailed = int(subset["label_binary"].sum())
    total = int(len(subset))
    civil = total - derailed
    return SplitStats(
        split=split,
        conversations=total,
        derailed=derailed,
        civil=civil,
        derailment_rate=(derailed / total) if total else 0.0,
        mean_turns=float(subset["num_turns"].mean()) if total else 0.0,
        median_turns=float(subset["num_turns"].median()) if total else 0.0,
        mean_max_toxicity=float(subset["max_toxicity"].mean()) if total else 0.0,
        toxicity_coverage_rate=float(subset["has_toxicity_scores"].mean()) if total else 0.0,
    )


def validate_manifest(frame: pd.DataFrame) -> list[str]:
    issues: list[str] = []
    split_sets = {
        split: set(frame.loc[frame["split"] == split, "conversation_id"])
        for split in ["train", "dev", "test"]
    }

    if split_sets["train"] & split_sets["dev"]:
        issues.append("train/dev overlap detected")
    if split_sets["train"] & split_sets["test"]:
        issues.append("train/test overlap detected")
    if split_sets["dev"] & split_sets["test"]:
        issues.append("dev/test overlap detected")

    for split in ["train", "dev", "test"]:
        labels = set(frame.loc[frame["split"] == split, "label_binary"])
        if labels != {0, 1}:
            issues.append(f"{split} split is missing one of the two label classes")

    return issues


def render_report(config: ProtocolConfig, manifest: pd.DataFrame, split_stats: list[SplitStats]) -> str:
    analysis_unit = "conversation/thread"
    label_name = "conversation_has_personal_attack / has_derailed"
    lines = [
        "=" * 72,
        f"CGA TOXICITY PROTOCOL SUMMARY ({config.dataset.upper()})",
        "=" * 72,
        "",
        "PRIMARY DECISIONS",
        "-" * 40,
        f"Primary analysis unit: {analysis_unit}",
        f"Primary label:         {label_name}",
        "Primary task:          binary derailment classification",
        "Leakage policy:        split by conversation id before any turn/utterance feature expansion",
        "Auxiliary analyses:    utterance/turn-level toxicity remains descriptive, not the primary supervised target",
        "",
        "FILTERS",
        "-" * 40,
        f"Minimum turns:         {config.min_turns}",
        "",
        "SPLIT CONFIGURATION",
        "-" * 40,
        f"Seed:                  {config.seed}",
        f"Train/dev/test:        {config.train_size:.2f} / {config.dev_size:.2f} / {config.test_size:.2f}",
        "",
        "DATASET SUMMARY",
        "-" * 40,
        f"Conversations kept:    {len(manifest)}",
        f"Derailed:              {int(manifest['label_binary'].sum())}",
        f"Civil:                 {int((1 - manifest['label_binary']).sum())}",
        f"Derailment rate:       {manifest['label_binary'].mean():.4f}",
        f"Mean turns:            {manifest['num_turns'].mean():.2f}",
        f"Median turns:          {manifest['num_turns'].median():.2f}",
        f"Toxicity coverage:     {manifest['has_toxicity_scores'].mean():.4f}",
        "",
        "SPLIT SUMMARY",
        "-" * 40,
    ]

    for stats in split_stats:
        lines.extend(
            [
                f"{stats.split.upper()}",
                f"  conversations:       {stats.conversations}",
                f"  derailed / civil:    {stats.derailed} / {stats.civil}",
                f"  derailment rate:     {stats.derailment_rate:.4f}",
                f"  mean turns:          {stats.mean_turns:.2f}",
                f"  median turns:        {stats.median_turns:.2f}",
                f"  mean max toxicity:   {stats.mean_max_toxicity:.4f}",
                f"  toxicity coverage:   {stats.toxicity_coverage_rate:.4f}",
                "",
            ]
        )

    lines.extend(
        [
            "RATIONALE",
            "-" * 40,
            "Conversation/thread level is the primary supervised unit because the label is defined at the conversation level in CGA.",
            "This avoids leakage from placing utterances from the same conversation into different splits.",
            "Turn- and utterance-level toxicity signals remain useful for exploratory analysis and later trajectory features,",
            "but they should be derived only after the conversation-level split has already been fixed.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    config = ProtocolConfig(
        dataset=args.dataset,
        seed=args.seed,
        train_size=args.train_size,
        dev_size=args.dev_size,
        test_size=args.test_size,
        min_turns=args.min_turns,
    )

    loader = CGALoader(dataset=args.dataset)
    manifest = build_protocol_frame(loader.load(), min_turns=args.min_turns)
    manifest = assign_splits(manifest, config)

    issues = validate_manifest(manifest)
    if issues:
        raise ValueError("Protocol validation failed: " + "; ".join(issues))

    split_stats = [summarize_split(manifest, split) for split in ["train", "dev", "test"]]
    report = render_report(config, manifest, split_stats)

    stem = f"cga_{args.dataset}"
    manifest.to_csv(args.output_dir / f"{stem}_split_manifest.tsv", sep="\t", index=False)
    for split in ["train", "dev", "test"]:
        manifest.loc[manifest["split"] == split].to_csv(
            args.output_dir / f"{stem}_{split}.tsv",
            sep="\t",
            index=False,
        )

    with open(args.output_dir / f"{stem}_protocol_report.txt", "w", encoding="utf-8") as handle:
        handle.write(report)
    with open(args.output_dir / f"{stem}_protocol_config.json", "w", encoding="utf-8") as handle:
        json.dump(asdict(config), handle, indent=2)
    with open(args.output_dir / f"{stem}_split_summary.json", "w", encoding="utf-8") as handle:
        json.dump([asdict(stats) for stats in split_stats], handle, indent=2)

    print(report)
    print(f"Artifacts written to {args.output_dir}")


if __name__ == "__main__":
    main()
