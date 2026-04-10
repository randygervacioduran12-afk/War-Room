from f70_reports_morning_brief import build_morning_brief


def test_reports_module_imports():
    assert callable(build_morning_brief)