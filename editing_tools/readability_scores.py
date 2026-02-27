#!/usr/bin/env python3
"""Flesch-Kincaid readability scores for assembled paper sections.

Usage:
    python editing_tools/readability_scores.py

Run from repo root. Requires: pip install textstat
"""

import glob
import os
import sys

try:
    import textstat
except ImportError:
    print("ERROR: textstat not installed. Run: pip install textstat")
    sys.exit(1)

files = sorted(glob.glob("paper/sections/0[1-8]*.md"))
if not files:
    print("ERROR: No section files found. Run from repo root.")
    sys.exit(1)

print(f"{'Section':<45} {'FK Grade':>8} {'Words':>6}")
print("-" * 62)
for f in files:
    text = open(f).read()
    grade = textstat.flesch_kincaid_grade(text)
    words = textstat.lexicon_count(text)
    flag = "  ← check" if grade > 16 else ""
    print(f"{os.path.basename(f):<45} {grade:>8.1f} {words:>6}{flag}")

print()
print("Target: FK Grade 12–16 (college level). See editing_tools/editing_tools_srs.md.")
