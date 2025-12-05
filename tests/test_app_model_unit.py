import csv
from pathlib import Path

from models.app_model import ApplicationModel, Video


def _hms(seconds: int) -> str:
    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{sec:02d}"


def test_parse_time_to_seconds_accepts_multiple_formats_and_invalid_values():
    model = ApplicationModel()
    assert model._parse_time_to_seconds("11h46m54s") == 42414
    assert model._parse_time_to_seconds("11:46:54") == 42414
    assert model._parse_time_to_seconds("00:00:09.7") == 9
    assert model._parse_time_to_seconds("invalid") == 0
    assert model._parse_time_to_seconds(None) == 0


def test_charger_metadata_kosmos_csv_reads_common_fields(tmp_path: Path):
    csv_path = tmp_path / "0001.csv"
    csv_path.write_text(
        "system,camera,model,version,duration\nSYS,CAM,M1,1.0,00:05:00\n",
        encoding="utf-8",
    )
    video = Video("0001.mp4", str(tmp_path / "0001.mp4"), "0001")
    model = ApplicationModel()

    ok = model._charger_metadata_kosmos_csv(video, str(csv_path))

    assert ok is True
    assert video.metadata_communes == {
        "system": "SYS",
        "camera": "CAM",
        "model": "M1",
        "version": "1.0",
    }
    assert video.duree == "00:05:00"


def test_get_angle_event_times_returns_defaults_without_system_event(tmp_path: Path):
    model = ApplicationModel()
    campagne = model.creer_campagne("Test", str(tmp_path))

    video_dir = tmp_path / "0001"
    video_dir.mkdir()
    video_path = video_dir / "0001.mp4"
    video_path.write_bytes(b"\x00\x00")

    video = model._creer_video_depuis_fichier(str(video_path), "0001")
    campagne.ajouter_video(video)

    expected_default = [("00:00:01", 2)] * 6
    assert model.get_angle_event_times("0001.mp4") == expected_default


def test_get_angle_event_times_falls_back_when_start_encoder_missing(tmp_path: Path):
    model = ApplicationModel()
    campagne = model.creer_campagne("Test", str(tmp_path))

    video_dir = tmp_path / "0002"
    video_dir.mkdir()
    video_path = video_dir / "0002.mp4"
    video_path.write_bytes(b"\x00\x00")

    video = model._creer_video_depuis_fichier(str(video_path), "0002")
    campagne.ajouter_video(video)

    event_path = video_dir / "systemEvent.csv"
    with event_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["Event", "Fichier", "Heure"])
        for i in range(15):
            writer.writerow(["START MOTEUR", "0002_video.mp4", _hms(10 + i * 2)])

    seek_times = model.get_angle_event_times("0002.mp4")

    expected_times = [_hms(t) for t in (23, 25, 27, 29, 31, 33)]
    assert seek_times == [(t, 30) for t in expected_times]


def test_selectionner_video_updates_selection_flags(tmp_path: Path):
    model = ApplicationModel()
    campagne = model.creer_campagne("Test", str(tmp_path))

    video_a = Video("a.mp4", str(tmp_path / "a.mp4"), "0001")
    video_b = Video("b.mp4", str(tmp_path / "b.mp4"), "0002")
    campagne.ajouter_video(video_a)
    campagne.ajouter_video(video_b)

    selected = model.selectionner_video("a.mp4")
    assert selected is video_a
    assert video_a.est_selectionnee is True
    assert model.video_selectionnee is video_a

    selected = model.selectionner_video("b.mp4")
    assert selected is video_b
    assert video_a.est_selectionnee is False
    assert video_b.est_selectionnee is True
    assert model.video_selectionnee is video_b
