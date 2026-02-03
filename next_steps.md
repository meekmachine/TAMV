# Next Steps for main.tex

## Sections Still Needing Expansion

### 1. Temporal structure and tense/aspect (§2.3) - Line 95-98
Currently only 1 bullet. Could expand with:
- Reichenbach's tense model (speech time, event time, reference time)
- How aspect interacts with temporal interpretation
- Ambiguous cases (e.g., present perfect vs simple past)

### 2. Linguistic evidence for TAMV and register (§3.1) - Line 101-104
Currently only 1 bullet. Overlaps with Background - could differentiate or merge.

### 3. Benchmarks for downstream prediction (§3.3) - Line 114-118
Has "(To add)" placeholder for toxicity and VAD benchmarks.

### 4. Data section (§4) - Line 119+
Has "(To add)" placeholders for:
- Toxicity prediction dataset
- VAD prediction dataset/lexicon

### 5. Intrinsic evaluation (§6.1) - Line ~145
Only 1 bullet. Could add:
- Evaluation methodology details
- Test case construction approach
- Error taxonomy

### 6. Toxicity/VAD prediction sections (§6.3-6.4)
Need dataset citations once BibTeX entries available.

### 7. Results section (§7)
All placeholders - needs actual results.

---

## References to Add to BibTeX

### Tesnière - Dependency Grammar (Original French)
```bibtex
@book{Tesniere1959Elements,
    author = {Tesni\`{e}re, Lucien},
    title = {\'{E}l\'{e}ments de syntaxe structurale},
    year = {1959},
    publisher = {Klincksieck},
    address = {Paris},
    note = {2nd edition 1969}
}
```

### Tesnière - Dependency Grammar (English Translation)
```bibtex
@book{Tesniere2015Elements,
    author = {Tesni\`{e}re, Lucien},
    translator = {Osborne, Timothy and Kahane, Sylvain},
    title = {Elements of Structural Syntax},
    year = {2015},
    publisher = {John Benjamins},
    address = {Amsterdam},
    doi = {10.1075/z.185}
}
```

### Chomsky - Government & Binding
```bibtex
@book{Chomsky1981Lectures,
    author = {Chomsky, Noam},
    title = {Lectures on Government and Binding},
    year = {1981},
    publisher = {Foris Publications},
    address = {Dordrecht}
}
```

### Chomsky - Syntactic Structures (Original Phrase Structure)
```bibtex
@book{Chomsky1957Syntactic,
    author = {Chomsky, Noam},
    title = {Syntactic Structures},
    year = {1957},
    publisher = {Mouton},
    address = {The Hague}
}
```

### Universal Dependencies v2 (Foundational UD Paper)
```bibtex
@inproceedings{Nivre2020UniversalDependencies,
    author = {Nivre, Joakim and de Marneffe, Marie-Catherine and Ginter, Filip and Haji\v{c}, Jan and Manning, Christopher D. and Pyysalo, Sampo and Schuster, Sebastian and Tyers, Francis and Zeman, Daniel},
    title = {Universal Dependencies v2: An Evergrowing Multilingual Treebank Collection},
    booktitle = {Proceedings of the 12th Language Resources and Evaluation Conference (LREC 2020)},
    year = {2020},
    pages = {4034--4043},
    address = {Marseille, France},
    publisher = {European Language Resources Association},
    url = {https://aclanthology.org/2020.lrec-1.497/}
}
```

### Stanford Dependencies (Original Paper)
```bibtex
@inproceedings{deMarneffe2006Generating,
    author = {de Marneffe, Marie-Catherine and MacCartney, Bill and Manning, Christopher D.},
    title = {Generating Typed Dependency Parses from Phrase Structure Parses},
    booktitle = {Proceedings of LREC 2006},
    year = {2006},
    pages = {449--454},
    address = {Genoa, Italy}
}
```

### Universal Stanford Dependencies
```bibtex
@inproceedings{deMarneffe2014Universal,
    author = {de Marneffe, Marie-Catherine and Dozat, Timothy and Silveira, Natalia and Haverinen, Katri and Ginter, Filip and Nivre, Joakim and Manning, Christopher D.},
    title = {Universal Stanford Dependencies: A Cross-Linguistic Typology},
    booktitle = {Proceedings of LREC 2014},
    year = {2014},
    pages = {4585--4592},
    address = {Reykjavik, Iceland},
    url = {https://nlp.stanford.edu/pubs/USD_LREC14_paper_camera_ready.pdf}
}
```

---

## Summary of Today's Edits

### Completed
1. Fixed Europarl/TMV-annotator validation (88.9% accuracy)
2. Created `code/scripts/convert_europarl.py` with correct mood mapping
3. Created `code/data/europarl_tamv.tsv`
4. Expanded §2.1 Register section with examples
5. Expanded §2.2 UD vs SD with theoretical foundations (Tesnière vs Chomsky)
6. Expanded §3.2 Related Work with Ramm et al., spaCy, Mate comparison
7. Expanded §5.2 TAMV extraction with detection rules

### Pending
- Add Longman Grammar Chapter 6 examples to synthetic test data
- Fill in toxicity/VAD dataset placeholders
- Add actual results to Results section
