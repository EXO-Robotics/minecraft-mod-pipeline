import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def test_deterministic_and_closed():
    script = HERE / "build_skyreach_authority_map.py"
    subprocess.run([sys.executable, str(script)], check=True)
    first = hashlib.sha256((HERE / "SKYREACH_VERTICAL_INTAKE_MAP.json").read_bytes()).hexdigest()
    subprocess.run([sys.executable, str(script)], check=True)
    assert first == hashlib.sha256((HERE / "SKYREACH_VERTICAL_INTAKE_MAP.json").read_bytes()).hexdigest()
    data = json.loads((HERE / "SKYREACH_VERTICAL_INTAKE_MAP.json").read_text())
    assert len(data["assets"]) == len({row["id"] for row in data["assets"]}) == 50
    assert data["packet"]["category_counts"] == {"blocks": 10, "creatures": 10, "plants": 10, "resources": 10, "structures": 10}
    assert all(len(row["source_files"]) == 6 for row in data["assets"])
    assert set(data["minimum_authority_tranches"]) == {"W1-001-SR", "W1-003-STORM-NEST", "W1-004-SR"}
    assert all(row["status"] == "PROPOSED_NOT_RATIFIED" for row in data["minimum_authority_tranches"].values())
    current = data["current_ratification_reconciliation"]
    assert set(current["approved"]) == {"W1-001-SR", "W1-003-STORM-NEST", "W1-004-SR"}
    assert all(row["status"] == "APPROVED_AS_PROPOSED" for row in current["approved"].values())
    assert current["W1-CREATIVE-005"] == "DEFERRED_BY_USER"
    assert any(row["id"] == "W1-CREATIVE-005" and row["disposition"] == "DEFERRED_BY_USER" for row in data["blocker_matrix"])
    assert data["guards"]["new_numbers_or_identities_invented"] is False


if __name__ == "__main__":
    test_deterministic_and_closed()
    print("PASS: Skyreach authority intake deterministic and closed")
