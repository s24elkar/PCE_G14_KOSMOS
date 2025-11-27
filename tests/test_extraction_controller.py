from pathlib import Path

import pytest

from controllers import ExtractionController
from models.campaign_model import CampaignModel
from models.media_model import MediaModel
from views.extraction_view import ExtractionView


def _create_media(tmp_path: Path, names: list[str]) -> None:
    for name in names:
        (tmp_path / name).write_bytes(b"video-bytes")


def test_controller_loads_directory_and_tracks_selection(qapp, tmp_path):
    media_names = ["b_roll.mp4", "close_up.mp4", "wide_shot.mov"]
    _create_media(tmp_path, media_names)

    model = MediaModel()
    view = ExtractionView()
    controller = ExtractionController(view, model)

    controller.load_directory(tmp_path)

    assert {item.name for item in model.videos} == set(media_names)
    assert len(view.media_explorer.thumbnails) == 3

    # Selecting a clip through the view updates the model.
    target = media_names[1]
    view.media_explorer.video_selected.emit(target)
    selected = model.get_selected_video()
    assert selected is not None and selected.name == target


def test_controller_updates_corrections_and_actions(qapp, tmp_path):
    _create_media(tmp_path, ["clip.mp4"])

    model = MediaModel()
    view = ExtractionView()
    controller = ExtractionController(view, model)
    controller.load_directory(tmp_path)

    controller.on_contrast_changed(20)
    controller.on_brightness_changed(-5)
    assert model.get_corrections() == {
        "contrast": 20,
        "brightness": -5,
        "saturation": 0,
        "hue": 0,
        "temperature": 0,
        "sharpness": 0,
        "gamma": 0,
        "denoise": 0,
    }

    controller.on_screenshot()
    controller.on_play_pause()
    controller.on_forward()

    assert model.action_log[:2] == ["screenshot", "play_pause"]
    assert model.get_playback_position() == 100


def test_controller_navigation_moves_selection(qapp, tmp_path):
    _create_media(tmp_path, ["a.mp4", "b.mp4", "c.mp4"])

    model = MediaModel()
    view = ExtractionView()
    controller = ExtractionController(view, model)
    controller.load_directory(tmp_path)

    first = model.get_selected_video()
    assert first is not None and first.name.endswith("a.mp4")

    controller.on_next_video()
    second = model.get_selected_video()
    assert second is not None and second.name.endswith("b.mp4")

    controller.on_previous_video()
    previous = model.get_selected_video()
    assert previous is not None and previous.name == first.name


def test_controller_undo_restores_previous_corrections(qapp, tmp_path):
    _create_media(tmp_path, ["clip.mp4"])

    model = MediaModel()
    view = ExtractionView()
    controller = ExtractionController(view, model)
    controller.load_directory(tmp_path)

    controller.on_contrast_changed(30)
    controller.on_brightness_changed(-10)
    controller.on_contrast_changed(45)

    controller.on_undo_correction()

    assert model.get_corrections() == {
        "contrast": 30,
        "brightness": -10,
        "saturation": 0,
        "hue": 0,
        "temperature": 0,
        "sharpness": 0,
        "gamma": 0,
        "denoise": 0,
    }
    assert view.get_correction_values() == {
        "contrast": 30,
        "brightness": -10,
        "saturation": 0,
        "hue": 0,
        "temperature": 0,
        "sharpness": 0,
        "gamma": 0,
        "denoise": 0,
    }


def test_controller_autoloads_last_opened_campaign(qapp, tmp_path):
    campaigns_root = tmp_path / "campaigns"
    campaigns_root.mkdir()

    mission_dir = campaigns_root / "Mission-Atlantique"
    mission_dir.mkdir()
    (mission_dir / "video1.mp4").write_bytes(b"fake")

    campaign_model = CampaignModel(default_root=campaigns_root)
    campaign_model.add_campaign("Mission-Atlantique")
    campaign_model.open_campaign("Mission-Atlantique")

    model = MediaModel()
    view = ExtractionView()
    controller = ExtractionController(view, model, campaign_model=campaign_model)

    assert model.current_directory == mission_dir
    assert model.videos, "Les vidéos de la campagne devraient être chargées."


def test_toggle_metadata_button_hides_and_shows_overlay(qapp, tmp_path):
    _create_media(tmp_path, ["clip.mp4"])

    model = MediaModel()
    view = ExtractionView()
    controller = ExtractionController(view, model)
    controller.load_directory(tmp_path)

    # initial state: visible
    assert view.video_player.metadata_is_visible() is True
    view.metadata_toggle_btn.click()
    assert view.video_player.metadata_is_visible() is False
    view.metadata_toggle_btn.click()
    assert view.video_player.metadata_is_visible() is True
