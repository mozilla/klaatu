# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import time

from pytest_bdd import scenarios, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

scenarios("../features/generic_nimbus.feature")


@then("The experiment branch should be correctly reported")
def check_branch_in_telemetry(
    telemetry_event_check, experiment_json, request, experiment_slug
):
    experiment_branch = request.config.getoption("--experiment-branch")
    telemetry_event_check(f"optin-{experiment_slug}")
    assert experiment_branch in experiment_json["branch"]


@then("The Experiment is unenrolled via the about:studies page")
def unenroll_via_studies_page(selenium, experiment_json):
    study_name_locator = (By.CSS_SELECTOR, ".study-name")

    timeout = timeout = time.time() + 60
    while time.time() < timeout:
        selenium.get("about:studies")
        WebDriverWait(selenium, 30).until(
            EC.presence_of_element_located(study_name_locator)
        )
        items = selenium.find_elements(*study_name_locator)
        if any(
            item for item in items if experiment_json["userFacingName"] in item.text
        ):
            logging.info("Experiment unenrolled")
            return True
        time.sleep(2)


@then("the Experiment is shown as disabled on about:studies page")
def check_experiment_is_disabled_on_about_studies(selenium, experiment_json):
    selenium.get("about:studies")
    disabled_studies = selenium.find_elements(
        By.CSS_SELECTOR, "#app .inactive-study-list .study.nimbus.disabled"
    )
    if any(
        item
        for item in disabled_studies
        if experiment_json["slug"] in item.get_attribute("data-study-slug")
    ):
        return True


@then("The experiment can be unenrolled via opting out of studies")
def opt_out_via_about_preferences(selenium):
    selenium.get("about:preferences")
    WebDriverWait(selenium, 60).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "#preferences-body")),
        message="about:preferences page did not load.",
    )
    el = selenium.find_element(By.CSS_SELECTOR, "#category-privacy")
    el.click()
    WebDriverWait(selenium, 60).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "#browserPrivacyCategory")),
        message="about:preferences Privacy page did not load.",
    )
    check_box = selenium.find_element(By.CSS_SELECTOR, "#optOutStudiesEnabled")
    check_box.click()
