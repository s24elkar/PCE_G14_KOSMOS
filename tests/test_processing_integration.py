import numpy as np
import cv2

from models import app_model as ac


def test_dehaze_and_denoise_pipeline_runs_end_to_end():
    # Image synthétique avec dégradés et léger flou pour simuler le "haze".
    height, width = 60, 80
    gradient = np.linspace(60, 220, width, dtype=np.uint8)
    base = np.zeros((height, width, 3), dtype=np.uint8)
    base[:, :, 0] = gradient  # canal bleu
    base[:, :, 1] = 90
    base[:, :, 2] = np.flip(gradient)  # canal rouge
    hazy = cv2.blur(base, (5, 5))

    atm = ac.atm_calculation(hazy)
    dehazed = ac.process_image_dehaze(
        hazy,
        atm,
        window=9,
        omega=0.8,
        guided_radius=15,
        guided_eps=1e-4,
        tx=0.2,
    )
    denoised = ac.denoise_image(
        dehazed,
        method="nlm",
        h=8,
        hColor=8,
        templateWindowSize=3,
        searchWindowSize=7,
    )

    assert dehazed.shape == hazy.shape == denoised.shape
    assert dehazed.dtype == np.uint8
    assert denoised.dtype == np.uint8
    assert not np.array_equal(hazy, dehazed)
    assert dehazed.min() >= 0 and dehazed.max() <= 255
    assert ac.tenengrad_contrast(denoised) > 0


def test_motion_detection_pipeline_detects_moving_object():
    subtractor = ac.init_motion_detector(history=3, var_threshold=8, detect_shadows=False)
    static_frame = np.zeros((120, 160, 3), dtype=np.uint8)

    # Phase de "warmup" : on nourrit l'algorithme avec un fond stable.
    for _ in range(3):
        ac.detect_moving_subjects(static_frame, subtractor, min_area=30)

    detections = []
    moving_frame = static_frame
    for i in range(4):
        moving_frame = static_frame.copy()
        cv2.rectangle(
            moving_frame,
            (10 + 15 * i, 50),
            (40 + 15 * i, 80),
            (255, 255, 255),
            -1,
        )
        detections = ac.detect_moving_subjects(moving_frame, subtractor, min_area=50)

    assert detections, "Le détecteur devrait repérer le déplacement du carré blanc."

    annotated = ac.annotate_detections(moving_frame, detections)
    assert annotated.shape == moving_frame.shape
    for detection in detections:
        x, y, w, h = detection["bbox"]
        assert w > 0 and h > 0
