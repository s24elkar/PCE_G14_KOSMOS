from components.metadonnees import Window


def test_metadonnees_window_display(qapp, capsys):
    window = Window()
    window.input1.setText("user")
    window.input2.setText("secret")

    window.display()

    captured = capsys.readouterr()
    assert "user" in captured.out
    assert "secret" in captured.out
