# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import os
import random
import subprocess
import time
from pathlib import Path

import pytest
import requests
from pytest_metadata.plugin import metadata_key

from .gradlewbuild import GradlewBuild
from .models.models import TelemetryModel

here = Path()


def pytest_addoption(parser):
    parser.addoption(
        "--experiment-feature",
        action="store",
        help="Feature name you want to test against",
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
        "--experiment-slug",
        action="store",
        default=None,
        help="Experiment slug from Experimenter",
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
        logging.info(f"{module_path.name} started")
        return process


@pytest.fixture(name="nimbus_cli_args")
def fixture_nimbus_cli_args():
    return ""


@pytest.fixture(name="experiment_branch", scope="session", autouse=True)
def fixture_experiment_branch(request):
    branch = request.config.getoption("--experiment-branch")
    os.environ["EXPERIMENT_BRANCH"] = branch
    return branch


@pytest.fixture(name="experiment_slug", scope="session", autouse=True)
def fixture_experiment_slug(request, experiment_server):
    slug = request.config.getoption("--experiment-slug")
    if experiment_server != "prod":
        slug = f"{experiment_server}/{slug}"
    os.environ["EXPERIMENT_SLUG"] = slug
    return slug


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


@pytest.fixture(name="check_ping_for_experiment")
def fixture_check_ping_for_experiment(experiment_slug, variables):
    def _check_ping_for_experiment(
        branch=None, experiment=experiment_slug, reason=None
    ):
        model = TelemetryModel(branch=branch, experiment=experiment)

        timeout = time.time() + 60 * 5
        while time.time() < timeout:
            data = requests.get(
                f"{variables['urls']['telemetry_server']}/pings", timeout=10
            ).json()
            events = []
            for item in data:
                event_items = item.get("events")
                if event_items:
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
                    reason == "unenrollment"
                    and event_name in ["unenrollment", "disqualification"]
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


@pytest.fixture(name="open_app")
def fixture_open_app(run_nimbus_cli_command):
    def _():
        command = "nimbus-cli --app fenix --channel developer open"
        run_nimbus_cli_command(command)
        time.sleep(10)

    return _


@pytest.fixture(name="run_nimbus_cli_command")
def fixture_run_nimbus_cli_command(gradlewbuild_log):
    def _run_nimbus_cli_command(command):
        logging.info(f"Running command {command}")
        try:
            out = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            out = e.output
            logging.info(out)
            raise
        finally:
            with open(gradlewbuild_log, "w") as f:
                f.write(f"{out}")

    return _run_nimbus_cli_command


@pytest.fixture(name="experiment_data", scope="session")
def fixture_experiment_data(experiment_url, request):
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


@pytest.fixture(name="set_experiment_test_name", autouse=True)
def fixture_set_experiment_test_name(experiment_data):
    # Get a random word from the experiments userFacingName attribute.
    exp_name = experiment_data[0]["userFacingName"].split()
    os.environ["EXP_NAME"] = exp_name[random.randint(0, len(exp_name) - 1)]


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


@pytest.fixture
def gradlewbuild_log(pytestconfig, tmpdir):
    gradlewbuild_log = f"{tmpdir.join('gradlewbuild.log')}"
    pytestconfig._gradlewbuild_log = gradlewbuild_log
    yield gradlewbuild_log


@pytest.fixture
def gradlewbuild(gradlewbuild_log):
    yield GradlewBuild(gradlewbuild_log)


@pytest.fixture(name="ping_server", autouse=True, scope="session")
def fixture_ping_server():
    path = next(iter(here.glob("**/ping_server")))
    process = start_process(path, ["python", "ping_server.py"])
    yield "http://localhost:5000"
    process.terminate()


@pytest.fixture(name="delete_telemetry_pings")
def fixture_delete_telemetry_pings(ping_server):
    def runner():
        requests.delete(f"{ping_server}/pings", timeout=10)

    return runner


@pytest.fixture(name="dismiss_system_dialogs", autouse=True)
def fixture_dismiss_system_dialogs():
    """Dismiss any system dialogs before each test to prevent Espresso failures."""
    logging.info("Dismissing system dialogs")
    try:
        subprocess.run(
            [
                "adb",
                "shell",
                "am",
                "broadcast",
                "-a",
                "android.intent.action.CLOSE_SYSTEM_DIALOGS",
            ],
            timeout=5,
            capture_output=True,
        )
    except Exception as e:
        logging.warning(f"Failed to dismiss system dialogs: {e}")
    yield


@pytest.fixture(name="setup_experiment")
def fixture_setup_experiment(
    run_nimbus_cli_command, experiment_slug, experiment_branch
):
    def setup_experiment():
        logging.info("====== Beginning Test ======")
        command = [
            "nimbus-cli",
            "--app",
            "fenix",
            "--channel",
            "developer",
            "enroll",
            f"{experiment_slug}",
            "--branch",
            f"{experiment_branch}",
            "--reset-app",
        ]
        run_nimbus_cli_command(" ".join(command))
        time.sleep(
            10
        )  # Wait a while as there's no real way to know when the app has started

    return setup_experiment
