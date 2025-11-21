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


def test_media_explorer_toggle_view_mode(qapp):
    explorer = MediaExplorer()
    explorer.add_video("Vid1")
    explorer.add_video("Vid2")

    # Vue grille: deuxième élément doit être en colonne 1, ligne 0
    assert explorer.content_layout.itemAtPosition(0, 1).widget() is explorer.thumbnails[1]

    captured = []
    explorer.view_mode_changed.connect(captured.append)

    explorer.set_view_mode("list")

    assert explorer.view_mode == "list"
    assert explorer.content_layout.itemAtPosition(1, 0).widget() is explorer.thumbnails[1]
    assert explorer.content_layout.itemAtPosition(0, 1) is None
    assert captured == ["list"]
