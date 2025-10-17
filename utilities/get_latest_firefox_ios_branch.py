"""
Script to find the latest Firefox-iOS release branch matching a given major version.

Firefox Desktop uses versions like 128.0, 129.1, 144.0.4, etc.
Firefox-iOS uses branches like release/v128, release/v129.1, etc.

This script queries the GitHub API to find the latest patch version for a given major version.

"""

import sys
import json
import argparse
import os
from packaging.version import Version, parse as parse_version_str
from typing import List, Optional

import requests


def parse_version(branch_name: str) -> Optional[Version]:
    """Parse a Firefox-iOS branch name into a Version object."""

    if not branch_name.startswith('release/v'):
        return None

    version_str = branch_name.replace('release/v', '')

    try:
        parsed = parse_version_str(version_str)
        if isinstance(parsed, Version):
            return parsed
        return None
    except Exception:
        return None


def get_firefox_ios_branches(github_token: Optional[str] = None) -> List[str]:
    """Fetch all Firefox-iOS release branches from GitHub using the REST API."""
    base_url = "https://api.github.com/repos/mozilla-mobile/firefox-ios/branches"
    all_branches = []
    page = 1
    per_page = 100

    # Setup headers with optional authentication to avoid rate limits
    headers = {'Accept': 'application/vnd.github.v3+json'}
    if github_token:
        headers['Authorization'] = f'token {github_token}'

    try:
        while True:
            response = requests.get(
                base_url,
                params={'per_page': per_page, 'page': page},
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            branches = response.json()

            if not branches:
                break

            all_branches.extend(branches)
            page += 1

        # Filter for release branches only
        release_branches = [
            b['name'] for b in all_branches
            if b['name'].startswith('release/v')
        ]

        return release_branches

    except requests.RequestException as e:
        print(f"Error fetching branches from GitHub: {e}", file=sys.stderr)
        sys.exit(1)
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error parsing GitHub API response: {e}", file=sys.stderr)
        sys.exit(1)


def find_latest_branch(major_version: int, branches: List[str]) -> str:
    """Find the latest branch for the given major version."""
    matching_branches = []

    for branch in branches:
        parsed_version = parse_version(branch)
        if parsed_version is None:
            continue

        # Check if major version matches
        if parsed_version.major == major_version:
            matching_branches.append((branch, parsed_version))

    if not matching_branches:
        raise ValueError(f"No branches found for major version {major_version}")

    matching_branches.sort(key=lambda x: x[1], reverse=True)
    latest_branch = matching_branches[0][0]
    return latest_branch


def main():
    parser = argparse.ArgumentParser(
        description='Find the latest Firefox-iOS release branch for a given major version'
    )
    parser.add_argument(
        'version',
        help='Firefox major version number (e.g., 128 or 128.0)'
    )

    args = parser.parse_args()

    # Parse the input version to get major version
    version_parts = args.version.split('.')
    try:
        major_version = int(version_parts[0])
    except ValueError:
        print(f"Invalid version format: {args.version}", file=sys.stderr)
        sys.exit(1)

    # Get GitHub token from environment variable (avoids rate limiting)
    github_token = os.environ.get('GITHUB_TOKEN')
    branches = get_firefox_ios_branches(github_token)

    # Find the latest branch for this major version
    try:
        latest_branch = find_latest_branch(major_version, branches)
        print(latest_branch)

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
