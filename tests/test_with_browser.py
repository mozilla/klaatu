import typing

import pytest

from tests.toolbar import ToolBar


@pytest.mark.nondestructive
def test_experiment_does_not_stop_startup(selenium: typing.Any):
    """Experiment does not stop browser startup, or prohibit a clean exit."""
    selenium.get("https://www.mozilla.org")


@pytest.mark.nondestructive
def test_private_browsing_disables_experiment(
    firefox: typing.Any, selenium: typing.Any, addon_ids: list
):
    """Experiment should be disabled in private browsing mode."""
    new_browser = firefox.browser.open_window(private=True)
    assert new_browser.is_private
    toolbar = ToolBar(selenium)
    for item in toolbar.toolbar_items:
        if addon_ids[0] not in item._id:
            continue
        else:
            raise AssertionError("Extension is Found")


@pytest.mark.nondestructive
def test_experiment_does_not_drastically_slow_firefox(
    firefox_startup_time: int, selenium: typing.Any
):
    """Experiment should not slow firefox down by more then 20%."""
    startup = selenium.execute_script(
        """
        perfData = window.performance.timing 
        return perfData.loadEventEnd - perfData.navigationStart
        """
    )
    assert ((firefox_startup_time * 0.2) + firefox_startup_time) >= startup


@pytest.mark.nondestructive
def test_experiment_shows_on_support_page(selenium: typing.Any, addon_ids: list):
    """Experiment should show on about:support page."""
    selenium.get("about:support")
    extensions = selenium.find_element_by_id("extensions-tbody")
    items = extensions.find_elements_by_css_selector("tr > td")
    for item in items:
        if addon_ids[0] not in item.text:
            continue
        else:
            assert True, "Extension Found"
