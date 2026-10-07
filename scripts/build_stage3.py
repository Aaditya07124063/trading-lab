"""Deterministic Stage 3 input build for S2-MOM-v1 (Phase 3B). Inputs only - no portfolio returns.

Reads RET-1.1, UNIV-1 and ID-1 (hash-checked), writes data/stage3/s2_mom_v1/. If the outputs
already exist they are rebuilt and must be byte-identical. Prints structural counts only.

    python3 scripts/build_stage3.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.stage3.data import build                                           # noqa: E402

if __name__ == "__main__":
    content, _ = build()
    print(json.dumps({k: content[k] for k in ("samples", "structural_counts", "outputs_sha256")}, indent=1))
    print("RESULT: Stage 3 inputs built / verified identical")
