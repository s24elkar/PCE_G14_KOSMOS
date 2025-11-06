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
