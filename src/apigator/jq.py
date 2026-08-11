"""Modular logic to call and run jq on a given set of data."""

import json
import subprocess
from typing import Any


def run_jq_filter(data: Any, jq_filter: str) -> str:
    """Run jq filters on specified data."""
    result = subprocess.run(
        ("jq", jq_filter), input=json.dumps(data), capture_output=True, text=True
    )
    if result.returncode == 0:
        value = json.loads(result.stdout)
    else:
        raise ValueError(f"jq filter failed for '{jq_filter}': {result.stderr}")
    return value
