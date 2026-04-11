#!/usr/bin/env python3
"""Package intrinsic TAMV validation artifacts for paper use.

This script copies the existing intrinsic validation outputs into a dedicated
paper-ready directory and writes a compact summary table extracted from the
checked-in validation reports.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
from pathlib import Path


SINGLE_PATTERNS = {
    "overall_accuracy": r"Overall accuracy:\s+([0-9.]+%)",
    "verb_detection": r"Verb detection rate:\s+([0-9.]+%)",
    "tense_accuracy": r"Tense:\s+([0-9.]+%)",
    "aspect_accuracy": r"Aspect:\s+([0-9.]+%)",
    "mood_accuracy": r"Mood:\s+([0-9.]+%)",
    "voice_accuracy": r"Voice:\s+([0-9.]+%)",
}

TMV_PATTERNS = {
    "sentence_count": r"Sentence count:\s+([0-9]+)",
    "tmv_rows": r"Total TMV-annotator rows:\s+([0-9]+)",
    "comparable_rows": r"Comparable finite rows after TMV->TAMV conversion:\s+([0-9]+)",
    "matched_verbs": r"Matched verbs:\s+([0-9]+)",
    "detection_rate": r"Detection rate:\s+([0-9.]+%)",
    "full_alignment": r"  Full:\s+([0-9.]+%)",
}

PHRASE_PATTERNS = {
    "labels_correct": r"Labels fully correct:\s+([0-9]+ \([0-9.]+%\))",
    "phrases_detected": r"Phrases detected:\s+([0-9]+ \([0-9.]+%\))",
    "tense_accuracy": r"Tense:\s+([0-9.]+%)",
    "aspect_accuracy": r"Aspect:\s+([0-9.]+%)",
    "mood_accuracy": r"Mood:\s+([0-9.]+%)",
    "voice_accuracy": r"Voice:\s+([0-9.]+%)",
}


def parse_args() -> argparse.Namespace:
    code_dir = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Package intrinsic validation artifacts.")
    parser.add_argument("--input-dir", type=Path, default=code_dir / "output")
    parser.add_argument("--output-dir", type=Path, default=code_dir / "output" / "intrinsic_paper")
    return parser.parse_args()


def extract_metrics(text: str, patterns: dict[str, str], prefix: str) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for metric, pattern in patterns.items():
        match = re.search(pattern, text, flags=re.MULTILINE)
        if match:
            rows.append((f"{prefix}_{metric}", match.group(1)))
    return rows


def copy_artifacts(input_dir: Path, output_dir: Path) -> list[Path]:
    files = [
        "validation_report.txt",
        "confusion_tense.png",
        "confusion_aspect.png",
        "confusion_mood.png",
        "confusion_voice.png",
        "confusion_matrices_combined.png",
        "phrase_validation_report.txt",
        "phrase_confusion_tense.png",
        "phrase_confusion_aspect.png",
        "phrase_confusion_mood.png",
        "phrase_confusion_voice.png",
        "phrase_confusion_matrices_combined.png",
    ]
    optional_files = [
        "tmv_alignment_report.txt",
        "tmv_alignment_mismatches.tsv",
    ]

    copied: list[Path] = []
    for name in files:
        src = input_dir / name
        if not src.exists():
            raise FileNotFoundError(f"Missing required artifact: {src}")
        dst = output_dir / name
        shutil.copy2(src, dst)
        copied.append(dst)

    for name in optional_files:
        src = input_dir / name
        if src.exists():
            dst = output_dir / name
            shutil.copy2(src, dst)
            copied.append(dst)

    return copied


def write_summary(output_dir: Path, single_report: Path, phrase_report: Path, tmv_report: Path | None) -> Path:
    single_text = single_report.read_text(encoding="utf-8")
    phrase_text = phrase_report.read_text(encoding="utf-8")
    rows = [
        ("task", "metric", "value"),
        ("single", "source_report", single_report.name),
        ("phrase", "source_report", phrase_report.name),
    ]
    if tmv_report is not None:
        rows.append(("tmv_alignment", "source_report", tmv_report.name))
    rows.extend(("single", metric, value) for metric, value in extract_metrics(single_text, SINGLE_PATTERNS, "single"))
    rows.extend(("phrase", metric, value) for metric, value in extract_metrics(phrase_text, PHRASE_PATTERNS, "phrase"))
    if tmv_report is not None:
        tmv_text = tmv_report.read_text(encoding="utf-8")
        rows.extend(("tmv_alignment", metric, value) for metric, value in extract_metrics(tmv_text, TMV_PATTERNS, "tmv"))

    summary_path = output_dir / "intrinsic_summary.tsv"
    with summary_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerows(rows)
    return summary_path


def write_markdown(output_dir: Path, summary_path: Path) -> Path:
    md_path = output_dir / "intrinsic_summary.md"
    lines = [
        "# Intrinsic Validation Summary",
        "",
        "Packaged from the checked-in intrinsic validation reports.",
        "",
        f"- Summary table: `{summary_path.name}`",
        "- Single-verb figures and report: `validation_report.txt` and `confusion_*.png`",
        "- Phrase-level figures and report: `phrase_validation_report.txt` and `phrase_confusion_*.png`",
        "- TMV compatibility sample: `tmv_alignment_report.txt` and `tmv_alignment_mismatches.tsv` when present",
        "",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return md_path


def write_category_table(output_dir: Path, single_report: Path) -> Path:
    text = single_report.read_text(encoding="utf-8")
    rows = []
    in_section = False
    for line in text.splitlines():
        if line.startswith("ACCURACY BY CATEGORY"):
            in_section = True
            continue
        if in_section and line.startswith("TENSE CONFUSION MATRIX"):
            break
        if in_section:
            match = re.match(r"\s*([A-Za-z0-9_:-]+)\s+(\d+/\s*\d+\s+\([0-9.]+%\))", line)
            if match:
                rows.append((match.group(1), match.group(2)))

    path = output_dir / "single_category_accuracy.tsv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["category", "accuracy"])
        writer.writerows(rows)
    return path


def write_failure_table(output_dir: Path, single_report: Path, phrase_report: Path) -> Path:
    def extract_failures(text: str, report: str) -> list[tuple[str, str, str, str, str]]:
        rows: list[tuple[str, str, str, str, str]] = []
        sentence = ""
        verb = ""
        category = ""
        expected = ""
        got = ""
        in_section = False
        for line in text.splitlines():
            if line.startswith("FAILED TEST CASES"):
                in_section = True
                continue
            if not in_section:
                continue
            if line.startswith("  Sentence: "):
                sentence = line.split("Sentence: ", 1)[1].strip().strip('"')
                verb = ""
                category = ""
                expected = ""
                got = ""
            elif line.startswith("  ID ") and ":" in line:
                sentence = line.split(":", 1)[1].strip().strip('"')
                verb = ""
                category = ""
                expected = ""
                got = ""
            elif line.strip().startswith("- '") and "':" in line:
                verb = line.strip().split("':", 1)[0].lstrip("- *").strip("'")
            elif line.startswith("  Verb: "):
                verb = line.split("Verb: ", 1)[1].strip()
            elif line.startswith("  Category: "):
                category = line.split("Category: ", 1)[1].strip()
            elif line.startswith("  Expected: "):
                expected = line.split("Expected: ", 1)[1].strip()
            elif line.startswith("  Got: "):
                got = line.split("Got: ", 1)[1].strip()
            elif line.strip().startswith("- ") or line.strip().startswith("* "):
                rows.append((report, sentence, verb, category, f"{line.strip()} | expected={expected} | got={got}"))
        return rows

    rows = extract_failures(single_report.read_text(encoding="utf-8"), "single")
    rows.extend(extract_failures(phrase_report.read_text(encoding="utf-8"), "phrase"))

    path = output_dir / "failure_cases.tsv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["report", "sentence", "verb", "category", "note"])
        writer.writerows(rows)
    return path


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    copied = copy_artifacts(args.input_dir, args.output_dir)
    summary_path = write_summary(
        args.output_dir,
        args.input_dir / "validation_report.txt",
        args.input_dir / "phrase_validation_report.txt",
        args.input_dir / "tmv_alignment_report.txt" if (args.input_dir / "tmv_alignment_report.txt").exists() else None,
    )
    category_path = write_category_table(args.output_dir, args.input_dir / "validation_report.txt")
    failure_path = write_failure_table(
        args.output_dir,
        args.input_dir / "validation_report.txt",
        args.input_dir / "phrase_validation_report.txt",
    )
    md_path = write_markdown(args.output_dir, summary_path)
    manifest = {
        "copied_artifacts": [str(path.name) for path in copied],
        "summary_table": summary_path.name,
        "category_table": category_path.name,
        "failure_table": failure_path.name,
    }
    (args.output_dir / "bundle_manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    print(f"Packaged {len(copied)} artifacts into {args.output_dir}")
    print(f"Summary table: {summary_path}")
    print(f"Markdown note: {md_path}")


if __name__ == "__main__":
    main()
