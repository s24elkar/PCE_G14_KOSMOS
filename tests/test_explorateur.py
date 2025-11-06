from components.explorateur import MediaExplorer


def test_media_explorer_add_and_select(qapp):
    explorer = MediaExplorer()

    explorer.add_video("Vid1")
    explorer.add_video("Vid2", "#123456")

    assert len(explorer.thumbnails) == 2
    assert explorer.selected_thumbnail is None

    captured = []
    explorer.video_selected.connect(captured.append)

    explorer.on_thumbnail_clicked("Vid2")

    assert explorer.selected_thumbnail is explorer.thumbnails[1]
    assert captured == ["Vid2"]


def test_media_explorer_clear_videos(qapp):
    explorer = MediaExplorer()
    explorer.add_video("Vid1")

    explorer.clear_videos()

    assert len(explorer.thumbnails) == 0
    assert explorer.selected_thumbnail is None
