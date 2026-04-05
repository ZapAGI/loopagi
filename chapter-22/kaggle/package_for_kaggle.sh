#!/bin/bash
# Package loopagi/ for Kaggle dataset upload
# Creates a zip file containing just the loopagi/ package
# that the notebook can add to sys.path

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUTPUT_DIR="$SCRIPT_DIR/dataset"

echo "Packaging loopagi/ from $REPO_ROOT"
echo "Output: $OUTPUT_DIR"

# Clean previous
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# Copy loopagi package (only arc/ subpackage needed)
mkdir -p "$OUTPUT_DIR/loopagi/arc"
mkdir -p "$OUTPUT_DIR/loopagi/core"

# Copy __init__.py files
cp "$REPO_ROOT/loopagi/__init__.py" "$OUTPUT_DIR/loopagi/" 2>/dev/null || touch "$OUTPUT_DIR/loopagi/__init__.py"

# Copy arc modules (the solver pipeline)
cp "$REPO_ROOT/loopagi/arc/"*.py "$OUTPUT_DIR/loopagi/arc/"

# Create minimal core __init__.py (avoid langchain imports)
cat > "$OUTPUT_DIR/loopagi/core/__init__.py" << 'EOF'
"""Minimal core package for Kaggle (no langchain dependency)."""
EOF

# Create minimal ollama_utils.py (needed by llm_bridge lazy import)
cat > "$OUTPUT_DIR/loopagi/core/ollama_utils.py" << 'EOF'
"""Minimal ollama_utils for Kaggle (Ollama not available)."""

def is_ollama_running(model: str = "") -> bool:
    """Always returns False on Kaggle — no Ollama available."""
    return False
EOF

# Count files
N_FILES=$(find "$OUTPUT_DIR" -name "*.py" | wc -l)
TOTAL_SIZE=$(du -sh "$OUTPUT_DIR" | cut -f1)

echo "Packaged $N_FILES Python files ($TOTAL_SIZE)"
echo ""
echo "Next steps:"
echo "  1. Create a Kaggle dataset from $OUTPUT_DIR/"
echo "     kaggle datasets create -p $OUTPUT_DIR/"
echo "  2. Or zip and upload manually:"
echo "     cd $OUTPUT_DIR && zip -r ../loopagi-arc-solver.zip ."
echo ""
echo "Done!"
