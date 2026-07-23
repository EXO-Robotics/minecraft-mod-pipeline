from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from mccompiler.reconstruction.forest_wave_1 import render_forest_wave_1_diagnosis  # noqa: E402


def main() -> int:
    reports, paths = render_forest_wave_1_diagnosis(ROOT)
    readiness = reports["forest-wave-1-execution-readiness.json"]
    print(json.dumps({
        "mode": "DIAGNOSTIC_ONLY",
        "execution_status": "EXECUTION_NOT_AUTHORIZED",
        "aggregate_readiness": readiness["aggregate"]["status"],
        "blocking": readiness["aggregate"]["autonomous_production_may_proceed"] is False,
        "artifacts": [str(path.relative_to(ROOT)) for path in paths],
    }, sort_keys=True))
    return 3 if readiness["aggregate"]["autonomous_production_may_proceed"] is False else 0


if __name__ == "__main__":
    raise SystemExit(main())
