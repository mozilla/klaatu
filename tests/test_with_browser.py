import pytest

from tests.toolbar import ToolBar


@pytest.mark.nondestructive
def test_experiment_does_not_stop_startup(selenium):
    """Experiment does not stop browser startup, or prohibit a clean exit."""
    selenium.get("https://www.mozilla.org")


@pytest.mark.nondestructive
def test_private_browsing_disables_experiment(firefox, selenium):
    """Experiment should be disabled in private browsing mode."""
    new_browser = firefox.browser.open_window(private=True)
    assert new_browser.is_private
    toolbar = ToolBar(selenium)
    for item in toolbar.toolbar_items:
        if "shield.mozilla.org" not in item._id:
            continue
        else:
            raise AssertionError("Extension is Found")


@pytest.mark.nondestructive
def test_experiment_does_not_drastically_slow_firefox(firefox_startup_time, selenium):
    """Experiment should not slow firefox down by more then 20%."""
    startup = selenium.execute_script(
        """
        perfData = window.performance.timing 
        return perfData.loadEventEnd - perfData.navigationStart
        """
    )
    assert (firefox_startup_time * 0.02) < startup
