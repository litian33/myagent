# experiments/p5_8_bug/test_username.py

from username import normalize_username


def test_normalize_username_lowercases_name() -> None:
    assert normalize_username(" Alice Smith ") == "alice_smith"


def test_normalize_username_collapses_whitespace() -> None:
    assert normalize_username("  ALICE   SMITH  ") == "alice_smith"


def test_normalize_username_preserves_normalized_value() -> None:
    assert normalize_username("alice_smith") == "alice_smith"
