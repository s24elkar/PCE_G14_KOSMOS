from PyQt6.QtWidgets import QMessageBox

from controllers.accueil_controller import AccueilController
from models.campaign_model import CampaignModel
from views.accueil_view import AccueilView


def test_accueil_controller_adds_campaign_and_shows_message(qapp, monkeypatch):
    model = CampaignModel()
    view = AccueilView()
    controller = AccueilController(view, model)

    info_messages = []
    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *args: info_messages.append(args[2]),
    )

    view.name_input.setText("Mission Atlantique")
    view.create_button.click()

    assert model.campaigns()[0].name == "Mission Atlantique"
    assert info_messages[-1] == "Campagne 'Mission Atlantique' ajoutée."
    assert view.name_input.text() == ""


def test_accueil_controller_validates_inputs(qapp, monkeypatch):
    model = CampaignModel()
    view = AccueilView()
    controller = AccueilController(view, model)

    errors = []
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *args: errors.append(args[2]),
    )
    monkeypatch.setattr(QMessageBox, "information", lambda *args: None)

    # Empty name
    view.create_button.click()
    assert errors[-1] == "Veuillez saisir un nom de campagne."

    # Duplicate
    view.name_input.setText("Mission 1")
    view.create_button.click()
    view.name_input.setText("Mission 1")
    view.create_button.click()
    assert "exists" in errors[-1]
