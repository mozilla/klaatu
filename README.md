# Firefox Experiments validator - Klaatu

A tool used to validate firefox experiments

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

```--run-firefox-release```: Runs the suite with an unbranded release Firefox version.
```--private-browsing-enabled```: If your experiment runs within private browsing windows please include this option.
```--run-update-test```: Includes the update test in the test run using Firefox Nightly.
```--experiment```: Path to the experiment you want to test.

## Using the docker hub image

To use the docker hub image, you must mount your local dir as a volume in the container. I suggest mounting the volume like `-v {LOCAL-DIR}:/code/test_files`. Here is an example: ```docker run --rm --name "klaatu" -v $PWD/{PATH-TO-XPI-FOLDER}:/code/test_files mozilla/klaatu:latest tox -e exp-tests -- --experiment=test_files/{NAME-OF-FILE}.xpi --html=report.html```