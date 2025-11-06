from components.outils_modification import ExtractionTools


def test_extraction_tools_signals_triggered(qapp):
    tools = ExtractionTools()

    triggered = []

    tools.screenshot_clicked.connect(lambda: triggered.append("screenshot"))
    tools.recording_clicked.connect(lambda: triggered.append("recording"))
    tools.short_clicked.connect(lambda: triggered.append("short"))
    tools.crop_clicked.connect(lambda: triggered.append("crop"))

    tools.screenshot_btn.click()
    tools.recording_btn.click()
    tools.short_btn.click()
    tools.crop_btn.click()

    assert triggered == ["screenshot", "recording", "short", "crop"]
