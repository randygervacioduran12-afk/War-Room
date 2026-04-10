from f82_bootstrap_checks import EXPECTED_TABLES


def test_expected_tables_not_empty():
    assert "runs" in EXPECTED_TABLES
    assert "tasks" in EXPECTED_TABLES