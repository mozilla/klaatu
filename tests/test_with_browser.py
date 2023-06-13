import os
from pathlib import Path
import time
import typing

import pytest
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    InvalidElementStateException,
)
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


@pytest.mark.nondestructive
def test_experiment_does_not_stop_startup(selenium: typing.Any):
    """Experiment does not stop browser startup, or prohibit a clean exit."""
    selenium.get("https://www.allizom.org")
    

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
    assert (
        (int(firefox_startup_time) * 0.2) + int(firefox_startup_time)
    ) >= startup, "This experiment caused a slowdown within Firefox."


@pytest.mark.nondestructive
def test_experiment_shows_on_support_page(selenium: typing.Any, experiment_slug: str):
    """Experiment should show on about:support page."""
    selenium.get("about:support")
    extensions = selenium.find_element(By.ID, "remote-experiments-tbody")
    items = extensions.find_elements(By.CSS_SELECTOR, "tr > td")
    for item in items:
        if experiment_slug not in item.text:
            continue
        else:
            assert True, "Extension Found"


@pytest.mark.nondestructive
def test_experiment_shows_on_studies_page(
    selenium: typing.Any, variables: dict
):
    """Experiment should show on about:studies page."""
    selenium.get("about:studies")
    WebDriverWait(selenium, 60).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".study-name")),
        message="Experiment not shown on about:studies.",
    )
    items = selenium.find_elements(By.CSS_SELECTOR, ".study-name")
    for item in items:
        if variables["userFacingName"] in item.text:
            assert (
                variables["userFacingDescription"]
                in selenium.find_element(By.CSS_SELECTOR, ".study-description").text
            )


# @pytest.mark.expire_experiment
# @pytest.mark.nondestructive
# def test_experiment_expires_correctly(
#     selenium: typing.Any,
#     firefox_options: typing.Any,
#     pings: typing.Any,
#     manifest_id: str,
#     addon_ids: dict,
# ):
#     selenium.get("about:addons")
#     loop = True
#     while loop:
#         all_pings = pings.get_pings()
#         for ping in all_pings:
#             if "main" in ping["type"]:
#                 loop = False
#             else:
#                 continue
#         time.sleep(2)
#     addons = all_pings[-1]["environment"]["addons"]["activeAddons"]
#     for name in addons:
#         if manifest_id not in name:
#             continue
#         else:
#             break
#     # Disable Experiment
#     selenium.execute_script(
#         """
#             const { AddonManager } = ChromeUtils.import(
#             "resource://gre/modules/AddonManager.jsm"
#             );

#             async function callit(add_on) {
#                 let addon = await AddonManager.getAddonByID(add_on);
#                 console.log(add_on)
#                 await addon.disable();
#             }
#             callit(arguments[0]);
#         """,
#         list(addon_ids.keys())[0],
#     )
#     # Loop to make sure it expires
#     loop = True
#     counter = 0
#     while loop and counter <= 30:
#         time.sleep(2)
#         counter = counter + 1
#         all_pings = pings.get_pings()
#         ping_amount = len(all_pings[-1]["environment"]["addons"]["activeAddons"])
#         count = 0
#         for ping in all_pings:
#             for specific_ping in ping["environment"]["addons"]["activeAddons"]:
#                 if f"{manifest_id}" not in specific_ping:
#                     count = count + 1
#                     continue
#             if count == ping_amount:
#                 loop = False
#                 break
#     if counter == 25:
#         raise TimeoutError("Pings may not have updated in time")


# @pytest.mark.reuse_profile
# @pytest.mark.nondestructive
# def test_experiment_remains_disabled_after_user_disables_it(
#     selenium: typing.Any, addon_ids: dict, pytestconfig: typing.Any, pings: typing.Any
# ):
#     """Disable experiment, restart Firefox to make sure it stays disabled."""
#     selenium.get("about:addons")

#     selenium.execute_script(
#         """
#             const { AddonManager } = ChromeUtils.import(
#             "resource://gre/modules/AddonManager.jsm"
#             );

