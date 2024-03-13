# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import logging
import os
import shutil
import sys
import time
import typing
from pathlib import Path

import pytest
import requests
from pytest_bdd import given, then
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

PING_SERVER = "http://ping-server:5000"


def pytest_addoption(parser) -> None:
    parser.addoption(
        "--experiment-recipe",
        action="store",
        default=None,
        help="Recipe JSON for experiment",
    ),
    parser.addoption(
        "--experiment-branch",
        action="store",
        default=None,
        help="Experiment Branch to test",
    ),
    parser.addoption(
        "--run-update-test",
        action="store_true",
        default=None,
        help="Run older version of firefox",
    ),
    parser.addoption(
        "--private-browsing-enabled",
        action="store_true",
        default=None,
        help="Run private browsing test",
    )


@pytest.fixture(name="enroll_experiment", autouse=True)
def fixture_enroll_experiment(
    request: typing.Any,
    selenium: typing.Any,
    variables: dict,
    check_ping_for_experiment: object,
) -> typing.Any:
    """Fixture to enroll into an experiment"""
    experiment_branch = request.config.getoption("--experiment-branch")
    if experiment_branch == "":
        pytest.raises("The experiment branch must be declared")
    script = """
        const ExperimentManager = ChromeUtils.import(
            "resource://nimbus/lib/ExperimentManager.jsm"
        );
        const branchSlug = arguments[1];
        ExperimentManager.ExperimentManager.store._deleteForTests(arguments[1])
        const recipe = JSON.parse(arguments[0]);
        let branch = recipe.branches.find(b => b.slug == branchSlug);
        ExperimentManager.ExperimentManager.forceEnroll(recipe, branch);
    """

    with selenium.context(selenium.CONTEXT_CHROME):
        selenium.execute_script(script, json.dumps(variables), experiment_branch)
    assert (
        check_ping_for_experiment(f"optin-{variables['slug']}") is not None
    ), "Experiment not found in telemetry"


@pytest.fixture(name="experiment_slug")
def fixture_experiment_slug(variables: dict) -> typing.Any:
    return f"optin-{variables['slug']}"


@pytest.fixture
def setup_profile(pytestconfig: typing.Any, request: typing.Any) -> typing.Any:
    """Fixture to create a copy of the profile to use within the test."""
    if request.config.getoption("--run-update-test"):
        shutil.copytree(
            Path("utilities/klaatu-profile-old-base").absolute(),
            Path("utilities/klaatu-profile").absolute(),
            dirs_exist_ok=True,
            ignore_dangling_symlinks=True,
        )
        return f'{Path("utilities/klaatu-profile").absolute()}'
    if request.node.get_closest_marker("reuse_profile") and not request.config.getoption(
        "--run-update-test"
    ):
        shutil.copytree(
            Path("utilities/klaatu-profile-firefox-base").absolute(),
            Path("utilities/klaatu-profile-current-base").absolute(),
            dirs_exist_ok=True,
        )
        return f'{Path("utilities/klaatu-profile-current-base").absolute()}'


