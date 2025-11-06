import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")

from kosmos_processing import algos_correction as ac


def test_float_conversions_roundtrip():
    arr = np.linspace(0, 1, 9, dtype=np.float32).reshape(3, 3)
    converted = ac.Float2BGR(arr)
    assert converted.dtype == np.uint8
    restored = ac.BGR2Float(converted)
    np.testing.assert_allclose(restored, arr.astype(np.float64), atol=1 / 255)


def test_process_image_he_outputs_uint8_image():
    image = np.random.randint(0, 255, size=(8, 8, 3), dtype=np.uint8)
    processed = ac.process_image_HE(image.astype(np.float64), 1.0, 1.0, 1.0)
    assert processed.shape == image.shape
    assert processed.dtype == np.uint8


def test_dark_channel_and_transmission_pipeline():
    image = np.full((4, 4, 3), 0.5, dtype=np.float32)
    dark = ac.DarkChannel(image, 3)
    assert dark.shape == (4, 4)

    atm = ac.AtmLight(image, dark)
    assert atm.shape == (1, 3)

    transmission = ac.TransmissionEstimate(image, atm, 3)
    assert transmission.shape == (4, 4)

    refined = ac.TransmissionRefine((image * 255).astype(np.uint8), transmission)
    assert refined.shape == (4, 4)
