from components.navbar import NavBar


def test_navbar_default_tab(qapp):
    navbar = NavBar()
    assert navbar.get_active_tab() == "Tri"
    assert len(navbar.tab_buttons) == 4


def test_navbar_tab_change_emits_signal(qapp):
    navbar = NavBar()
    captured = []
    navbar.tab_changed.connect(captured.append)

    navbar.set_active_tab("Extraction")

    assert navbar.get_active_tab() == "Extraction"
    assert captured == ["Extraction"]

    # A repeated activation should keep button checked
    navbar.set_active_tab("Extraction")
    assert navbar.tab_buttons["Extraction"].isChecked()
