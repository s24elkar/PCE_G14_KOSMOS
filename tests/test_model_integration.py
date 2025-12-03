import csv
import json
from pathlib import Path

from models.app_model import ApplicationModel


def _time_str(seconds: int) -> str:
    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{sec:02d}"


def test_importer_and_seek_times_pipeline(tmp_path: Path):
    root = tmp_path
    dossier = root / "0001"
    dossier.mkdir()

    video_path = dossier / "0001.mp4"
    video_path.write_bytes(b"\x00\x00")  # fichier factice suffisant pour l'import

    json_path = dossier / "0001.json"
    json_payload = {
        "video": {"hourDict": {"HMSOS": "00:00:10"}},
        "system": {"camera": "KOSMOS_CAM", "model": "v1"},
        "campaign": {"dateDict": {"date": "2024-01-15"}},
    }
    json_path.write_text(json.dumps(json_payload), encoding="utf-8")

    csv_path = dossier / "0001.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["system", "camera", "model", "version", "duree"])
        writer.writerow(["KOSMOS", "CAM", "A1", "0.1", "00:10:00"])

    events_path = dossier / "systemEvent.csv"
    with events_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["Event", "Fichier", "Heure"])
        writer.writerow(["START ENCODER", "0001_video.mp4", "00:00:10"])
        for i in range(16):
            writer.writerow(["START MOTEUR", "0001_video.mp4", _time_str(10 + i * 3)])

    model = ApplicationModel()
    model.creer_campagne("Test", str(root))

    resultats = model.importer_videos_kosmos(str(root))
    assert "0001.mp4" in resultats["videos_importees"]
    assert model.campagne_courante is not None
    assert model.campagne_courante.videos

    video = model.campagne_courante.obtenir_video("0001.mp4")
    assert video is not None
    assert video.metadata_communes["system"] == "KOSMOS"
    assert video.start_time_str == "00:00:10"

    seek_times = model.get_angle_event_times("0001.mp4")
    expected_events = [37, 40, 43, 46, 49, 52]  # 10e START MOTEUR et les 5 suivants
    expected = [(_time_str(event + 5 - 10), 30) for event in expected_events]
    assert seek_times == expected
