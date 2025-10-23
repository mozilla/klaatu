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
        choices=("prod", "stage", "stage/preview"),
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

    prod = f"https://experimenter.services.mozilla.com/api/v6/experiments/{experiment_slug}"
    stage = f"https://stage.experimenter.nonprod.webservices.mozgcp.net/api/v6/experiments/{experiment_slug}/"  # noqa: E501

    if experiment_json:
        with open(experiment_json) as f:
            return json.load(f)
    match slug_server:
        case "prod":
            url = prod
        case "stage":
            url = stage
        case "stage/preview":
            url = stage
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
    control = False
    timeout = time.time() + 60

    if experiment_branch == "":
        pytest.raises("The experiment branch must be declared")
    script = """
        const callback = arguments[arguments.length - 1];

        (async function (arguments) {
            try {
                const { ExperimentAPI } = ChromeUtils.importESModule(
                    "resource://nimbus/ExperimentAPI.sys.mjs"
                );
                const branchSlug = arguments[1];

                Services.fog.initializeFOG();

                await ExperimentAPI.ready();

                ExperimentAPI.manager.store._deleteForTests(arguments[1]);
                const recipe = arguments[0];
                let branch = recipe.branches.find(b => b.slug == "control");
                await ExperimentAPI.manager.forceEnroll(recipe, branch);

                callback(true);
            } catch (err) {
                callback({ success: false, error: err.message });
            }
        })(arguments);
    """

    try:
        with selenium.context(selenium.CONTEXT_CHROME):
            time.sleep(5)
            result = selenium.execute_async_script(script, experiment_json, experiment_branch)
            logging.info(f"Force Enrolling: {result}")
    except JavascriptException as e:
        if "slug" in str(e):
            raise (Exception("Experiment slug was not found in the experiment."))
    while not control:
        time.sleep(10)
        control = telemetry_event_check(f"optin-{experiment_slug}", "enrollment")
        if time.time() > timeout:
            raise AssertionError("Experiment enrollment was never seen in ping Data")
    logging.info("Experiment loaded successfully!")
    time.sleep(15)


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
    firefox_options.add_argument("-remote-allow-system-access")
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
    firefox_options.set_preference("remote.system-access-check.enabled", False)
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
            script = """
                const callback = arguments[0];

                (async function () {
                    try {
                        const { ExperimentAPI } = ChromeUtils.importESModule(
                            "resource://nimbus/ExperimentAPI.sys.mjs"
                        );
                        const { RemoteSettings } = ChromeUtils.importESModule(
                            "resource://services-settings/remote-settings.sys.mjs"
                        );

                        await RemoteSettings.pollChanges();
                        await ExperimentAPI.ready();
                        await ExperimentAPI._rsLoader.updateRecipes("test");

                        callback(true);
                    } catch (err) {
                        callback(false);
                    }
                })();
                """
            selenium.execute_async_script(script)
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
        nimbus_events = None
        script = f"return Glean.nimbusEvents.{event}.testGetValue('events')"

        try:
            with selenium.context(selenium.CONTEXT_CHROME):
                nimbus_events = selenium.execute_script(script)

            logging.info(f"nimbus events: {nimbus_events}")
            assert any(
                events["name"] == event and events["extra"]["experiment"] == experiment
                for events in nimbus_events
            )
            return True
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
            WebDriverWait(selenium, 60).until(EC.element_to_be_clickable(el))
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


@pytest.fixture(name="find_impression")
def fixture_find_impression(selenium, find_telemetry):
    def fixture_find_impression_runner(source: str, provider: str, tagged: bool) -> bool:
        control = True
        timeout = time.time() + 120
        script = "return Glean.serp.impression.testGetValue()"
        flush_fog_ops = """
            const callback = arguments[0];
                (async function () {
                    try {
                        await Services.fog.testFlushAllChildren();
                        callback(true);
                    } catch (err) {
                        callback(false);
                    }
                })();

            """
        clear_scalars = "Services.telemetry.clearScalars();"

        while control and time.time() < timeout:
            # flush pending FOG operations
            with selenium.context(selenium.CONTEXT_CHROME):
                selenium.execute_async_script(flush_fog_ops)

            time.sleep(30)
            with selenium.context(selenium.CONTEXT_CHROME):
                impressions = selenium.execute_script(script)

            logging.info(f"Impressions: {impressions}")
            match_found = any(
                isinstance(item, dict)
                and isinstance(item.get("extra"), dict)
                and item["extra"].get("provider") == provider
                and item["extra"].get("source") == source
                and item["extra"].get("tagged") == tagged
                for item in impressions
            )

            if match_found:
                # Clear scalars and exit
                try:
                    with selenium.context(selenium.CONTEXT_CHROME):
                        selenium.execute_script(clear_scalars)
                    logging.info("Cleared Impressions")
                except Exception as e:
                    logging.warning("Failed to clear scalars: %s", e)
                return True
        else:
            return False

    return fixture_find_impression_runner


