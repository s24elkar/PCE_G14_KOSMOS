from __future__ import annotations

from typing import Dict


class MetadataModel:
    """
    Holds the shared metadata for the tri workflow.

    Controllers update this model when the operator edits the values and
    retrieve the current snapshot to refresh the view.
    """

    def __init__(self, initial: Dict[str, str] | None = None) -> None:
        self._common_metadata: Dict[str, str] = dict(initial or {})

    def get_common_metadata(self) -> Dict[str, str]:
        """Return a copy of the current metadata."""
        return dict(self._common_metadata)

    def update_common_metadata(self, updates: Dict[str, str]) -> Dict[str, str]:
        """
        Merge the provided key/value pairs into the store.

        Returns the updated snapshot to allow fluent controller code.
        """
        for key, value in updates.items():
            self._common_metadata[key] = value
        return self.get_common_metadata()
