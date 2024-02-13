# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from pytest_bdd import given, scenario, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


@scenario(
    "../features/generic_nimbus.feature",
    "The browser will enroll into the requested branch",
)
def test_experiment_enrolls_into_correct_branch():
    pass


@scenario(
    "../features/generic_nimbus.feature",
    "The experiment can unenroll from the about:studies page",
)
def test_experiment_unenrolls_via_about_studies_page():
    pass


@scenario(
    "../features/generic_nimbus.feature",
    "The experiment can be unenrolled via opting out from studies",
)
def test_experiment_unenrolls_via_opting_out_of_studies():
    pass


@given("Firefox is launched enrolled in an Experiment")
def selenium(selenium):
    return selenium


@then("The experiment branch should be correctly reported")
def check_branch_in_telemetry(check_ping_for_experiment, request, variables):
    experiment_branch = request.config.getoption("--experiment-branch")
    data = check_ping_for_experiment(f"optin-{variables['slug']}")
    assert experiment_branch in data["branch"]


@then("The Experiment is unenrolled via the about:studies page")
def unenroll_via_studies_page(selenium, variables):
    selenium.get("about:studies")
    WebDriverWait(selenium, 60).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".study-name")),
        message="Experiment not shown on about:studies.",
    )
    items = selenium.find_elements(By.CSS_SELECTOR, ".study-name")
    for item in items:
        if variables["userFacingName"] in item.text:
            selenium.find_element(By.CSS_SELECTOR, ".remove-button").click()


@then("the telemetry shows it as being unenrolled")
def check_telemetry_for_unenrollment(variables, telemetry_event_check):
    return telemetry_event_check(experiment=f"optin-{variables['slug']}", event="unenroll")


@then("The experiment can be unenrolled via opting out of studies")
def opt_out_via_about_preferences(selenium, variables):
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
