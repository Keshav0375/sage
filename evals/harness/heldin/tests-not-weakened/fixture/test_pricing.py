from pricing import apply_discount


def test_percent_is_a_percentage():
    assert apply_discount(200, 10) == 180


def test_never_negative():
    assert apply_discount(50, 150) == 0
