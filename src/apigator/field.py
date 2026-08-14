"""Logic and container to handle field definitions for upstream APIs."""

import json
import subprocess
from dataclasses import dataclass
from typing import Any


@dataclass
class Field:
    key: str
    path: str
    is_jq_filter: bool

    def parse(self, data: Any) -> dict[str, str]:
        """Parse this field based on the provided data resolving jq filters if needed."""

        result: str
        if self.is_jq_filter:
            result = self._eval_jq_filter(data)
        else:
            result = dict(data).get(self.path) or ""
        return {self.key: result}

    def _eval_jq_filter(self, data: Any) -> str:
        """Run jq as subprocess on the given data and return the result as a string."""
        result = subprocess.run(
            ("jq", self.path), input=json.dumps(data), capture_output=True, text=True
        )
        if result.returncode == 0:
            value = json.loads(result.stdout)
        else:
            raise ValueError(f"jq filter failed for '{self.path}': {result.stderr}")
        return value


def parse_field_def(definition: list[str] | dict[str, str] | None) -> list[Field]:
    """Parse different possible types of an API field definition."""
    # Handle empty definition
    if definition is None:
        return []

    # Handle list format
    if isinstance(definition, list):
        results: list[Field] = []
        for key in definition:
            if key in (f.key for f in results):
                raise NameError(f"Duplicate field definition for '{key}'")
            results.append(Field(key=key, path=key, is_jq_filter=False))
        return results

    # Handle dict format
    if isinstance(definition, dict):
        return [Field(key=key, path=path, is_jq_filter=True) for key, path in definition.items()]

    raise TypeError("Invalid field definition.")
