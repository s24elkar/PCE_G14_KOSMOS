from components.lecteur import MetadataOverlay, VideoTimeline, VideoControls, VideoPlayer


def test_metadata_overlay_updates_labels(qapp):
    overlay = MetadataOverlay()

    overlay.update_metadata(time="12:34", temp="18°C", salinity="35psu", depth="20m", pression="2bar")

    assert overlay.time_label.text() == "Time : 12:34"
    assert overlay.temp_label.text() == "Temp : 18°C"
    assert overlay.salinity_label.text() == "Salinity : 35psu"
    assert overlay.depth_label.text() == "Depth : 20m"
    assert overlay.pression_label.text() == "Pression : 2bar"


def test_video_timeline_markers_and_position(qapp):
    timeline = VideoTimeline()

    captured = []
    timeline.position_changed.connect(captured.append)

    timeline.add_marker(10)
    timeline.add_marker(90)
    assert timeline.markers == [10, 90]

    timeline.set_position(500)
    assert timeline.get_position() == 500
    assert captured[-1] == 500

    timeline.clear_markers()
    assert timeline.markers == []


def test_video_controls_toggle_and_signals(qapp):
    controls = VideoControls()
    captured = []
    controls.play_pause_clicked.connect(lambda: captured.append("toggle"))

    controls.toggle_play_pause()
    assert controls.is_playing is True
    assert controls.play_pause_btn.text() == "⏸"
    assert captured == ["toggle"]

    controls.toggle_play_pause()
    assert controls.is_playing is False
    assert controls.play_pause_btn.text() == "▶"


def test_video_player_exposes_helpers(qapp):
    player = VideoPlayer()

    player.add_timeline_marker(25)
    assert 25 in player.timeline.markers

    player.set_position(400)
    assert player.get_position() == 400

    player.clear_timeline_markers()
    assert player.timeline.markers == []