@pytest.fixture(name="find_telemetry")
def fixture_find_telemetry(selenium):
    def _(ping, scalar=None, value=None, scalar_type="keyedScalars"):
        control = True
        timeout = time.time() + 60

        submit_ping_script = """
            const callback = arguments[0];
                (async function () {
                    try {
                        let telemetryController = ChromeUtils.importESModule(
                            "resource://gre/modules/TelemetryControllerParent.sys.mjs"
                        );
                        await telemetryController.TelemetryController.submitExternalPing(
                            "main", {reason: "testing"}
                        )

                        callback(true);
                    } catch (err) {
                        callback(false);
                    }
                })();
        """

        while control and time.time() < timeout:
            match scalar_type:
                case "keyedScalars":
                    script = """
                        return Services.telemetry.getSnapshotForKeyedScalars("main")
                    """
                    with selenium.context(selenium.CONTEXT_CHROME):
                        telemetry = selenium.execute_script(script)
                    try:
                        for item, val in telemetry["parent"].get(ping).items():
                            if scalar == item and value == val:
                                logging.info(f"Parent Pings {telemetry['parent']}\n")
                                return True
                    except (TypeError, AttributeError, KeyError):
                        logging.info(f"Parent Pings {telemetry.get('parent')}\n")

                case "scalars":
                    script = """
                            return Services.telemetry.getSnapshotForScalars("main")
                        """
                    with selenium.context(selenium.CONTEXT_CHROME):
                        telemetry = selenium.execute_script(script)
                    assert telemetry["parent"].get(ping) == value
                    logging.info(f"Parent Pings {telemetry['parent']}\n")
                    return True
                case _:
                    pytest.raises("Incorrect Scalar type")
            time.sleep(5)
            with selenium.context(selenium.CONTEXT_CHROME):
                telemetry = selenium.execute_script(submit_ping_script)
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
def fixture_setup_search_test(selenium, firefox):
    def _():
        test_data = """
        let SearchSERPTelemetry;

        try {
            SearchSERPTelemetry = ChromeUtils.importESModule(
                "moz-src:///browser/components/search/SearchSERPTelemetry.sys.mjs"
            ).SearchSERPTelemetry;
        } catch (e) {
            SearchSERPTelemetry = ChromeUtils.importESModule(
                "resource:///modules/SearchSERPTelemetry.sys.mjs"
            ).SearchSERPTelemetry;
        }
        SearchSERPTelemetryUtils = ChromeUtils.importESModule(
            "moz-src:///browser/components/search/SearchSERPTelemetry.sys.mjs"
        ).SearchSERPTelemetryUtils
        let testProvider = [
            {
                telemetryId: "klaatu",
                searchPageRegexp:
                /^https:\/\/localhost\/?/,
                queryParamNames: ["s"],
                codeParamName: "abc",
                taggedCodes: ["ff"],
                adServerAttributes: ["mozAttr"],
                nonAdsLinkRegexps: [],
                extraAdServersRegexps: [/^https:\/\/example\.com\/ad/],
                components: [
                    {
                        type: SearchSERPTelemetryUtils.COMPONENTS.AD_LINK,
                        default: true,
                    },
                ],
            },
        ];
        SearchSERPTelemetry.overrideSearchTelemetryForTests(testProvider);
        """

        search_engine = """
        const callback = arguments[0];
            (async function () {
                try {
                    installedEngines = await Services.search.getAppProvidedEngines();
                    userEngine = await Services.search.addUserEngine({
                        name: "Moz Search",
                        url: "https://localhost:8888/searchTelemetryAd.html?s={searchTerms}&abc=ff",
                        suggest_url: "https://localhost:8888/searchSuggestionEngine.sjs?query={searchTerms}",
                        alias: "mzsrch",
                    });
                    installedEngines.push(userEngine);
                    Services.search.setDefault(
                        Services.search.getEngineByName("Moz Search"),
                        Ci.nsISearchService.CHANGE_REASON_USER_SEARCHBAR
                        );
                    callback(true);
                } catch (err) {
                    callback(false);
                }
            })();
        """  # noqa
        with selenium.context(selenium.CONTEXT_CHROME):
            selenium.execute_script(test_data)
            selenium.execute_async_script(search_engine)

    return _


@pytest.fixture(name="enable_search_bar")
def fixture_enable_search_bar(selenium):
    def _enable_search_bar():
        script = """
        try {
            const { CustomizableUI } = ChromeUtils.importESModule(
                "resource:///modules/CustomizableUI.sys.mjs",
            );
        }
        catch (e) {
            const { CustomizableUI } = ChromeUtils.importESModule(
                "moz-src:///browser/components/customizableui/CustomizableUI.sys.mjs",
            );
        }

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
    setup_search_test()
    logging.info("Custom search enabled\n")
    script = """
        Services.fog.testResetFOG();
        Services.telemetry.clearScalars();
    """
    with selenium.context(selenium.CONTEXT_CHROME):
        selenium.execute_script(script)
    logging.info("Cleared Telemetry events\n")
    return selenium


@then("The browser opens a private window")
def open_private_browsing_window(selenium, firefox):
    browser = firefox.browser.open_window(private=True)
    assert browser.is_private
    logging.info("Opened Private window\n")
