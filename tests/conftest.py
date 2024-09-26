# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import logging
import os
import shutil
import subprocess
import sys
import time
import typing
from pathlib import Path

import pytest
import requests
from pytest_bdd import given, then
from pytest_metadata.plugin import metadata_key
from selenium.common.exceptions import JavascriptException
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


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
    ),
    parser.addoption(
        "--experiment-slug",
        action="store",
        default=None,
        help="Experiment slug from Experimenter",
    ),
    parser.addoption(
        "--experiment-server",
        action="store",
        default="prod",
        choices=("prod", "stage"),
        help="The server where the experiment is located, either stage or prod",
    ),
    parser.addoption(
        "--experiment-json",
        action="store",
        default=None,
        help="The experiments JSON file.",
    ),
    parser.addoption(
        "--firefox-path",
        action="store",
        default=None,
        help="The path to the Firefox you want to use",
    )


def start_process(path, command):
    module_path = Path(path)

    try:
        process = subprocess.Popen(
            command,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            cwd=module_path.absolute(),
        )
        stdout, stderr = process.communicate(timeout=5)

        if process.returncode != 0:
            raise Exception(stderr)
    except subprocess.TimeoutExpired:
        logging.info(f"{module_path.name} server started")
        return process


@pytest.fixture(name="experiment_json", scope="session")
def fixture_experiment_json(request):
    experiment_slug = request.config.getoption("--experiment-slug")
    slug_server = request.config.getoption("--experiment-server")
    experiment_json = request.config.getoption("--experiment-json")

    if experiment_json:
        with open(experiment_json) as f:
            return json.load(f)
    match slug_server:
        case "prod":
            url = f"https://experimenter.services.mozilla.com/api/v6/experiments/{experiment_slug}/"  # noqa: E501
        case "stage":
            url = f"https://stage.experimenter.nonprod.dataops.mozgcp.net/api/v6/experiments/{experiment_slug}/"  # noqa: E501
    return requests.get(url).json()


@pytest.fixture(name="enroll_experiment", autouse=True)
def fixture_enroll_experiment(
    request: typing.Any,
    selenium: typing.Any,
    telemetry_event_check: object,
    experiment_json: object,
    experiment_slug: str,
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

    try:
        with selenium.context(selenium.CONTEXT_CHROME):
            selenium.execute_script(script, json.dumps(experiment_json), experiment_branch)
    except JavascriptException as e:
        if "slug" in str(e):
            raise (Exception("Experiment slug was not found in the experiment."))
    else:
        assert telemetry_event_check(
            f"optin-{experiment_slug}", event="enroll"
        ), "Experiment not found in telemetry"
        logging.info("Experiment loaded successfully!")


@pytest.fixture(name="experiment_slug", scope="session", autouse=True)
def fixture_experiment_slug(request) -> typing.Any:
    slug = request.config.getoption("--experiment-slug")
    os.environ["EXPERIMENT_SLUG"] = slug
    return slug


@pytest.fixture(name="experiment_branch", scope="session", autouse=True)
def fixture_experiment_branch(request):
    branch = request.config.getoption("--experiment-branch")
    os.environ["EXPERIMENT_BRANCH"] = branch
    return branch


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
    ping_server,
) -> typing.Any:
    """Setup Firefox"""
    if firefox_path := request.config.getoption("--firefox-path"):
        firefox_options.binary = firefox_path
        logging.info(f"Using firefox at {firefox_path}")
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
    firefox_options.set_preference("toolkit.telemetry.server", f"{ping_server}")
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
    requests.delete(f"{ping_server}/pings")

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
def fixture_check_ping_for_experiment(trigger_experiment_loader, ping_server):
    def _check_ping_for_experiment(experiment=None):
        control = True
        timeout = time.time() + 60
        while control and time.time() < timeout:
            data = requests.get(f"{ping_server}/pings").json()
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
def fixture_telemetry_event_check(trigger_experiment_loader, selenium):
    def _telemetry_event_check(experiment=None, event=None):
        fetch_events = """
            return Services.telemetry.snapshotEvents(Ci.nsITelemetry.DATASET_ALL_CHANNELS);
        """

        with selenium.context(selenium.CONTEXT_CHROME):
            telemetry = selenium.execute_script(fetch_events)
            logging.info(f"Event pings: {telemetry}\n")
            control = True
            timeout = time.time() + 30

            while control and time.time() < timeout:
                for item in telemetry.get("parent"):
                    if (experiment and event) in item:
                        return True
                else:
                    trigger_experiment_loader()
                    continue
            else:
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
                EC.url_contains("localhost"),  # test website server
                EC.url_contains("static-server"),  # MozSearch server
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
            logging.info("Ping was not found\n")
            return False

    return _


@pytest.fixture(name="search_server", autouse=True, scope="session")
def fixture_search_server():
    process = start_process("search_files", ["python", "search_server.py"])
    yield "https://localhost:8888"
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


@pytest.fixture(name="enable_search_bar")
def fixture_enable_search_bar(selenium):
    def _enable_search_bar():
        script = """
        const { CustomizableUI } = ChromeUtils.importESModule(
            "resource:///modules/CustomizableUI.sys.mjs",
        );

        CustomizableUI.addWidgetToArea(
            "search-container",
            CustomizableUI.AREA_NAVBAR,
            CustomizableUI.getPlacementOfWidget("urlbar-container").position + 1
        );
        """
        with selenium.context(selenium.CONTEXT_CHROME):
            selenium.execute_script(script)

    return _enable_search_bar


@pytest.fixture(name="static_server", autouse=True, scope="session")
def fixture_static_server():
    if os.environ.get("DEBIAN_FRONTEND") and not os.environ.get("CI"):
        yield "http://static-server:8000"
    else:
        process = start_process(
            "tests/fixtures", ["python", "-m", "http.server", "-d", "./", "8000"]
        )
        yield "http://localhost:8000"
        process.terminate()


@pytest.fixture(name="ping_server", autouse=True, scope="session")
def fixture_ping_server():
    if os.environ.get("DEBIAN_FRONTEND") and not os.environ.get("CI"):
        yield "http://ping-server:5000"
    else:
        process = start_process("ping_server", ["python", "ping_server.py"])
        yield "http://localhost:5000"
        process.terminate()


@pytest.fixture(name="firefox_version", autouse=True)
def fixture_firefox_version(selenium):
    script = """return navigator.userAgent"""
    version = selenium.execute_script(script)
    version = [item for item in version.split() if "Firefox" in item][0]
    logging.info(f"Firefox version {version}")
    os.environ["FIREFOX_VERSION"] = version.split("/")[-1]
    return version


@pytest.hookimpl(tryfirst=True)
def pytest_sessionfinish(session, exitstatus):
    # Add data to html report
    session.config.stash[metadata_key]["Experiment Slug"] = os.environ.get(
        "EXPERIMENT_SLUG", "N/A"
    )
    session.config.stash[metadata_key]["Experiment Branch"] = os.environ.get(
        "EXPERIMENT_BRANCH", "N/A"
    )
    session.config.stash[metadata_key]["Firefox Version"] = os.environ.get(
        "FIREFOX_VERSION", "N/A"
    )


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


@then("The browser opens a private window")
def open_private_browsing_window(selenium, firefox):
    browser = firefox.browser.open_window(private=True)
    assert browser.is_private
    logging.info("Opened Private window\n")
