from components.Explorateur_dossier import WinLikeExplorer


def test_win_like_explorer_navigation(qapp, tmp_path):
    explorer = WinLikeExplorer(start_path=str(tmp_path))

    assert explorer.current_path() == str(tmp_path)

    nested = tmp_path / "nested"
    nested.mkdir()

    explorer.navigate_to(str(nested))

    assert explorer.current_path() == str(nested)
    assert explorer.path_edit.text() == str(nested)
