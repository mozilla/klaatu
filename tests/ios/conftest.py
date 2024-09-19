# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests

sys.path.append("../../")

from .models.models import TelemetryModel  # noqa
from .xcodebuild import XCodeBuild  # noqa
from .xcrun import XCRun  # noqa

KLAATU_SERVER_URL = "http://localhost:1378"
KLAATU_LOCAL_SERVER_URL = "http://localhost:1378"

here = Path()


def pytest_addoption(parser):
    parser.addoption("--experiment", action="store", help="The experiments experimenter URL")
    parser.addoption("--stage", action="store_true", default=None, help="Use the stage server")
    parser.addoption(
        "--build-dev",
        action="store_true",
        default=False,
        help="Build the developer edition of Firefox",
    )
    parser.addoption(
        "--experiment-feature", action="store", help="Feature name you want to test against"
    )
    parser.addoption(
        "--experiment-branch",
        action="store",
        default="control",
        help="Experiment Branch you want to test on",
    )
    parser.addoption(
        "--experiment-server",
        action="store",
        default="prod",
        help="Experiment Server the experiment is hosted on",
    )


def pytest_runtest_setup(item):
    envnames = [mark.name for mark in item.iter_markers()]
    if envnames:
        if item.config.getoption("--experiment-feature") not in envnames:
            pytest.skip("test does not match feature name")


@pytest.fixture(name="nimbus_cli_args")
def fixture_nimbus_cli_args():
    return "FIREFOX_SKIP_INTRO FIREFOX_TEST DISABLE_ANIMATIONS 'GCDWEBSERVER_PORT:7777'"


@pytest.fixture(name="experiment_branch")
def fixture_experiment_branch(request):
    return request.config.getoption("--experiment-branch")


@pytest.fixture(name="experiment_server")
def fixture_experiment_server(request):
    return request.config.getoption("--experiment-server")


@pytest.fixture(name="load_branches")
def fixture_load_branches(experiment_url):
    branches = []

    if experiment_url:
        data = experiment_url
    else:
        try:
            data = requests.get(f"{KLAATU_SERVER_URL}/experiment").json()
        except ConnectionRefusedError:
            logging.warn("No URL or experiment slug provided, exiting.")
            exit()
        else:
            for item in reversed(data):
                data = item
                break
    experiment = requests.get(data).json()
    for item in experiment["branches"]:
        branches.append(item["slug"])
    return branches


@pytest.fixture()
def xcodebuild_log(request, tmp_path_factory):
    xcodebuild_log = tmp_path_factory.mktemp("logs") / "xcodebuild.log"
    logging.info(f"Logs stored at: {xcodebuild_log}")
    request.config._xcodebuild_log = xcodebuild_log
    yield xcodebuild_log


@pytest.fixture(scope="session", autouse=True)
def fixture_build_fennec(request):
    if not request.config.getoption("--build-dev"):
        return
    command = [
        "xcodebuild",
        "build-for-testing",
        "-project Client.xcodeproj",
        "-scheme Fennec",
        "-configuration Fennec",
        "-sdk iphonesimulator",
        "-destination 'platform=iOS Simulator,name=iPhone 15,OS=17.4'",
    ]
    try:
        logging.info("Building app")
        subprocess.check_output(
            " ".join(command),
            cwd=here.parents[2],
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            shell=True,
        )
    except subprocess.CalledProcessError:
        raise


@pytest.fixture()
def xcodebuild(xcodebuild_log):
    yield XCodeBuild(xcodebuild_log, scheme="Fennec", test_plan="ExperimentIntegrationTests")


@pytest.fixture(scope="session")
def xcrun():
    return XCRun()


@pytest.fixture(name="device_control", scope="module", autouse=True)
def fixture_device_control(xcrun):
    xcrun.erase()
    xcrun.boot()
    yield
    xcrun.erase()


@pytest.fixture(name="start_app")
def fixture_start_app(nimbus_cli_args, run_nimbus_cli_command):
    def runner():
        command = [
            "nimbus-cli",
            "--app firefox_ios",
            "--channel developer",
            f"open -- {nimbus_cli_args}",
        ]
        run_nimbus_cli_command(" ".join(command))

    return runner


