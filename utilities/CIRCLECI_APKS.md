# CircleCI APK Fetcher

Scripts to automatically find and download APK artifacts from CircleCI jobs in the mozilla/experimenter repository.

## Files

- **get_circleci_apks.py** - Python script that uses CircleCI API to find and download APKs
- **fetch_circleci_apks.sh** - Bash wrapper for easy CI usage

## Prerequisites

- Python 3.6+
- `requests` library (`pip install requests`)
- CircleCI API token (optional for public repos, required for private repos)

## Usage

### Python Script

Basic usage (defaults to mozilla/experimenter, main branch):
```bash
python utilities/get_circleci_apks.py
```

With custom options:
```bash
python utilities/get_circleci_apks.py \
  --branch main \
  --job-name build-fenix \
  --output-dir ./apks
```

All options:
```bash
python utilities/get_circleci_apks.py \
  --org mozilla \
  --repo experimenter \
  --branch main \
  --workflow-name "Build" \
  --job-name "build-fenix" \
  --output-dir ./apks \
  --token YOUR_CIRCLECI_TOKEN
```

### Bash Script

The bash script provides a simpler interface using environment variables:

```bash
# Basic usage
./utilities/fetch_circleci_apks.sh

# With environment variables
CIRCLECI_BRANCH=main \
CIRCLECI_OUTPUT_DIR=./apks \
CIRCLECI_JOB_NAME=build-fenix \
./utilities/fetch_circleci_apks.sh
```

### GitHub Actions Integration

Add this step to your GitHub Actions workflow:

```yaml
- name: Fetch APKs from CircleCI
  env:
    CIRCLECI_TOKEN: ${{ secrets.CIRCLECI_TOKEN }}  # Optional
    CIRCLECI_BRANCH: main
    CIRCLECI_OUTPUT_DIR: ${{ github.workspace }}/klaatu
  run: |
    ./utilities/fetch_circleci_apks.sh
```

Or use the Python script directly:

```yaml
- name: Install Python dependencies
  run: pip install requests

- name: Fetch APKs from CircleCI
  env:
    CIRCLECI_TOKEN: ${{ secrets.CIRCLECI_TOKEN }}  # Optional
  run: |
    python utilities/get_circleci_apks.py \
      --branch main \
      --output-dir ${{ github.workspace }}/klaatu \
      --job-name build-fenix
```

### Example for Android Workflow

Here's how to integrate it into the android_manual.yml workflow:

```yaml
- name: Fetch Fenix APKs from Experimenter CircleCI
  env:
    CIRCLECI_TOKEN: ${{ secrets.CIRCLECI_TOKEN }}
    CIRCLECI_BRANCH: main
    CIRCLECI_OUTPUT_DIR: ${{ github.workspace }}/klaatu
  working-directory: klaatu
  run: |
    pip install requests
    python utilities/get_circleci_apks.py --job-name fenix

- name: Install APKs
  working-directory: klaatu
  run: |
    adb install *.apk
```

## Environment Variables

The bash script supports these environment variables:

- `CIRCLECI_TOKEN` - CircleCI API token (optional for public repos)
- `CIRCLECI_ORG` - GitHub organization (default: mozilla)
- `CIRCLECI_REPO` - GitHub repository (default: experimenter)
- `CIRCLECI_BRANCH` - Branch name (default: main)
- `CIRCLECI_OUTPUT_DIR` - Output directory (default: current directory)
- `CIRCLECI_WORKFLOW_NAME` - Filter by workflow name (optional)
- `CIRCLECI_JOB_NAME` - Filter by job name (optional)

## How It Works

1. Fetches recent pipelines from the specified repository and branch
2. For each pipeline, gets all workflows
3. For each successful workflow, gets all jobs
4. For each successful job, checks for artifacts
5. Downloads any APK artifacts found
6. Stops after downloading from the first successful job with APKs

This ensures you always get the most recent successful build's APKs without any manual intervention.

## CircleCI API Token

To access private repositories or increase rate limits, you'll need a CircleCI API token:

1. Go to https://app.circleci.com/settings/user/tokens
2. Create a new Personal API Token
3. Set it as `CIRCLECI_TOKEN` environment variable or use `--token` flag

For GitHub Actions, add it as a repository secret:
- Go to repository Settings → Secrets and variables → Actions
- Add new secret named `CIRCLECI_TOKEN`

## Troubleshooting

**No APKs found:**
- Check that the branch name is correct
- Verify there are recent successful builds with APK artifacts
- Try without job/workflow filters first
- Check if you need a CircleCI token for the repository

**Download fails:**
- Ensure you have the `requests` library installed
- Check your CircleCI token has proper permissions
- Verify the artifact URLs are accessible

**Rate limiting:**
- Add a CircleCI API token to increase rate limits
- The script checks up to 20 recent pipelines by default
