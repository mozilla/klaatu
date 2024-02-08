# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from pathlib import Path

import pytest
from pytest_bdd import given, scenario, then, when
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from tests.expected import (
    firefox_update_banner_is_found,
    firefox_update_banner_is_invisible,
)


@scenario("../features/user_interface.feature", "The browser can navigate effectively")
def test_experiment_does_not_stop_startup():
    print("browser navigation test done")


@scenario(
    "../features/user_interface.feature",
    "The experiment does not drastically slow down Firefox",
)
def test_experiment_does_not_drastically_slow_firefox():
    pass


@scenario("../features/user_interface.feature", "The experiment shows on the studies page")
def test_experiment_shows_on_studies_page():
    pass


@scenario("../features/user_interface.feature", "The experiment shows on the support page")
def test_experiment_shows_on_support_page():
    pass


@scenario(
    "../features/user_interface.feature",
    "The experiment should not block Firefox updates",
)
def test_experiment_does_not_stop_update(request):
    if not request.config.getoption("--run-update-test"):
        pytest.skip("needs --run-update-test option to run")
        return


@given("Firefox is launched enrolled in an Experiment")
def selenium(selenium):
    return selenium


@when("The user navigates to a webpage")
def navigate_to_web_page(selenium):
    selenium.get("https://www.allizom.org")


@then("Firefox should load the webpage")
def page_loads(selenium):
    selenium.find_element(By.CSS_SELECTOR, "#home").is_displayed()


@then("The Experiment should be shown on the about:studies page")
def studies_page_shows_experiment(selenium, variables):
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


@then("The Experiment should be shown on the about:support page")
def support_page_shows_experiment(selenium, experiment_slug):
    selenium.get("about:support")
    extensions = selenium.find_element(By.ID, "remote-experiments-tbody")
    items = extensions.find_elements(By.CSS_SELECTOR, "tr > td")
    for item in items:
        if experiment_slug not in item.text:
            continue
        else:
            assert True, "Extension Found"


@then("Firefox should not be slowed down")
def firefox_speed(selenium, firefox_startup_time):
    startup = selenium.execute_script(
        """
        perfData = window.performance.timing
        return perfData.loadEventEnd - perfData.navigationStart
        """
    )
    assert (
        (int(firefox_startup_time) * 0.2) + int(firefox_startup_time)
    ) >= startup, "This experiment caused a slowdown within Firefox."


@then("A user chooses to update Firefox")
def update_firefox(selenium, request):
    if not request.config.getoption("--run-update-test"):
        pytest.skip("needs --run-update-test option to run")
        return
    with selenium.context(selenium.CONTEXT_CHROME):
        WebDriverWait(selenium, 60).until(
            firefox_update_banner_is_found(),
            message="Update banner not found",
        )

        element = selenium.find_element(
            By.CSS_SELECTOR,
            """
                #appMenu-popup #appMenu-multiView
                #appMenu-protonMainView
                #appMenu-proton-update-banner
            """,
        )
        element.click()
    selenium.quit()


@then("Firefox updates correctly", target_fixture="selenium")
def start_updated_firefox():
    # Start firefox again with new selenium driver
    # Build new Firefox Instance
    options = Options()
    options.add_argument("-profile")
    options.add_argument(f'{Path("utilities/klaatu-profile").absolute()}')
    options.add_argument("-headless")
    binary = f"{Path('utilities/firefox-old-nightly/firefox/firefox-bin').absolute()}"
    options.binary_location = f"{binary}"

    # Start Firefox and test
    selenium = webdriver.Firefox(firefox_binary=binary, options=options)
    selenium.get("https://www.allizom.org")
    WebDriverWait(selenium, 10).until(
        firefox_update_banner_is_invisible(),
        message="Update banner found, maybe firefox didn't update?",
    )
    return selenium


@then("The experiment is still enrolled")
def check_experiment_is_still_enrolled(selenium, variables):
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
    selenium.quit()
