from src.bottleneck.compute import escape_level, score_layers


def _series(start: float, end: float, n: int = 80):
    step = (end - start) / (n - 1)
    return [(f"d{i:03d}", start + step * i) for i in range(n)]


def test_strongest_rising_layer_is_tightest():
    layers = {"a": ("A", ["UP"]), "b": ("B", ["DOWN"])}
    prices = {"UP": _series(100, 150), "DOWN": _series(100, 60)}
    rows = {r["key"]: r for r in score_layers(layers, prices)}
    assert rows["a"]["tightness"] == 100
    assert rows["b"]["tightness"] == 0


def test_escape_level_from_ai_bubble():
    assert escape_level({"composite_level": "green", "market_level": "yellow", "stage": 1})["level"] == 0
    assert escape_level({"composite_level": "green", "market_level": "orange", "stage": 3})["level"] == 1
    assert escape_level({"composite_level": "yellow", "stage": 5})["level"] == 3
