from components.correction import ImageCorrection


def test_image_correction_default_values(qapp):
    correction = ImageCorrection()

    values = correction.get_contrast(), correction.get_brightness()
    assert values == (0, 0)


def test_image_correction_signals_and_reset(qapp):
    correction = ImageCorrection()

    captured = {"contrast": [], "brightness": []}
    correction.contrast_changed.connect(lambda value: captured["contrast"].append(value))
    correction.brightness_changed.connect(lambda value: captured["brightness"].append(value))

    correction.contrast_slider.set_value(25)
    correction.brightness_slider.set_value(-10)

    assert correction.get_contrast() == 25
    assert correction.get_brightness() == -10

    correction.reset_all()
    assert correction.get_contrast() == 0
    assert correction.get_brightness() == 0

    assert captured["contrast"][-1] == 25
    assert captured["brightness"][-1] == -10


def test_image_correction_apply_and_undo_signals(qapp):
    correction = ImageCorrection()

    apply_hits, undo_hits = [], []
    correction.apply_clicked.connect(lambda: apply_hits.append(True))
    correction.undo_clicked.connect(lambda: undo_hits.append(True))

    correction.apply_btn.click()
    correction.undo_btn.click()

    assert apply_hits and undo_hits

    # set_corrections ne doit pas réémettre les signaux des sliders
    before_counts = (len(apply_hits), len(undo_hits))
    correction.set_corrections(40, -20)
    assert correction.get_contrast() == 40
    assert correction.get_brightness() == -20
    assert (len(apply_hits), len(undo_hits)) == before_counts
