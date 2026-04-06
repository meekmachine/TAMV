#!/usr/bin/env python3
"""Majority and lexicon-style toxicity baselines for CGA."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split

from .corpus_loaders import CGALoader, Conversation


TOXIC_LEXICON: Dict[str, float] = {
    "abuse": 1.2,
    "abusive": 1.4,
    "asshole": 2.4,
    "bigot": 2.0,
    "bitch": 2.1,
    "bullshit": 2.2,
    "crap": 0.9,
    "dumb": 1.2,
    "fool": 1.0,
    "fuck": 2.8,
    "garbage": 1.1,
    "hate": 1.6,
    "idiot": 2.0,
    "jerk": 1.1,
    "liar": 1.6,
    "loser": 1.4,
    "moron": 2.2,
    "nonsense": 0.8,
    "pathetic": 1.5,
    "racist": 2.3,
    "sexist": 2.3,
    "shit": 2.4,
    "stupid": 1.9,
    "troll": 1.7,
    "ugly": 1.0,
    "worthless": 1.8,
}


@dataclass
class BaselineConfig:
    dataset: str
    seed: int
    min_turns: int
    split_manifest: str | None
    threshold: float | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run CGA toxicity baselines.")
    parser.add_argument("--dataset", choices=["wiki", "cmv"], default="wiki")
    parser.add_argument("--output-dir", type=Path, default=Path("output/toxicity_baselines"))
    parser.add_argument("--split-manifest", type=Path, default=Path("output/toxicity_protocol/cga_wiki_split_manifest.tsv"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--min-turns", type=int, default=2)
    parser.add_argument("--threshold", type=float, default=None, help="Override lexicon decision threshold.")
    return parser.parse_args()


def normalize_text(text: str) -> list[str]:
    return re.findall(r"[a-z']+", text.lower())


def build_conversation_frame(conversations: Iterable[Conversation], min_turns: int) -> pd.DataFrame:
    rows: list[dict] = []
    for convo in conversations:
        if len(convo.utterances) < min_turns:
            continue
        rows.append(
            {
                "conversation_id": convo.id,
                "text": convo.full_text,
                "label": int(convo.has_derailed),
                "label_name": "derailed" if convo.has_derailed else "civil",
                "num_turns": len(convo.utterances),
                "toxicity_coverage": len(convo.toxicity_scores) / len(convo.utterances) if convo.utterances else 0.0,
            }
        )
    frame = pd.DataFrame(rows).sort_values("conversation_id").reset_index(drop=True)
    if frame.empty:
        raise ValueError("No conversations available after filtering.")
    return frame


def build_default_split_manifest(frame: pd.DataFrame, seed: int) -> pd.DataFrame:
    train_ids, holdout_ids = train_test_split(
        frame["conversation_id"],
        train_size=0.7,
        random_state=seed,
        stratify=frame["label"],
    )
    holdout = frame.set_index("conversation_id").loc[holdout_ids].reset_index()
    dev_ids, test_ids = train_test_split(
        holdout["conversation_id"],
        train_size=0.5,
        random_state=seed,
        stratify=holdout["label"],
    )
    split_map = {cid: "train" for cid in train_ids}
    split_map.update({cid: "dev" for cid in dev_ids})
    split_map.update({cid: "test" for cid in test_ids})
    manifest = frame.copy()
    manifest["split"] = manifest["conversation_id"].map(split_map)
    if manifest["split"].isna().any():
        raise ValueError("Unassigned split rows detected.")
    return manifest


def load_split_manifest(path: Path | None, frame: pd.DataFrame, seed: int) -> pd.DataFrame:
    if path and path.exists():
        manifest = pd.read_csv(path, sep="\t")
        required = {"conversation_id", "split"}
        if not required.issubset(manifest.columns):
            raise ValueError(f"Split manifest must contain columns: {sorted(required)}")
        if "label_binary" in manifest.columns:
            manifest["label"] = manifest["label_binary"].astype(int)
        elif "label" in manifest.columns:
            if manifest["label"].dtype == object:
                manifest["label"] = manifest["label"].map({"civil": 0, "derailed": 1}).astype(int)
            else:
                manifest["label"] = manifest["label"].astype(int)
        else:
            manifest = manifest.merge(
                frame[["conversation_id", "label", "label_name", "text", "num_turns", "toxicity_coverage"]],
                on="conversation_id",
                how="left",
            )
        if "label_name" not in manifest.columns:
            manifest["label_name"] = manifest["label"].map({0: "civil", 1: "derailed"})
        lookup = frame.set_index("conversation_id")
        for column in ["text", "num_turns", "toxicity_coverage"]:
            if column not in manifest.columns:
                manifest[column] = manifest["conversation_id"].map(lookup[column])
        return manifest
    return build_default_split_manifest(frame, seed)


def lexicon_score(text: str) -> float:
    tokens = normalize_text(text)
    if not tokens:
        return 0.0
    score = sum(TOXIC_LEXICON.get(tok, 0.0) for tok in tokens)
    return score / len(tokens)


def best_threshold(scores: np.ndarray, labels: np.ndarray) -> float:
    unique_scores = np.unique(scores)
    if len(unique_scores) == 1:
        return float(unique_scores[0])
    candidates = [unique_scores[0] - 1e-6]
    candidates.extend((unique_scores[i] + unique_scores[i + 1]) / 2 for i in range(len(unique_scores) - 1))
    candidates.append(unique_scores[-1] + 1e-6)
    best_score = -1.0
    best_thresh = 0.0
    for thresh in candidates:
        pred = (scores >= thresh).astype(int)
        score = f1_score(labels, pred, average="macro")
        if score > best_score:
            best_score = score
            best_thresh = float(thresh)
    return best_thresh


def evaluate(y_true: np.ndarray, y_pred: np.ndarray, y_score: np.ndarray | None = None) -> dict:
    result = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro")),
        "positive_rate": float(np.mean(y_pred)),
    }
    if y_score is not None and len(np.unique(y_true)) > 1:
        result["auc"] = float(roc_auc_score(y_true, y_score))
    else:
        result["auc"] = float("nan")
    return result


def save_confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray, out_path: Path, title: str) -> None:
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    fig, ax = plt.subplots(figsize=(4.5, 4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False, ax=ax)
    ax.set_xticklabels(["civil", "derailed"])
    ax.set_yticklabels(["civil", "derailed"], rotation=0)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def run_majority(train: pd.DataFrame, test: pd.DataFrame) -> tuple[dict, np.ndarray]:
    clf = DummyClassifier(strategy="most_frequent")
    clf.fit(train[["label"]], train["label"])
    pred = clf.predict(test[["label"]])
    scores = np.full(len(test), float(clf.classes_[np.argmax(clf.class_prior_)]))
    metrics = evaluate(test["label"].to_numpy(), pred, scores)
    metrics["model"] = "majority"
    metrics["threshold"] = float("nan")
    return metrics, pred


def run_lexicon(train: pd.DataFrame, test: pd.DataFrame, threshold_override: float | None = None) -> tuple[dict, np.ndarray, float]:
    train_scores = train["text"].map(lexicon_score).to_numpy()
    test_scores = test["text"].map(lexicon_score).to_numpy()
    threshold = threshold_override if threshold_override is not None else best_threshold(train_scores, train["label"].to_numpy())
    pred = (test_scores >= threshold).astype(int)
    metrics = evaluate(test["label"].to_numpy(), pred, test_scores)
    metrics["model"] = "lexicon"
    metrics["threshold"] = float(threshold)
    return metrics, pred, threshold


def render_report(config: BaselineConfig, manifest: pd.DataFrame, summaries: list[dict], threshold: float) -> str:
    lines = [
        "=" * 72,
        f"CGA TOXICITY BASELINES ({config.dataset.upper()})",
        "=" * 72,
        "",
        "PROTOCOL",
        "-" * 40,
        "Primary unit: conversation/thread",
        "Primary label: conversation_has_personal_attack / has_derailed",
        f"Split manifest: {config.split_manifest or 'generated deterministically'}",
        f"Seed: {config.seed}",
        f"Minimum turns: {config.min_turns}",
        f"Lexicon threshold: {threshold:.6f}",
        "",
        "DATASET SUMMARY",
        "-" * 40,
        f"Conversations: {len(manifest)}",
        f"Derailed: {int(manifest['label'].sum())}",
        f"Civil: {int((1 - manifest['label']).sum())}",
        f"Derailment rate: {manifest['label'].mean():.4f}",
        "",
        "RESULTS",
        "-" * 40,
    ]
    for row in summaries:
        lines.append(
            f"{row['model']}: accuracy={row['accuracy']:.4f}, macro_f1={row['macro_f1']:.4f}, auc={row['auc']:.4f}, positive_rate={row['positive_rate']:.4f}"
        )
    lines.extend(
        [
            "",
            "NOTES",
            "-" * 40,
            "The majority baseline provides the lower bound from a trivial class prior.",
            "The lexicon baseline counts simple toxicity cue words and is tuned only on the train split.",
            "Conversation-level splitting is preserved so no utterance from one conversation leaks across splits.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    loader = CGALoader(dataset=args.dataset)
    frame = build_conversation_frame(loader.load(), min_turns=args.min_turns)
    manifest = load_split_manifest(args.split_manifest, frame, args.seed)
    manifest = manifest.sort_values(["split", "conversation_id"]).reset_index(drop=True)

    train = manifest[manifest["split"] == "train"].copy()
    dev = manifest[manifest["split"] == "dev"].copy()
    test = manifest[manifest["split"] == "test"].copy()
    if train.empty or dev.empty or test.empty:
        raise ValueError("All splits must be non-empty.")

    majority_metrics, majority_pred = run_majority(train, test)
    lexicon_metrics, lexicon_pred, threshold = run_lexicon(train, test, args.threshold)
    summaries = [majority_metrics, lexicon_metrics]

    pd.DataFrame(summaries).sort_values("macro_f1", ascending=False).to_csv(args.output_dir / "results_summary.csv", index=False)
    pd.DataFrame(classification_report(test["label"], majority_pred, output_dict=True, zero_division=0)).transpose().to_csv(
        args.output_dir / "classification_report_majority.csv"
    )
    pd.DataFrame(classification_report(test["label"], lexicon_pred, output_dict=True, zero_division=0)).transpose().to_csv(
        args.output_dir / "classification_report_lexicon.csv"
    )
    save_confusion_matrix(test["label"].to_numpy(), majority_pred, args.output_dir / "confusion_matrix_majority.png", "Majority Baseline")
    save_confusion_matrix(test["label"].to_numpy(), lexicon_pred, args.output_dir / "confusion_matrix_lexicon.png", "Lexicon Baseline")

    test_out = test[["conversation_id", "split", "label", "label_name", "num_turns", "toxicity_coverage"]].copy()
    test_out["majority_pred"] = majority_pred
    test_out["lexicon_pred"] = lexicon_pred
    test_out["lexicon_score"] = test["text"].map(lexicon_score).to_numpy()
    test_out.to_csv(args.output_dir / "test_predictions.tsv", sep="\t", index=False)

    config = BaselineConfig(
        dataset=args.dataset,
        seed=args.seed,
        min_turns=args.min_turns,
        split_manifest=str(args.split_manifest) if args.split_manifest else None,
        threshold=float(threshold),
    )
    with open(args.output_dir / "run_info.json", "w", encoding="utf-8") as handle:
        json.dump(asdict(config), handle, indent=2)

    report = render_report(config, manifest, summaries, threshold)
    with open(args.output_dir / "baseline_report.txt", "w", encoding="utf-8") as handle:
        handle.write(report)

    print(report)
    print(f"Artifacts written to {args.output_dir}")


if __name__ == "__main__":
    main()
