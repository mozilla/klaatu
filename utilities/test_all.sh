#!/bin/bash
# Runs docker builds for every file within the test_files directory.

mkdir validated_experiments

for file in ./test_files/*
do
  docker rm klaatu
  file_name=$(basename ${file%.*})

  docker run -v "$PWD"/test_files:/code/test_files --name "klaatu" klaatu tox -e py37-exp-tests -- --experiment="$file" --html=test_results/${file_name}-current-firefox.html
  docker cp klaatu:/code/test_results/${file_name}-current-firefox.html test_results/${file_name}-current-firefox.html
  docker rm klaatu
  current_nightly_result=$?
  
  docker run -v "$PWD"/test_files:/code/test_files --name "klaatu" klaatu tox -e py37-exp-tests -- --experiment="$file" --html=test_results/${file_name}-old-firefox.html --run-old-firefox
  docker cp klaatu:/code/test_results/${file_name}-old-firefox.html test_results/${file_name}-old-firefox.html
  docker rm klaatu

  if [ "$current_nightly_result" == "0" ] && [ $? == "0" ]
  then 
    mv $file validated_experiments
  fi

done