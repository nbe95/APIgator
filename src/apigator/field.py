"""Logic and container to handle field definitions for upstream APIs."""

from dataclasses import dataclass


@dataclass
class Field:
    key: str
    path: str
    is_jq_filter: bool

    @staticmethod
    def parse_field_def(definition: list[str] | dict[str, str] | None) -> list["Field"]:
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
            return [
                Field(key=key, path=path, is_jq_filter=True) for key, path in definition.items()
            ]

        raise TypeError("Invalid field definition.")
