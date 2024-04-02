# Firefox Experiments validator - Klaatu

A tool used to validate firefox experiments

## Using the docker hub image

To use the docker hub image, you must mount your local dir as a volume in the container. I suggest mounting the volume like `-v {LOCAL-DIR}:/code/test_files`.

Here is an example: `docker compose run klaatu tox -e bdd-tests -- --experiment-branch control --variables tests/fixtures/test_experiment.json --private-browsing-enabled`. By default this will build and run the tests on Firefox Release.

There are 3 versions of Klaatu that have each major Firefox type. 
1. `mozilla/klaatu:firefox-release` : Firefox Release
2. `mozilla/klaatu:firefox-beta`: Firefox Beta
3. `mozilla/klaatu:firefox-nightly`: Firefox Nightly

## Prerequisites

You should have docker and git installed.

## Building locally

1. Clone repository
2. Copy the JSON of your experiment, into a file named `experiment.json`. The JSON can be found in 2 ways. On production:
```
https://experimenter.services.mozilla.com/api/v6/experiments/{EXPERIMENT-SLUG-HERE}
```
Or Stage:
```
https://stage.experimenter.nonprod.dataops.mozgcp.net/api/v6/experiments/{EXPERIMENT-SLUG-HERE}
```
Place this file in the somewhere within the working directory.

3. Add the path using the `--variables` option. Ex: `--variables={PATH/TO/experiment.json}`
4. Add the branch you want to test with the `--experiment-branch` option. Ex: `--experiment-branch control`

5. Build docker image with command `FIREFOX_VERSION="-nightly" docker compose -f docker-compose.yml up -d --build` in the projects root directory. The `FIREFOX_VERSION` env variable can either be `-nightly` or `-beta`. Leave it blank to build for release: `FIREFOX_VERSION=""`.
6. Run tests with docker, example: `docker compose run klaatu tox -e bdd-tests -- --experiment-branch={BRANCH YOU WANT TO TEST} --variables={PATH/TO/variables.json}`

## Running on Windows

The file `docker-compose-windows.yml` contains a windows docker image. This setup is much more involved but I've provided some scripts to help with this.

1. The method of interacting with the docker image is through RDP. I suggest using [XDRP](https://github.com/neutrinolabs/xrdp) for this. If you're on windows but using WSL, you can use the build in RDP client.
2. Run the docker image `docker compose -f docker-compose-windows.yml up`. This will take some time to finish as it has to download the windows image. You can view this process via `novnc` in the browser at `localhost:8006`
3. Close the VNC window after the windows desktop is shown and connect via RDP using the following address: `localhost:3389`. The user is `docker` and there is no password.
4. Open a powershell terminal and execute the following:
```sh
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```
5. Install git:
```sh
choco install git
```
6. Right click on the desktop and make a folder named `klaatu`.
7. Open the `klaatu` folder and right click, select `More Options` and then `Open git bash here`.
8. Clone the klaatu repo: 
```sh
git clone https://github.com/mozilla/klaatu.git
```
9. Run the `setup_script.sh`: 
```sh
./setup_script.sh
```

You should now be able to run the tests in the git bash shell: `tox -e bdd-tests -- --experiment-branch control --variables tests/fixtures/test_experiment.json`


## CLI Options

- `--private-browsing-enabled`: If your experiment runs within private browsing windows please include this option.
- `--run-update-test`: Includes the update test in the test run using Firefox Nightly.
- `--experiment-branch`: Experiment branch you want to test.