from __future__ import annotations

from models.campaign_model import CampaignModel


class AccueilController:
    """
    Coordinates the accueil view with the campaign model.
    """

    def __init__(self, view, model: CampaignModel):
        self.view = view
        self.model = model

        self.view.set_controller(self)
        self.load_initial_data()

    def load_initial_data(self) -> None:
        self.view.show_campaigns(campaign.name for campaign in self.model.campaigns())

    def on_new_campaign(self, name: str) -> None:
        try:
            self.model.add_campaign(name)
        except ValueError as exc:
            self.view.show_error(str(exc))
            return
        self.view.show_campaigns(campaign.name for campaign in self.model.campaigns())
        self.view.clear_name_input()
        self.view.show_information(f"Campagne '{name}' ajoutée.")

    def on_open_campaign(self, name: str) -> None:
        try:
            campaign = self.model.open_campaign(name)
        except ValueError as exc:
            self.view.show_error(str(exc))
            return
        self.view.show_information(f"Campagne '{campaign.name}' ouverte.")
