#!/bin/bash

ls
cd klaatu
adb install app-fenix-debug-androidTest.apk
adb install app-fenix-x86_64-debug.apk
cp -f tests/android/conftest.py ../firefox/mobile/android/fenix/app/src/androidTest/java/org/mozilla/fenix/experimentintegration
cp -f tests/android/generate_smoke_tests.py ../firefox/mobile/android/fenix/app/src/androidTest/java/org/mozilla/fenix/experimentintegration
cp -f tests/android/variables.yaml ../firefox/mobile/android/fenix/app/src/androidTest/java/org/mozilla/fenix/experimentintegration
cd ../firefox/mobile/android/fenix/app/src/androidTest/java/org/mozilla/fenix/experimentintegration
pip3 install virtualenv poetry pipenv
pipenv install
pipenv install pytest-rerunfailures
pipenv run python generate_smoke_tests.py
echo "TEST COMMAND: pipenv run pytest --experiment-slug $SLUG --experiment-branch $BRANCH --experiment-server $EXPERIMENT_SERVER --experiment-feature $FEATURE_NAME --firefox-version $FIREFOX_VERSION $EXTRA_ARGUMENTS --reruns 1"
pipenv run pytest --self-contained-html --experiment-slug "$SLUG" --experiment-branch "$BRANCH" --experiment-server "$EXPERIMENT_SERVER" --firefox-version "$FIREFOX_VERSION" --experiment-feature $FEATURE_NAME $EXTRA_ARGUMENTS --reruns 2 --maxfail=5 -rs tests/ || true
