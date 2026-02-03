#!/usr/bin/env python3
"""
Convert Europarl TMV-annotator output to TAMV validation format.

This script correctly maps TMV-annotator's labels to our TAMV format,
using the ACTUAL mood values from TMV-annotator (not overriding them).

TMV-annotator mood values: indicative, subjunctive
TMV-annotator tense values: pres, past, presPerf, pastPerf, futureI, futureII, condI, condII
"""

from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def parse_europarl_line(line):
    """Parse a line from europarl_expected.tsv (TMV-annotator format)."""
    parts = line.strip().split('\t')
    if len(parts) < 10:
        return None

    sent_idx = int(parts[0])
    token_pos = parts[1]
    verb_phrase = parts[2]
    is_finite = parts[3]
    lemma = parts[4]
    tmv_tense = parts[5]   # pres, past, presPerf, condI, futureII, etc.
    tmv_mood = parts[6]    # indicative, subjunctive, or "-"
    tmv_voice = parts[7]   # active, passive, or "-"
    progressive = parts[8]  # yes, no
    negation = parts[9]     # yes, no

    # Skip non-finite verbs (they have "-" for tense/mood/voice)
    if tmv_tense == "-" or is_finite == "no":
        return None

    # Map TMV-annotator tense to our TENSE dimension
    # Note: condI/condII indicate conditional constructions, but the TENSE
    # is still present/past based on the form
    tense_map = {
        'pres': 'PRESENT',
        'past': 'PAST',
        'presPerf': 'PRESENT',      # Present perfect: tense is present
        'pastPerf': 'PAST',         # Past perfect: tense is past
        'futureI': 'FUTURE',
        'futureII': 'FUTURE',       # Future perfect
        'condI': 'PRESENT',         # Conditional I: "would work" - present form
        'condII': 'PAST',           # Conditional II: "would have worked" - past reference
    }

    # Determine ASPECT based on tense value and progressive flag
    def get_aspect(tmv_tense, progressive):
        is_perfect = 'Perf' in tmv_tense or tmv_tense in ('futureII', 'condII')
        is_prog = progressive == 'yes'

        if is_perfect and is_prog:
            return 'PERFECT_PROGRESSIVE'
        elif is_perfect:
            return 'PERFECT'
        elif is_prog:
            return 'PROGRESSIVE'
        else:
            return 'SIMPLE'

    # Map MOOD - USE ACTUAL TMV-ANNOTATOR VALUE, don't override!
    # TMV-annotator uses: indicative, subjunctive
    # For condI/condII tenses, TMV-annotator marks mood as "subjunctive"
    mood_map = {
        'indicative': 'INDICATIVE',
        'subjunctive': 'SUBJUNCTIVE',
    }

    # Map VOICE directly
    voice_map = {
        'active': 'ACTIVE',
        'passive': 'PASSIVE',
    }

    our_tense = tense_map.get(tmv_tense, 'PRESENT')
    our_aspect = get_aspect(tmv_tense, progressive)
    our_mood = mood_map.get(tmv_mood, 'INDICATIVE')  # Use actual TMV mood!
    our_voice = voice_map.get(tmv_voice, 'ACTIVE')

    # Determine category for reporting
    if our_mood == 'SUBJUNCTIVE':
        category = 'mood_subjunctive'
    elif our_voice == 'PASSIVE':
        category = 'voice_passive'
    elif our_aspect != 'SIMPLE':
        category = f'aspect_{our_aspect.lower()}'
    else:
        category = f'tense_{our_tense.lower()}'

    return {
        'sent_idx': sent_idx,
        'verb': lemma,
        'tense': our_tense,
        'aspect': our_aspect,
        'mood': our_mood,
        'voice': our_voice,
        'category': category,
        'source': 'Ramm et al. (Europarl)'
    }


def convert_europarl():
    """Convert Europarl TMV-annotator data to TAMV validation format."""
    expected_file = DATA_DIR / "europarl_expected.tsv"
    output_file = DATA_DIR / "europarl_tamv.tsv"

    annotations = []
    with open(expected_file, 'r') as f:
        for line in f:
            parsed = parse_europarl_line(line)
            if parsed:
                annotations.append(parsed)

    # Write converted data
    with open(output_file, 'w') as f:
        f.write("index\tverb\ttense\taspect\tmood\tvoice\tcategory\tsource\n")
        for ann in annotations:
            f.write(f"{ann['sent_idx']}\t{ann['verb']}\t{ann['tense']}\t{ann['aspect']}\t{ann['mood']}\t{ann['voice']}\t{ann['category']}\t{ann['source']}\n")

    print(f"Converted {len(annotations)} verb annotations")
    print(f"Output: {output_file}")

    # Show sample
    print("\nSample conversions:")
    for ann in annotations[:5]:
        print(f"  {ann['verb']}: {ann['tense']}-{ann['aspect']}-{ann['mood']}-{ann['voice']}")

    # Show mood distribution
    mood_counts = {}
    for ann in annotations:
        mood_counts[ann['mood']] = mood_counts.get(ann['mood'], 0) + 1
    print(f"\nMood distribution: {mood_counts}")


if __name__ == "__main__":
    convert_europarl()
