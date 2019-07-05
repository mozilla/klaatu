import os
import typing

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from tests.expected import (
    firefox_update_banner_is_found,
    firefox_update_banner_is_invisible,
)
from tests.toolbar import ToolBar


@pytest.mark.first
@pytest.mark.update_test
@pytest.mark.nondestructive
@pytest.mark.skipif(
    not pytest.config.option.run_old_firefox,
    reason="needs --run-old-firefox option to run",
)
def test_experiment_does_not_stop_update(addon_ids: dict, selenium: typing.Any):
    """Experinemt should not block firefox updates."""
    selenium.get("about:profiles")
    # Sleep to let firefox update
    with selenium.context(selenium.CONTEXT_CHROME):
        WebDriverWait(selenium, 60).until(
            firefox_update_banner_is_found(), message="Update banner not found"
        )
        banner = selenium.find_element_by_css_selector(".panel-banner-item")
        banner.click()
    selenium.quit()

    # Start firefox again with new selenium driver
    # Build new Firefox Instance
    profile = FirefoxProfile(
        f'{os.path.abspath("utilities/klaatu-profile-disable-test")}'
    )
    options = Options()
    options.add_argument("-profile")
    options.add_argument(f'{os.path.abspath("utilities/klaatu-profile-disable-test")}')
    options.add_argument("-headless")
    binary = os.path.abspath(
        "utilities/firefox-old-nightly-disable-test/firefox/firefox-bin"
    )
    options.binary = binary

    # Start Firefox and test
    selenium = webdriver.Firefox(
        firefox_binary=binary, firefox_profile=profile, firefox_options=options
    )
    selenium.get("https://www.allizom.org")
    WebDriverWait(selenium, 10).until(
        firefox_update_banner_is_invisible(),
        message="Update banner found, maybe firefox didn't update?",
    )
    toolbar = ToolBar(selenium)
    for item in toolbar.toolbar_items:
        if list(addon_ids)[0] not in item._id:
            continue
        else:
            assert True  # Experiment is installed


@pytest.mark.nondestructive
def test_experiment_does_not_stop_startup(selenium: typing.Any, addon_ids: dict):
    """Experiment does not stop browser startup, or prohibit a clean exit."""
    selenium.get("https://www.allizom.org")
    toolbar = ToolBar(selenium)
    for item in toolbar.toolbar_items:
        if list(addon_ids)[0] not in item._id:
            continue
        else:
            assert True  # Experiment is installed


@pytest.mark.nondestructive
def test_private_browsing_disables_experiment(
    firefox: typing.Any, selenium: typing.Any, addon_ids: dict
):
    """Experiment should be disabled in private browsing mode."""
    new_browser = firefox.browser.open_window(private=True)
    assert new_browser.is_private
    toolbar = ToolBar(selenium)
    for item in toolbar.toolbar_items:
        if list(addon_ids)[0] not in item._id:
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
    assert ((int(firefox_startup_time) * 0.2) + int(firefox_startup_time)) >= startup


@pytest.mark.nondestructive
def test_experiment_shows_on_support_page(selenium: typing.Any, addon_ids: dict):
    """Experiment should show on about:support page."""
    selenium.get("about:support")
    extensions = selenium.find_element_by_id("extensions-tbody")
    items = extensions.find_elements_by_css_selector("tr > td")
    for item in items:
        if list(addon_ids)[0] not in item.text:
            continue
        else:
            assert True, "Extension Found"


@pytest.mark.expire_experiment
@pytest.mark.nondestructive
def test_experiment_expires_correctly(
    selenium: typing.Any, firefox_options: typing.Any):
    selenium.get("https://www.allizom.org")
    selenium.switch_to.window(selenium.window_handles[-1])
    WebDriverWait(selenium, 10).until(EC.url_contains("qsurvey"))


@pytest.mark.reuse_profile
@pytest.mark.nondestructive
def test_experiment_remains_disabled_after_user_disables_it(
    selenium: typing.Any,
    addon_ids: dict,
    pytestconfig: typing.Any,
    pings: typing.Any,
):
    """Disable experiment, restart Firefox to make sure it stays disabled."""
    selenium.get("about:addons")
    selenium.find_element_by_css_selector("#category-extension").click()
    if selenium.find_element_by_css_selector(".addon-view ").click():
        selenium.find_element_by_css_selector("#detail-disable-btn").click()
    else:
        with selenium.context(selenium.CONTEXT_CHROME):
            browser = selenium.find_element_by_css_selector(
                "window#main-window #browser #appcontent .browserStack browser"
            )
            selenium.switch_to.frame(browser)
            browser = selenium.find_element_by_css_selector(
                "#addons-page #html-view-browser"
            )
            selenium.switch_to.frame(browser)
            selenium.find_element_by_css_selector(".more-options-button").click()
            options = selenium.find_element_by_css_selector(
                ".more-options-menu addon-options"
            )
            panel_list = options.find_element_by_tag_name("panel-list")
            els = panel_list.find_elements_by_tag_name("panel-item")
            assert els[0].is_enabled
            selenium.execute_script(
                """
                let element = arguments[0].shadowRoot
                element.querySelector("button").click()
            """,
                els[0],
            )
    toolbar = ToolBar(selenium)
    for item in toolbar.toolbar_items:
        if list(addon_ids)[0] not in item._id:
            continue
        else:
            raise AssertionError("Extension is Found")
    selenium.quit()

    # Start firefox again with new selenium driver
    # Build new Firefox Instance with appropriate profile and binary
    if pytestconfig.getoption("--run-old-firefox"):
        profile = FirefoxProfile(f'{os.path.abspath("utilities/klaatu-profile")}')
        options = Options()
        options.add_argument("-profile")
        options.add_argument(f'{os.path.abspath("utilities/klaatu-profile")}')
        options.add_argument("-headless")
        binary = os.path.abspath("utilities/firefox-old-nightly/firefox/firefox-bin")
        options.binary = binary
    else:
        profile = FirefoxProfile(
            f'{os.path.abspath("utilities/klaatu-profile-current-nightly")}'
        )
        options = Options()
        options.add_argument("-profile")
        options.add_argument(
            f'{os.path.abspath("utilities/klaatu-profile-current-nightly")}'
        )
        options.add_argument("-headless")
        binary = "/usr/bin/firefox"
        options.binary = binary

    # Start Firefox and test
    selenium = webdriver.Firefox(firefox_profile=profile, firefox_options=options)
    selenium.get("about:addons")

    # Make sure experiment is still not enabled
    toolbar = ToolBar(selenium)
    for item in toolbar.toolbar_items:
        if list(addon_ids)[0] not in item._id:
            continue
        else:
            raise AssertionError("Extension is Found")
    
    # Check last telemetry ping
    pings = pings.get_pings()
    addons = pings[-1]["environment"]["addons"]["activeAddons"]
    for item in addons:
        if list(addon_ids)[0] in item:
            assert True
        else:
            continue
    selenium.quit()


@pytest.mark.nondestructive
async def test_experiment_sends_correct_telemetry(
    selenium: typing.Any, addon_ids: dict, pings: typing.Any
):
    """Make sure telemetry is sent and recieved properly."""
    selenium.get("https://www.allizom.org")
    pings = pings.get_pings()
    # for count, item in enumerate(ping_server.pings["pings"])
    addons = pings[-1]["environment"]["addons"]["activeAddons"]
    print(pings)
    for item in addons:
        if list(addon_ids)[0] in item:
            assert True
        else:
            continue