@pytest.fixture
def firefox_options(
    setup_profile: typing.Any,
    pytestconfig: typing.Any,
    firefox_options: typing.Any,
    request: typing.Any,
) -> typing.Any:
    """Setup Firefox"""
    firefox_options.log.level = "trace"
    if request.config.getoption("--run-update-test"):
        if request.node.get_closest_marker("update_test"):  # disable test needs different firefox
            binary = Path(
                "utilities/firefox-old-nightly-disable-test/firefox/firefox-bin"
            ).absolute()
            firefox_options.binary = f"{binary}"
            firefox_options.add_argument("-profile")
            firefox_options.add_argument(
                f'{Path("utilities/klaatu-profile-disable-test").absolute()}'
            )
        firefox_options.add_argument("-profile")
        firefox_options.add_argument(setup_profile)
    if request.node.get_closest_marker("reuse_profile") and not request.config.getoption(
        "--run-update-test"
    ):
        firefox_options.add_argument("-profile")
        firefox_options.add_argument(setup_profile)
    firefox_options.set_preference("extensions.install.requireBuiltInCerts", False)
    firefox_options.log.level = "trace"
    firefox_options.set_preference("browser.cache.disk.smart_size.enabled", False)
    firefox_options.set_preference("toolkit.telemetry.server", f"{PING_SERVER}")
    firefox_options.set_preference("telemetry.fog.test.localhost_port", -1)
    firefox_options.set_preference("toolkit.telemetry.initDelay", 1)
    firefox_options.set_preference("ui.popup.disable_autohide", True)
    firefox_options.set_preference("toolkit.telemetry.minSubsessionLength", 0)
    firefox_options.set_preference("datareporting.healthreport.uploadEnabled", True)
    firefox_options.set_preference("datareporting.policy.dataSubmissionEnabled", True)
    firefox_options.set_preference(
        "datareporting.policy.dataSubmissionPolicyBypassNotification", False
    )
    firefox_options.set_preference("sticky.targeting.test.pref", True)
    firefox_options.set_preference("toolkit.telemetry.log.level", "Trace")
    firefox_options.set_preference("toolkit.telemetry.log.dump", True)
    firefox_options.set_preference("toolkit.telemetry.send.overrideOfficialCheck", True)
    firefox_options.set_preference("toolkit.telemetry.testing.disableFuzzingDelay", True)
    firefox_options.set_preference("nimbus.debug", True)
    firefox_options.set_preference("app.normandy.run_interval_seconds", 30)
    firefox_options.set_preference(
        "security.content.signature.root_hash",
        "5E:36:F2:14:DE:82:3F:8B:29:96:89:23:5F:03:41:AC:AF:A0:75:AF:82:CB:4C:D4:30:7C:3D:B3:43:39:2A:FE",  # noqa: E501
    )
    firefox_options.set_preference("datareporting.healthreport.service.enabled", True)
    firefox_options.set_preference("datareporting.healthreport.logging.consoleEnabled", True)
    firefox_options.set_preference("datareporting.healthreport.service.firstRun", True)
    firefox_options.set_preference(
        "datareporting.healthreport.documentServerURI",
        "https://www.mozilla.org/legal/privacy/firefox.html#health-report",
    )
    firefox_options.set_preference(
        "app.normandy.api_url", "https://normandy.cdn.mozilla.net/api/v1"
    )
    firefox_options.set_preference("app.normandy.user_id", "7ef5ab6d-42d6-4c4e-877d-c3174438050a")
    firefox_options.set_preference("messaging-system.log", "debug")
    firefox_options.set_preference("toolkit.telemetry.scheduler.tickInterval", 15)
    firefox_options.set_preference("toolkit.telemetry.collectInterval", 10)
    firefox_options.set_preference("toolkit.telemetry.eventping.minimumFrequency", 3000)
    firefox_options.set_preference("toolkit.telemetry.unified", True)
    firefox_options.set_preference("toolkit.telemetry.eventping.maximumFrequency", 6000)
    firefox_options.set_preference("allowServerURLOverride", True)
    firefox_options.set_preference("browser.aboutConfig.showWarning", False)
    firefox_options.set_preference("browser.newtabpage.enabled", True)
    firefox_options.set_preference("privacy.query_stripping.enabled", False)
    yield firefox_options

    # Delete old pings
    requests.delete(f"{PING_SERVER}/pings")

    # Remove old profile
    if (
        request.node.get_closest_marker("reuse_profile")
        and not request.config.getoption("--run-update-test")
        or request.config.getoption("--run-update-test")
    ):
        shutil.rmtree(setup_profile)


@pytest.fixture
def firefox_startup_time(firefox: typing.Any) -> typing.Any:
    """Startup with no extension installed"""
    return firefox.selenium.execute_script(
        """
        perfData = window.performance.timing
        return perfData.loadEventEnd - perfData.navigationStart
        """
    )


@pytest.fixture
def selenium(selenium: typing.Any) -> typing.Any:
    """Setup Selenium"""
    return selenium


@pytest.fixture
def trigger_experiment_loader(selenium):
    def _trigger_experiment_loader():
        with selenium.context(selenium.CONTEXT_CHROME):
            selenium.execute_script(
                """
                    const { RemoteSettings } = ChromeUtils.import(
                        "resource://services-settings/remote-settings.js"
                    );
                    const { RemoteSettingsExperimentLoader } = ChromeUtils.import(
                        "resource://nimbus/lib/RemoteSettingsExperimentLoader.jsm"
                    );

                    RemoteSettings.pollChanges();
                    RemoteSettingsExperimentLoader.updateRecipes();
                """
            )
        time.sleep(5)

    return _trigger_experiment_loader


@pytest.fixture(name="check_ping_for_experiment")
def fixture_check_ping_for_experiment(trigger_experiment_loader):
    def _check_ping_for_experiment(experiment=None):
        control = True
        timeout = time.time() + 60 * 2
        while control and time.time() < timeout:
            data = requests.get(f"{PING_SERVER}/pings").json()
            try:
                experiments_data = [
                    item["environment"]["experiments"]
                    for item in data
                    if "experiments" in item["environment"]
                ]
            except KeyError:
                continue
            else:
                for item in experiments_data:
                    if experiment in item:
                        return item[experiment]
                time.sleep(5)
                trigger_experiment_loader()
        else:
            return False

    return _check_ping_for_experiment


@pytest.fixture(name="telemetry_event_check")
def fixture_telemetry_event_check(trigger_experiment_loader):
    def _telemetry_event_check(experiment=None, event=None):
        telemetry = requests.get(f"{PING_SERVER}/pings").json()
        events = [
            event["payload"]["events"]["parent"]
            for event in telemetry
            if "events" in event["payload"] and "parent" in event["payload"]["events"]
        ]

        try:
            for _event in events:
                for item in _event:
                    if (experiment and event) in item:
                        return True
            raise AssertionError
        except (AssertionError, TypeError):
            trigger_experiment_loader()
            return False

    return _telemetry_event_check


