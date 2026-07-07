import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import kubelb as kb


def test_gini_uniform_is_zero() -> None:
    assert kb.gini([5, 5, 5, 5]) == 0.0


def test_gini_single_is_max() -> None:
    # all load on one of 4 -> gini = (n-1)/n = 0.75
    assert abs(kb.gini([20, 0, 0, 0]) - 0.75) < 1e-9


def test_gini_empty_is_zero() -> None:
    assert kb.gini([0, 0, 0, 0]) == 0.0


def test_coverage() -> None:
    assert kb.coverage(["a", "b", "a", "c"]) == 3
    assert kb.coverage(["a", "a", "a"]) == 1


def test_starved() -> None:
    assert kb.starved([5, 0, 3, 0]) == 2
    assert kb.starved([1, 1, 1, 1]) == 0


def test_occupancy_expected() -> None:
    assert abs(kb.occupancy_expected(4, 1) - 1.0) < 1e-9
    assert abs(kb.occupancy_expected(4, 2) - 1.75) < 1e-9
    assert abs(kb.occupancy_expected(4, 4) - 2.734375) < 1e-9
    assert abs(kb.occupancy_expected(4, 8) - 3.599548) < 1e-5
