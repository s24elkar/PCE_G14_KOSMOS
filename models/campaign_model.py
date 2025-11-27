from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass(slots=True)
class Campaign:
    name: str
    description: str = ""
    media_directory: Optional[Path] = None


class CampaignModel:
    """
    Stores campaigns available on the accueil screen.
    """

    def __init__(self, initial: Optional[List[Campaign]] = None, default_root: Optional[Path | str] = None) -> None:
        self._campaigns: List[Campaign] = list(initial or [])
        self.last_opened: Optional[str] = None
        self.default_root: Optional[Path] = Path(default_root) if default_root else None

    def campaigns(self) -> List[Campaign]:
        return list(self._campaigns)

    def add_campaign(self, name: str, description: str = "", media_directory: Optional[Path | str] = None) -> Campaign:
        if not name.strip():
            raise ValueError("Campaign name cannot be empty")
        # Prevent duplicates based on name.
        for campaign in self._campaigns:
            if campaign.name == name:
                raise ValueError(f"Campaign '{name}' already exists")
        directory = Path(media_directory) if media_directory else None
        campaign = Campaign(name=name, description=description, media_directory=directory)
        self._campaigns.append(campaign)
        return campaign

    def open_campaign(self, name: str) -> Campaign:
        for campaign in self._campaigns:
            if campaign.name == name:
                self.last_opened = name
                return campaign
        raise ValueError(f"Campaign '{name}' not found")

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def resolve_campaign_path(self, name: str, base_dir: Optional[Path | str] = None) -> Path:
        """
        Retourne le dossier média associé à la campagne.

        - Si la campagne possède déjà un chemin, on le renvoie.
        - Sinon on construit: <base_dir or default_root or ./campaigns>/<name>
        """
        campaign = self.open_campaign(name)  # met aussi à jour last_opened
        if campaign.media_directory:
            return campaign.media_directory

        base = Path(base_dir) if base_dir else (self.default_root or Path("campaigns"))
        resolved = base / name
        campaign.media_directory = resolved
        return resolved
