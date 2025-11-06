from pathlib import Path

from components.apercu_video import ApercuVideos


def test_apercu_videos_limits_to_six_items(qapp, tmp_path):
    # Create more than six dummy video files
    for index in range(8):
        (Path(tmp_path) / f"video_{index}.mp4").write_bytes(b"data")

    widget = ApercuVideos(str(tmp_path))

    assert len(widget.videos) == 6
    assert all(name.endswith(".mp4") for name in widget.videos)
