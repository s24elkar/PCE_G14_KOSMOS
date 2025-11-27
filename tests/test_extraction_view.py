from views.extraction_view import ExtractionView


class DummyController:
    def __init__(self):
        self.load_calls = 0

    def load_initial_data(self):
        self.load_calls += 1


def test_extraction_view_initialises_components(qapp):
    controller = DummyController()
    view = ExtractionView(controller=controller)

    assert controller.load_calls == 1
    assert hasattr(view, "media_explorer")
    assert hasattr(view, "video_player")
    assert hasattr(view, "image_correction")
    assert hasattr(view, "histogram")

    videos = [
        {"name": "Vid1", "thumbnail_color": "#fff"},
        {"name": "Vid2"},
    ]
    view.update_video_list(videos)
    assert len(view.media_explorer.thumbnails) == 2

    view.image_correction.contrast_slider.set_value(15)
    view.image_correction.brightness_slider.set_value(-5)

    corrections = view.get_correction_values()
    assert corrections["contrast"] == 15
    assert corrections["brightness"] == -5
    # Les autres corrections avancées existent et restent à 0 par défaut
    for key in ("saturation", "hue", "temperature", "sharpness", "gamma", "denoise"):
        assert corrections.get(key) == 0

    view.reset_corrections()
    reset = view.get_correction_values()
    assert reset["contrast"] == 0
    assert reset["brightness"] == 0