@pytest.fixture(name="experiment_data")
def fixture_experiment_data(experiment_url):
    data = requests.get(experiment_url).json()
    logging.debug(f"JSON Data used for this test: {data}")
    return [data]


@pytest.fixture(name="experiment_url", scope="module")
def fixture_experiment_url(request, variables):
    url = None

    if slug := request.config.getoption("--experiment"):
        # Build URL from slug
        match request.config.getoption("--experiment-server"):
            case "prod":
                url = f"{variables['urls']['prod_server']}/api/v6/experiments/{slug}/"
            case "stage" | "stage/preview":
                url = f"{variables['urls']['stage_server']}/api/v6/experiments/{slug}/"
    else:
        try:
            data = requests.get(f"{KLAATU_SERVER_URL}/experiment").json()
        except requests.exceptions.ConnectionError:
            logging.error("No URL or experiment slug provided, exiting.")
            exit()
        else:
            for item in data:
                if isinstance(item, dict):
                    continue
                else:
                    url = item
    yield url
    return_data = {"url": url}
    try:
        requests.put(f"{KLAATU_SERVER_URL}/experiment", json=return_data)
    except requests.exceptions.ConnectionError:
        pass


@pytest.fixture(name="experiment_slug")
def fixture_experiment_slug(request):
    return request.config.getoption("--experiment")


@pytest.fixture(name="send_test_results", scope="session")
def fixture_send_test_results(xcrun):
    yield
    xcrun.shutdown()
    here = Path()

    with open(
        f"{here.parent / 'ExperimentIntegrationTests' / 'results' / 'index.html'}", "rb"
    ) as f:
        files = {"file": f}
        try:
            requests.post(f"{KLAATU_SERVER_URL}/test_results", files=files)
        except requests.exceptions.ConnectionError:
            pass


@pytest.fixture(name="set_env_variables", autouse=True)
def fixture_set_env_variables(experiment_data):
    """Set any env variables XCUITests might need"""
    os.environ["EXPERIMENT_NAME"] = experiment_data[0]["userFacingName"]


@pytest.fixture(name="check_ping_for_experiment")
def fixture_check_ping_for_experiment(experiment_slug, variables):
    def _check_ping_for_experiment(branch=None, experiment=experiment_slug, reason=None):
        model = TelemetryModel(branch=branch, experiment=experiment)

        timeout = time.time() + 60 * 5
        while time.time() < timeout:
            data = requests.get(f"{variables['urls']['telemetry_server']}/pings").json()
            events = []
            for item in data:
                event_items = item.get("events", [])
                for event in event_items:
                    if (
                        "category" in event
                        and "nimbus_events" in event["category"]
                        and "extra" in event
                        and "branch" in event["extra"]
                    ):
                        events.append(event)
            for event in events:
                event_name = event.get("name")
                if (reason == "enrollment" and event_name == "enrollment") or (
                    reason == "unenrollment" and event_name in ["unenrollment", "disqualification"]
                ):
                    telemetry_model = TelemetryModel(
                        branch=event["extra"]["branch"],
                        experiment=event["extra"]["experiment"],
                    )
                    if model == telemetry_model:
                        return True
            time.sleep(5)
        return False

    return _check_ping_for_experiment


@pytest.fixture(name="run_nimbus_cli_command")
def fixture_run_nimbus_cli_command():
    def _run_nimbus_cli_command(command):
        logging.info(f"Running command {command}")
        try:
            out = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            out = e.output
            logging.info(out)
            raise

    return _run_nimbus_cli_command


@pytest.fixture(name="setup_experiment")
def setup_experiment(
    experiment_slug, experiment_server, experiment_branch, run_nimbus_cli_command, nimbus_cli_args
):
    def _setup_experiment():
        logging.info(f"Testing experiment {experiment_slug}, BRANCH: {experiment_branch}")
        command = [
            "nimbus-cli",
            "--app firefox_ios",
            "--channel developer",
            f"enroll {experiment_server}/{experiment_slug}",
            f"--branch {experiment_branch}",
            f"--patch {Path() / 'patch.json'}",
            f"-- {nimbus_cli_args}",
        ]
        run_nimbus_cli_command(" ".join(command))

    return _setup_experiment
