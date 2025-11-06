from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(slots=True)
class Campaign:
    name: str
    description: str = ""


class CampaignModel:
    """
    Stores campaigns available on the accueil screen.
    """

    def __init__(self, initial: Optional[List[Campaign]] = None) -> None:
        self._campaigns: List[Campaign] = list(initial or [])
        self.last_opened: Optional[str] = None

    def campaigns(self) -> List[Campaign]:
        return list(self._campaigns)

    def add_campaign(self, name: str, description: str = "") -> Campaign:
        if not name.strip():
            raise ValueError("Campaign name cannot be empty")
        # Prevent duplicates based on name.
        for campaign in self._campaigns:
            if campaign.name == name:
                raise ValueError(f"Campaign '{name}' already exists")
        campaign = Campaign(name=name, description=description)
        self._campaigns.append(campaign)
        return campaign

    def open_campaign(self, name: str) -> Campaign:
        for campaign in self._campaigns:
            if campaign.name == name:
                self.last_opened = name
                return campaign
        raise ValueError(f"Campaign '{name}' not found")
