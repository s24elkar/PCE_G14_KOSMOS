from components.histogramme import Histogram


def test_histogram_updates_data(qapp):
    histogram = Histogram()
    sample = [i for i in range(256)]

    histogram.update_histogram(data_r=sample, data_g=sample, data_b=sample)

    internal = histogram.histogram_widget
    assert internal.data_r == sample
    assert internal.data_g == sample
    assert internal.data_b == sample


def test_histogram_refresh_generates_new_data(qapp):
    histogram = Histogram()
    before = (
        list(histogram.histogram_widget.data_r),
        list(histogram.histogram_widget.data_g),
        list(histogram.histogram_widget.data_b),
    )

    histogram.refresh()

    after = (
        histogram.histogram_widget.data_r,
        histogram.histogram_widget.data_g,
        histogram.histogram_widget.data_b,
    )

    assert any(a != b for a, b in zip(before, after))
