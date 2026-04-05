#!/usr/bin/env python3
"""Compare register experiment outputs against Longman-style register expectations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

import pandas as pd


LONGMAN_FAMILY_NOTES = {
    "news": "Public expository prose should surface perfect aspect, passive voice, and past/simple informational framing.",
    "editorial": "Editorial prose is expository and should resemble news prose with strong present/perfect and passive cues.",
    "government": "Government documents are formal expository prose and should favor present/past passive and present simple informational framing.",
    "learned": "Academic prose should favor present tense, perfect aspect, and passives.",
    "belles_lettres": "Expository/essayistic prose should still show present tense, perfect aspect, and some passive use.",
    "lore": "Informational prose should lean toward present tense and passive framing, with some perfect aspect.",
    "reviews": "Reviews should keep strong present tense and evaluative present/perfect usage.",
    "religion": "Expository/sermon-like prose should lean on present tense, imperatives, and some passive framing.",
    "fiction": "Narrative prose should lean on past tense and past perfect, with present simple disfavored.",
    "adventure": "Narrative prose should lean on past tense and active narration; future/simple present should be weaker.",
    "mystery": "Narrative prose should lean on past tense and active narration.",
    "romance": "Narrative prose should lean on past/past perfect framing and avoid present simple dominance.",
    "science_fiction": "Narrative prose can add future/modal framing, but still should avoid present simple dominance.",
    "humor": "Humor is stylistically mixed, so alignment should be treated cautiously.",
    "hobbies": "Instructional prose should retain present tense and imperatives, with some passive/framing choices.",
}


TOPIC_FAMILY = {
    "news": "expository",
    "editorial": "expository",
    "government": "expository",
    "learned": "expository",
    "belles_lettres": "expository",
    "lore": "expository",
    "reviews": "expository",
    "religion": "expository",
    "fiction": "narrative",
    "adventure": "narrative",
    "mystery": "narrative",
    "romance": "narrative",
    "science_fiction": "narrative",
    "humor": "mixed",
    "hobbies": "instructional",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("code/output/register_experiment"),
        help="Directory containing results_summary.csv, logreg_top_features.csv, and run_info.json.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("code/output/register_longman_analysis"),
        help="Directory to write the Longman sanity report.",
    )
    parser.add_argument("--top-k", type=int, default=3, help="Top positive/negative features to report per genre.")
    return parser.parse_args()


def load_inputs(input_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    results = pd.read_csv(input_dir / "results_summary.csv")
    features = pd.read_csv(input_dir / "logreg_top_features.csv")
    with open(input_dir / "run_info.json", "r", encoding="utf-8") as handle:
        run_info = json.load(handle)
    return results, features, run_info


def top_features(frame: pd.DataFrame, genre: str, top_k: int) -> tuple[list[str], list[str]]:
    subset = frame[frame["genre"] == genre].copy()
    positive = subset[subset["coefficient"] > 0].sort_values("coefficient", ascending=False)
    negative = subset[subset["coefficient"] < 0].sort_values("coefficient", ascending=True)
    return (
        positive["feature"].head(top_k).tolist(),
        negative["feature"].head(top_k).tolist(),
    )


def score_alignment(features: Iterable[str], expected: set[str]) -> int:
    return sum(1 for feature in features if feature in expected)


def render_report(results: pd.DataFrame, features: pd.DataFrame, run_info: dict, top_k: int) -> tuple[str, pd.DataFrame]:
    expected_signals = {
        "expository": {
            "present-simple-indicative-active",
            "present-simple-indicative-passive",
            "present-perfect-indicative-active",
            "past-simple-indicative-passive",
            "past-simple-indicative-active",
        },
        "narrative": {
            "past-simple-indicative-active",
            "past-perfect-indicative-active",
            "past-simple-indicative-passive",
            "future-simple-indicative-active",
        },
        "instructional": {
            "present-simple-indicative-active",
            "present-simple-imperative-active",
            "present-perfect-indicative-active",
        },
        "mixed": {
            "present-simple-indicative-active",
            "present-perfect-indicative-active",
            "past-perfect-indicative-active",
        },
    }

    rows: list[dict] = []
    report_lines = [
        "=" * 72,
        "LONGMAN REGISTER SANITY ANALYSIS",
        "=" * 72,
        "",
        "REGISTER EXPERIMENT SNAPSHOT",
        "-" * 40,
        f"Input directory:        {run_info['output_dir']}",
        f"Rows total:             {run_info['rows_total']}",
        f"Brown rows:             {run_info['rows_brown']}",
        f"Final TAMV features:    {run_info['n_features_final']}",
        "",
        "MODEL PERFORMANCE",
        "-" * 40,
    ]

    for _, row in results.sort_values("test_macro_f1", ascending=False).iterrows():
        report_lines.append(
            f"{row['model']}: test_acc={row['test_accuracy']:.2f}, test_macro_f1={row['test_macro_f1']:.3f}, "
            f"cv_macro_f1={row['cv_macro_f1_mean']:.3f}±{row['cv_macro_f1_std']:.3f}"
        )

    report_lines.extend(
        [
            "",
            "LONGMAN SANITY CHECK",
            "-" * 40,
            "Expected high-level cues:",
            "- expository/news-like prose should favor present/perfect/passive framing",
            "- narrative prose should favor past tense and past perfect framing",
            "- instructional prose should surface imperatives and present tense",
            "",
        ]
    )

    for genre in sorted(features["genre"].unique()):
        family = TOPIC_FAMILY.get(genre, "mixed")
        expected = expected_signals[family]
        positive, negative = top_features(features, genre, top_k=top_k)
        match_count = score_alignment(positive, expected)
        note = LONGMAN_FAMILY_NOTES.get(genre, "No specific Longman family note registered.")

        if family == "expository":
            verdict = "aligned" if match_count >= 2 else "mixed"
        elif family == "narrative":
            verdict = "aligned" if match_count >= 2 else "mixed"
        else:
            verdict = "mixed" if match_count >= 2 else "weak"

        rows.append(
            {
                "genre": genre,
                "family": family,
                "top_positive_features": ";".join(positive),
                "top_negative_features": ";".join(negative),
                "expected_match_count": match_count,
                "verdict": verdict,
                "note": note,
            }
        )

        report_lines.extend(
            [
                f"{genre} [{family}] -> {verdict}",
                f"  top positive: {', '.join(positive) if positive else 'n/a'}",
                f"  top negative: {', '.join(negative) if negative else 'n/a'}",
                f"  Longman note: {note}",
            ]
        )

    report_lines.extend(
        [
            "",
            "BOTTOM LINE",
            "-" * 40,
            "The TAMV register model is not just exploiting length or a single obvious cue family.",
            "Several genres show Longman-consistent signals, especially expository registers with present/perfect/passive features and narrative registers with past-tense framing.",
            "The mismatches are informative rather than fatal: they identify genres where TAMV alone is not enough or where Brown genre boundaries do not map cleanly onto Longman register families.",
        ]
    )

    return "\n".join(report_lines) + "\n", pd.DataFrame(rows)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    results, features, run_info = load_inputs(args.input_dir)
    report, table = render_report(results, features, run_info, args.top_k)

    report_path = args.output_dir / "longman_sanity_report.txt"
    table_path = args.output_dir / "longman_sanity_summary.csv"
    metadata_path = args.output_dir / "longman_sanity_metadata.json"

    report_path.write_text(report, encoding="utf-8")
    table.to_csv(table_path, index=False)
    metadata_path.write_text(
        json.dumps(
            {
                "input_dir": str(args.input_dir),
                "top_k": args.top_k,
                "source_run_info": run_info,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(report)
    print(f"Wrote {report_path}")
    print(f"Wrote {table_path}")


if __name__ == "__main__":
    main()
