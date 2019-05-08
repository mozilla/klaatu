import pytest


@pytest.mark.nondestructive
def test_experiment_does_not_stop_startup(firefox, selenium):
    """Experiment does not stop browser startup, or prohibit a clean exit."""
    selenium.get("https://www.mozilla.org")