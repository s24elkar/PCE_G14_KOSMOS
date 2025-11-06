from __future__ import annotations

from typing import Dict

from models.metadata_model import MetadataModel


class TriController:
    """
    Coordinates the tri view with the metadata model.
    """

    def __init__(self, view, metadata_model: MetadataModel):
        self.view = view
        self.model = metadata_model

        self.view.set_controller(self)
        self.load_initial_data()

    def load_initial_data(self) -> None:
        self.view.show_common_metadata(self.model.get_common_metadata())

    def on_common_metadata_save(self, payload: Dict[str, str]) -> None:
        updated = self.model.update_common_metadata(payload)
        self.view.show_common_metadata(updated)
        self.view.show_success_dialog()
