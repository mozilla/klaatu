# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import os
import subprocess
import time
from pathlib import Path

import pytest
import requests
from pytest_metadata.plugin import metadata_key

from .models.models import TelemetryModel
from .xcodebuild import XCodeBuild
from .xcrun import XCRun

here = Path()


def pytest_addoption(parser):
    parser.addoption("--experiment-slug", action="store", help="The experiments experimenter URL")
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
    parser.addoption(
        "--firefox-version",
        action="store",
        default=None,
        help="The Firefox Version you are testing on. This is just use for reporting",
    )


def pytest_runtest_setup(item):
    envnames = [mark.name for mark in item.iter_markers()]
    if envnames:
        if item.config.getoption("--experiment-feature") not in envnames:
            pytest.skip("test does not match feature name")


@pytest.fixture(name="nimbus_cli_args")
def fixture_nimbus_cli_args():
    return "FIREFOX_SKIP_INTRO FIREFOX_TEST DISABLE_ANIMATIONS 'GCDWEBSERVER_PORT:7777'"


@pytest.fixture(name="experiment_slug", scope="session", autouse=True)
def fixture_experiment_slug(request, experiment_server):
    slug = request.config.getoption("--experiment-slug")
    if experiment_server != "prod":
        slug = f"{experiment_server}/{slug}"
    os.environ["EXPERIMENT_SLUG"] = slug
    return slug


@pytest.fixture(name="experiment_branch", scope="session", autouse=True)
def fixture_experiment_branch(request):
    branch = request.config.getoption("--experiment-branch")
    os.environ["EXPERIMENT_BRANCH"] = branch
    return branch


@pytest.fixture(name="firefox_version", scope="session", autouse=True)
def fixture_firefox_version(request):
    ff_version = request.config.getoption("--firefox-version")
    os.environ["FIREFOX_VERSION"] = ff_version
    return ff_version


@pytest.fixture(name="experiment_server", scope="session", autouse=True)
def fixture_experiment_server(request):
    return request.config.getoption("--experiment-server")


@pytest.fixture(name="experiment_feature")
def fixture_experiment_feature(request):
    return request.config.getoption("--experiment-feature")


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

    device_udid = os.environ.get("SIMULATOR_UDID", "booted")

    # Disable slow animations
    subprocess.run(
        [
            "xcrun",
            "simctl",
            "spawn",
            device_udid,
            "defaults",
            "write",
            "com.apple.springboard",
            "FBLazyLoadingDelay",
            "0",
        ],
        check=False,
        capture_output=True,
    )

    # Speed up UIView animations
    subprocess.run(
        [
            "xcrun",
            "simctl",
            "spawn",
            device_udid,
            "defaults",
            "write",
            "NSGlobalDomain",
            "UIViewAnimationDurationMultiplier",
            "0.1",
        ],
        check=False,
        capture_output=True,
    )

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


@pytest.fixture(name="experiment_data", scope="session")
def fixture_experiment_data(experiment_url):
    data = requests.get(experiment_url, timeout=30).json()
    logging.debug(f"JSON Data used for this test: {data}")
    return [data]


@pytest.fixture(name="experiment_url", scope="session")
def fixture_experiment_url(request, variables, experiment_slug, experiment_server):
    url = None

    if slug := experiment_slug:
        # Build URL from slug
        match request.config.getoption("--experiment-server"):
            case "prod":
                url = f"{variables['urls']['prod_server']}/api/v6/experiments/{slug.removeprefix(f'{experiment_server}/')}/"  # noqa
            case "stage" | "stage/preview":
                url = f"{variables['urls']['stage_server']}/api/v6/experiments/{slug.removeprefix(f'{experiment_server}/')}/"  # noqa
    yield url
    return_data = {"url": url}
    return return_data


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
            data = requests.get(
                f"{variables['urls']['telemetry_server']}/pings", timeout=10
            ).json()
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
            f"enroll {experiment_slug}",
            f"--branch {experiment_branch}",
            f"-- {nimbus_cli_args}",
        ]
        run_nimbus_cli_command(" ".join(command))

    return _setup_experiment


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