#             async function callit(add_on) {
#                 let addon = await AddonManager.getAddonByID(add_on);
#                 console.log(add_on)
#                 await addon.disable();
#             }
#             callit(arguments[0]);
#         """,
#         list(addon_ids.keys())[0],
#     )
#     toolbar = ToolBar(selenium)
#     for item in toolbar.toolbar_items:
#         if list(addon_ids)[0] not in item._id:
#             continue
#         else:
#             raise AssertionError("Extension is Found")
#     selenium.quit()
#     # Start firefox again with new selenium driver
#     # Build new Firefox Instance with appropriate profile and binary
#     if pytestconfig.getoption("--run-update-test"):
#         profile = FirefoxProfile(f'{os.path.abspath("utilities/klaatu-profile")}')
#         options = Options()
#         options.add_argument("-profile")
#         options.add_argument(f'{os.path.abspath("utilities/klaatu-profile")}')
#         options.headless = True
#         binary = os.path.abspath("utilities/firefox-old-nightly/firefox/firefox-bin")
#         options.binary_location = binary
#     elif pytestconfig.getoption("--run-firefox-release"):
#         profile = FirefoxProfile(
#             f'{os.path.abspath("utilities/klaatu-profile-release-firefox")}'
#         )
#         options = Options()
#         options.add_argument("-profile")
#         options.add_argument(
#             f'{os.path.abspath("utilities/klaatu-profile-release-firefox")}'
#         )
#         options.headless = True
#         binary = os.path.abspath("utilities/firefox-release/firefox/firefox-bin")
#         options.binary_location = binary
#     else:
#         profile = FirefoxProfile(
#             f'{os.path.abspath("utilities/klaatu-profile-current-nightly")}'
#         )
#         options = Options()
#         options.add_argument("-profile")
#         options.add_argument(
#             f'{os.path.abspath("utilities/klaatu-profile-current-nightly")}'
#         )
#         options.headless = True
#         binary = "/usr/bin/firefox"
#         options.binary_location = binary

#     # Start Firefox and test
#     selenium = webdriver.Firefox(
#         firefox_profile=profile, options=options, firefox_binary=binary
#     )
#     selenium.get("about:addons")

#     # Make sure experiment is still not enabled
#     toolbar = ToolBar(selenium)
#     for item in toolbar.toolbar_items:
#         if list(addon_ids)[0] not in item._id:
#             continue
#         else:
#             raise AssertionError("Extension is Found")

#     # Check last telemetry ping
#     pings = pings.get_pings()
#     addons = pings[-1]["environment"]["addons"]["activeAddons"]
#     for item in addons:
#         if list(addon_ids)[0] in item:
#             assert True
#         else:
#             continue
#     selenium.quit()


# @pytest.mark.nondestructive
# async def test_experiment_sends_correct_telemetry(
#     selenium: typing.Any, addon_ids: dict, pings: typing.Any
# ):
#     """Make sure telemetry is sent and recieved properly."""
#     selenium.get("https://www.allizom.org")
#     pings = pings.get_pings()
#     # for count, item in enumerate(ping_server.pings["pings"])
#     addons = pings[-1]["environment"]["addons"]["activeAddons"]
#     print(pings)
#     for item in addons:
#         if list(addon_ids)[0] in item:
#             assert True
#         else:
#             continue


@pytest.mark.last
@pytest.mark.update_test
@pytest.mark.nondestructive
def test_experiment_does_not_stop_update(
    variables: dict, selenium: typing.Any, request: typing.Any
):
    """Experinemt should not block firefox updates."""
    if not request.config.getoption("--run-update-test"):
        pytest.skip("needs --run-update-test option to run")
        return
    selenium.get("about:profiles")
    # Sleep to let firefox update
    with selenium.context(selenium.CONTEXT_CHROME):
        WebDriverWait(selenium, 60).until(
            firefox_update_banner_is_found(),
            message="Update banner not found",
    )
        
        element = selenium.find_element(
            By.CSS_SELECTOR,
            "#appMenu-popup #appMenu-multiView #appMenu-protonMainView #appMenu-proton-update-banner"
        )
        element.click()
    selenium.quit()

    # Start firefox again with new selenium driver
    # Build new Firefox Instance
    options = Options()
    options.add_argument("-profile")
    options.add_argument(f'{Path("utilities/klaatu-profile").absolute()}')
    options.add_argument("-headless")
    binary = f"{Path('utilities/firefox-old-nightly/firefox/firefox-bin').absolute()}"
    options.binary_location = f"{binary}"

    # Start Firefox and test
    selenium = webdriver.Firefox(
        firefox_binary=binary, options=options
    )
    selenium.get("https://www.allizom.org")
    WebDriverWait(selenium, 10).until(
        firefox_update_banner_is_invisible(),
        message="Update banner found, maybe firefox didn't update?",
    )
    selenium.get("about:studies")
    print(selenium.page_source)
    WebDriverWait(selenium, 60).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".study-name")),
        message="Experiment not shown on about:studies.",
    )
    items = selenium.find_elements(By.CSS_SELECTOR, ".study-name")
    for item in items:
        if variables["userFacingName"] in item.text:
            assert (
                variables["userFacingDescription"]
                in selenium.find_element(By.CSS_SELECTOR, ".study-description").text
            )
    selenium.quit()
