#!/usr/bin/env python3
"""
build.py — Assemble draft_v1.qmd from source files and render to PDF.

Source of truth:
  - frontmatter.yml     (YAML config)
  - abstract.md         (abstract text)
  - sections/01–10.md   (section content, in order)

Output:
  - draft_v1.qmd  (build artifact — do NOT edit directly)
  - draft_v1.pdf  (rendered PDF)

Usage:
  python build.py              # assemble draft_v1.qmd only
  python build.py --render     # assemble + quarto render
  python build.py --open       # assemble + render + open PDF
"""

import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

# --- Configuration ---

PROJECT_DIR = Path(__file__).parent
OUTPUT_FILE = PROJECT_DIR / "draft_v1.qmd"

FRONTMATTER = PROJECT_DIR / "frontmatter.yml"
ABSTRACT = PROJECT_DIR / "abstract.md"

# Sections in assembly order — sidecars excluded
SECTIONS = [
    PROJECT_DIR / "sections" / "01_introduction.md",
    PROJECT_DIR / "sections" / "02_semantic_smearing.md",
    PROJECT_DIR / "sections" / "03_pragmatics.md",
    PROJECT_DIR / "sections" / "04_method.md",
    PROJECT_DIR / "sections" / "05_results.md",
    PROJECT_DIR / "sections" / "06_discussion.md",
    PROJECT_DIR / "sections" / "07_limitations_future.md",
    PROJECT_DIR / "sections" / "08_conclusion.md",
    PROJECT_DIR / "sections" / "09_references.md",
    PROJECT_DIR / "sections" / "10_appendices.md",
]

# Sidecars: not included in assembly, kept as working files
# - sections/05_extraction_pipeline.md
# - sections/08_discussion_sidecar.md


def validate_sources():
    """Check all source files exist before assembly."""
    missing = []
    for f in [FRONTMATTER, ABSTRACT] + SECTIONS:
        if not f.exists():
            missing.append(str(f.relative_to(PROJECT_DIR)))
    if missing:
        print(f"ERROR: Missing source files: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)


def assemble():
    """Assemble draft_v1.qmd from source files."""
    validate_sources()

    parts = []

    # --- YAML front matter ---
    parts.append("---")
    parts.append(FRONTMATTER.read_text().rstrip())

    # Inject abstract (indented 2 spaces for YAML block scalar)
    abstract_text = ABSTRACT.read_text().rstrip()
    abstract_indented = "\n".join(
        f"  {line}" if line.strip() else "" for line in abstract_text.splitlines()
    )
    parts.append(f"abstract: |\n{abstract_indented}")

    parts.append("---")

    # --- Section content ---
    for section in SECTIONS:
        parts.append("")  # blank line separator
        parts.append(section.read_text().rstrip())

    # --- Write output ---
    assembled = "\n".join(parts) + "\n"
    OUTPUT_FILE.write_text(assembled)

    line_count = assembled.count("\n")
    print(f"Assembled {OUTPUT_FILE.name} ({line_count} lines) from {len(SECTIONS)} sections")


def render():
    """Run quarto render."""
    print("Rendering PDF...")
    result = subprocess.run(
        ["quarto", "render", str(OUTPUT_FILE)],
        cwd=PROJECT_DIR,
    )
    if result.returncode != 0:
        print("ERROR: quarto render failed", file=sys.stderr)
        sys.exit(1)
    print(f"Done: {OUTPUT_FILE.stem}.pdf")


def clean_numbered_copies():
    """Remove numbered copies (e.g., draft_v1 2.pdf) left by xelatex multi-pass."""
    import glob
    patterns = [
        str(PROJECT_DIR / "draft_v1 *.pdf"),
        str(PROJECT_DIR / "draft_v1 *.log"),
        str(PROJECT_DIR / "draft_v1 *.aux"),
        str(PROJECT_DIR / "draft_v1 *.tex"),
    ]
    removed = 0
    for pattern in patterns:
        for f in glob.glob(pattern):
            Path(f).unlink()
            removed += 1
    if removed:
        print(f"Cleaned {removed} numbered build artifacts")


def crop_figures():
    """Crop whitespace from all figure PDFs using pdfCropMargins."""
    figures_dir = PROJECT_DIR / "assets" / "figures"
    pdfs = sorted(figures_dir.glob("*.pdf"))
    if not pdfs:
        print("No figure PDFs found to crop.")
        return

    cropped = 0
    for pdf in pdfs:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = tmp.name
        result = subprocess.run(
            ["pdf-crop-margins", "-p", "0", "-a", "-2", str(pdf), "-o", tmp_path],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            shutil.move(tmp_path, str(pdf))
            cropped += 1
        else:
            print(f"  WARNING: crop failed on {pdf.name}: {result.stderr.strip()}")

    print(f"Cropped {cropped}/{len(pdfs)} figure PDFs")


def open_pdf():
    """Open the rendered PDF."""
    pdf_path = PROJECT_DIR / f"{OUTPUT_FILE.stem}.pdf"
    if pdf_path.exists():
        subprocess.run(["open", str(pdf_path)])
    else:
        print(f"ERROR: {pdf_path} not found", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    assemble()

    if "--render" in sys.argv or "--open" in sys.argv:
        render()
        crop_figures()  # Always crop after render
        clean_numbered_copies()  # Remove xelatex multi-pass debris

    if "--open" in sys.argv:
        open_pdf()
