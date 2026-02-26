#!/bin/bash
# Build all D2 diagrams to PDF
# Usage: bash paper/assets/diagrams/build_diagrams.sh

set -e

DIAG_DIR="paper/assets/diagrams"
FIG_DIR="paper/assets/figures"
THEME=200  # Neutral default
LAYOUT=elk  # ELK bundled with D2 0.7+

mkdir -p "$FIG_DIR"

for d2file in "$DIAG_DIR"/F*.d2; do
    base=$(basename "$d2file" .d2)
    echo "Building $base..."
    d2 --theme "$THEME" --layout "$LAYOUT" "$d2file" "$FIG_DIR/${base}.pdf"
done

echo "Done. Figures in $FIG_DIR/"