@pytest.fixture(name="cmd_or_ctrl_button")
def fixture_cmd_or_ctrl_button():
    return Keys.COMMAND if sys.platform == "darwin" else Keys.CONTROL


@pytest.fixture(name="navigate_using_url_bar")
def fixture_navigate_using_url_bar(selenium, cmd_or_ctrl_button):
    def _navigate_function(text=None, use_clipboard=False):
        if not text:
            text = "http://localhost:8000"
        with selenium.context(selenium.CONTEXT_CHROME):
            el = selenium.find_element(By.CSS_SELECTOR, "#urlbar-input")
            if use_clipboard:
                ActionChains(selenium).move_to_element(el).pause(1).click().pause(1).key_down(
                    cmd_or_ctrl_button
                ).send_keys("v").key_up(cmd_or_ctrl_button).send_keys(Keys.ENTER).perform()
                return
            else:
                el.click()
                el.send_keys(text)
                el.send_keys(Keys.ENTER)
        WebDriverWait(selenium, 60).until(
            EC.any_of(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".loaded")),
                EC.title_contains(text),
                EC.url_contains("localhost:8888"),  # MozSearch server
            )
        )

    return _navigate_function


@pytest.fixture(name="find_telemetry")
def fixture_find_telemetry(selenium):
    def _(ping, scalar=None, value=None, scalar_type="keyedScalars"):
        control = True
        timeout = time.time() + 60

        while control and time.time() < timeout:
            match scalar_type:
                case "keyedScalars":
                    script = """
                        return Services.telemetry.getSnapshotForKeyedScalars()
                    """
                    with selenium.context(selenium.CONTEXT_CHROME):
                        telemetry = selenium.execute_script(script)
                    try:
                        for item, val in telemetry["parent"].get(ping).items():
                            if scalar == item and value == val:
                                logging.info(f"Parent Pings {telemetry['parent']}\n")
                                return True
                    except (TypeError, AttributeError):
                        continue
                case "scalars":
                    script = """
                            return Services.telemetry.getSnapshotForScalars()
                        """
                    with selenium.context(selenium.CONTEXT_CHROME):
                        telemetry = selenium.execute_script(script)
                    assert telemetry["parent"].get(ping) == value
                    logging.info(f"Parent Pings {telemetry['parent']}\n")
                    return True
                case _:
                    pytest.raises("Incorrect Scalar type")
            time.sleep(1)
        else:
            return False

    return _


@pytest.fixture(name="search_server", autouse=True, scope="session")
def fixture_search_server():
    from subprocess import PIPE, Popen

    os.chdir("search_files")
    process = Popen(
        ["python", "search_server.py"], stdout=PIPE, encoding="utf-8", universal_newlines=True
    )
    os.chdir("..")

    yield "https://localhost:8888"

    os.chdir("search_files")
    process.terminate()


@pytest.fixture(name="setup_search_test")
def fixture_setup_search_test(selenium):
    def _():
        test_data = """
        const lazy = {};
        ChromeUtils.defineESModuleGetters(lazy, {
            SearchSERPTelemetry: "resource:///modules/SearchSERPTelemetry.sys.mjs",
        });
        let testProvider = [
            {
                telemetryId: "klaatu",
                searchPageRegexp:
                /^https:\/\/localhost\/?/,
                queryParamNames: ["s"],
                codeParamName: "abc",
                taggedCodes: ["ff"],
                followOnParamNames: ["a"],
                extraAdServersRegexps: [/^https:\/\/example\.com\/ad2?/],
            },
        ];
        lazy.SearchSERPTelemetry.overrideSearchTelemetryForTests(testProvider);
        """
        with selenium.context(selenium.CONTEXT_CHROME):
            selenium.execute_script(test_data)

    return _


@then("Firefox should be allowed to open a new tab")
def open_a_new_tab(selenium):
    with selenium.context(selenium.CONTEXT_CHROME):
        el = selenium.find_element(By.CSS_SELECTOR, "#tabs-newtab-button")
        el.click()


@then("The tab should open successfully")
def check_new_tab(selenium):
    # get the last tab
    WebDriverWait(selenium, 60).until(EC.number_of_windows_to_be(3))
    selenium.switch_to.window(selenium.window_handles[-1])
    WebDriverWait(selenium, 60).until(EC.url_contains("newtab"))
    assert "about:newtab" in selenium.current_url


@given(
    "Firefox is launched enrolled in an Experiment with custom search", target_fixture="selenium"
)
def setup_browser(selenium, setup_search_test):
    selenium.implicitly_wait(5)
    path = os.path.abspath("tests/fixtures/search_addon")
    selenium.install_addon(path, temporary=True)
    with selenium.context(selenium.CONTEXT_CHROME):
        root = selenium.find_element(By.CSS_SELECTOR, "#addon-webext-defaultsearch-notification")
        root.find_element(By.CSS_SELECTOR, ".popup-notification-primary-button").click()
    setup_search_test()
    logging.info("Custom search enabled\n")
    return selenium
