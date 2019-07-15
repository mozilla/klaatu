# Firefox Experiments validator - Klaatu

A tool used to validate firefox experiments

## Prerequisites

You should have docker installed.

## How to use

1. Clone repository
2. Create ```test_files``` and ```test_results``` directories.
3. Place experiments in ```test_files``` folder.
4. Run tests in docker with ```./utilities/run_all.sh```

The tests should run and move all passed experiments to a ```validated_experiments``` folder.