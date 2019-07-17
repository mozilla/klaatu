# Firefox Experiments validator - Klaatu

A tool used to validate firefox experiments

## Prerequisites

You should have docker installed.

## How to use

1. Clone repository
2. Create ```test_files``` and ```test_results``` directories.
3. Place experiments in ```test_files``` folder.
4. Build docker image with command ```docker build -t klaatu .``` in the projects root directory.
5. Run tests in docker with ```./utilities/run_all.sh```

The tests should run and move all passed experiments to a ```validated_experiments``` folder. There will be an HTML report posted in the ```test_results``` folder for each test, even if the experiment fails to pass a test. You can view this report in your browser.
