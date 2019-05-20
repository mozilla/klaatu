import os
import typing

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from tests.toolbar import ToolBar


@pytest.mark.nondestructive
def test_experiment_does_not_stop_startup(selenium: typing.Any, addon_ids):
    """Experiment does not stop browser startup, or prohibit a clean exit."""
    selenium.get("https://www.allizom.org")
    toolbar = ToolBar(selenium)
    for item in toolbar.toolbar_items:
        if addon_ids[0] not in item._id:
            continue
        else:
            assert True  # Experiment is installed


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


@pytest.mark.last
@pytest.mark.nondestructive
@pytest.mark.skipif(
    not pytest.config.option.run_old_firefox,
    reason="needs --run-old-firefox option to run",
)
def test_experiment_does_not_stop_update(addon_ids: list, selenium: typing.Any):
    """Experinemt should not block firefox updates."""
    selenium.get("about:profiles")
    with selenium.context(selenium.CONTEXT_CHROME):
        selenium.find_element_by_id("PanelUI-menu-button").click()
        WebDriverWait(selenium, 30).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".panel-banner-item")),
            message="Update banner not found",
        )
        banner = selenium.find_element_by_css_selector(".panel-banner-item")
        banner.click()
    selenium.quit()

    # Start firefox again with new selenium driver
    # Build new Firefox Instance
    profile = FirefoxProfile(f'{os.path.abspath("utilities/klaatu-profile")}')
    options = Options()
    options.add_argument("-profile")
    options.add_argument(f'{os.path.abspath("utilities/klaatu-profile")}')
    options.add_argument("-headless")
    binary = os.path.abspath("utilities/firefox-old-nightly/firefox/firefox-bin")
    options.binary = binary

    # Start Firefox and test
    selenium = webdriver.Firefox(
        firefox_binary=binary, firefox_profile=profile, firefox_options=options
    )
    selenium.get("https://www.allizom.org")
    with selenium.context(selenium.CONTEXT_CHROME):
        selenium.find_element_by_id("PanelUI-menu-button").click()
        WebDriverWait(selenium, 10).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, ".panel-banner-item")),
            message="Update banner found, maybe firefox didn't update?",
        )
    toolbar = ToolBar(selenium)
    for item in toolbar.toolbar_items:
        if addon_ids[0] not in item._id:
            continue
        else:
            assert True  # Experiment is installed
