# Firefox Experiments validator - Klaatu

A tool used to validate firefox experiments

## Using the docker hub image

To use the docker hub image, you must mount your local dir as a volume in the container. I suggest mounting the volume like `-v {LOCAL-DIR}:/code/test_files`.

Here is an example: ```docker run --rm --name "klaatu" -v $PWD/{PATH-TO-XPI-FOLDER}:/code/test_files mozilla/klaatu:latest tox -e exp-tests -- --experiment=test_files/{NAME-OF-FILE}.xpi --html=report.html```

## Included tests
- ```test_experiment_does_not_stop_startup```: Experiment does not stop browser startup, or prohibit a clean exit.
- ```test_private_browsing_disables_experiment```: Experiment should be disabled in private browsing mode.
- ```test_experiment_does_not_drastically_slow_firefox```: Experiment should not slow firefox down by more then 20%.
- ```test_experiment_shows_on_support_page```: Experiment should show on about:support page.
- ```test_experiment_shows_on_studies_page```: Experiment should show on about:studies page.
- ```test_experiment_expires_correctly```: Experiment should not be included in the sent pings when it is disabled/expired.
- ```test_experiment_remains_disabled_after_user_disables_it```: Disable experiment, restart Firefox to make sure it stays disabled.
- ```test_experiment_sends_correct_telemetry```: Make sure telemetry is sent and recieved properly.
- ```test_experiment_does_not_stop_update```: Experiment should not block firefox updates.


## Prerequisites

You should have docker and git installed.

## How to use

1. Clone repository
2. Fill out this JSON file, name it `variables.json` and place it in the root directory:

```
    {
        "recipeId":
        "slug":
        "userFacingName":
        "userFacingDescription":
        "branch":
        "active": true,
        "addonId":
        "addonUrl": "https://example.com/{YOUR ADDON ID HERE}@mozilla.org-signed.xpi",
        "addonVersion":
        "extensionApiId":
        "extensionHash": "badhash",
        "hashAlgorithm": "sha256",
        "studyEndDate": null
    }
```
Add the path using the ```--variables``` option. ```--variables={PATH/TO/variables.json}```

3. Build docker image with command ```docker build -t klaatu .``` in the projects root directory.
4. Run tests with docker, example: ```docker run --rm --name="klaatu" klaatu tox -e exp-tests -- --experiment=fixtures/normandy-nextgen-study-example-a@mozilla.org-0.3-signed.xpi --variables={PATH/TO/variables.json} --private-browsing-enabled```

## CLI Options

- ```--run-release-firefox```: Runs the suite with an unbranded release Firefox version.
- ```--private-browsing-enabled```: If your experiment runs within private browsing windows please include this option.
- ```--run-update-test```: Includes the update test in the test run using Firefox Nightly.
- ```--experiment```: Path to the experiment you want to test.