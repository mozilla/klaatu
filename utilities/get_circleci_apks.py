"""
Script to automatically find and download APK artifacts from CircleCI jobs in mozilla/experimenter repo.

This script is designed for CI usage - it will automatically fetch the most recent successful
APK artifacts without requiring user input.

Usage:
    # Fetch APKs from most recent successful build on main branch
    python get_circleci_apks.py

    # Fetch from specific branch
    python get_circleci_apks.py --branch main

    # Fetch specific job
    python get_circleci_apks.py --job-name build-fenix

Environment Variables:
    CIRCLECI_TOKEN: CircleCI API token (required for private repos)
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

import requests


class CircleCIArtifactFetcher:
    """Fetches APK artifacts from CircleCI jobs."""

    BASE_URL = "https://circleci.com/api/v2"

    def __init__(self, token: Optional[str] = None):
        """
        Initialize the fetcher.

        Args:
            token: CircleCI API token. If not provided, will try to get from CIRCLECI_TOKEN env var.
        """
        self.token = token or os.environ.get("CIRCLECI_TOKEN")
        self.headers = {}
        if self.token:
            self.headers["Circle-Token"] = self.token

    def get_recent_pipelines(
        self, org: str, repo: str, branch: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get recent pipelines for a project."""
        url = f"{self.BASE_URL}/project/github/{org}/{repo}/pipeline"
        params = {}
        if branch:
            params["branch"] = branch

        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()

        data = response.json()
        return data.get("items", [])[:limit]

    def get_pipeline_workflows(self, pipeline_id: str) -> List[Dict[str, Any]]:
        """Get workflows for a specific pipeline."""
        url = f"{self.BASE_URL}/pipeline/{pipeline_id}/workflow"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()

        data = response.json()
        return data.get("items", [])

    def get_workflow_jobs(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get jobs for a specific workflow."""
        url = f"{self.BASE_URL}/workflow/{workflow_id}/job"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()

        data = response.json()
        return data.get("items", [])

    def get_job_artifacts(
        self, job_number: int, org: str, repo: str
    ) -> List[Dict[str, Any]]:
        """Get artifacts for a specific job."""
        url = f"{self.BASE_URL}/project/github/{org}/{repo}/{job_number}/artifacts"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()

        data = response.json()
        return data.get("items", [])

    def download_artifact(self, artifact_url: str, output_path: Path) -> None:
        """Download an artifact to a file."""
        response = requests.get(artifact_url, headers=self.headers, stream=True)
        response.raise_for_status()

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

    def find_and_download_apks(
        self,
        org: str,
        repo: str,
        output_dir: Path,
        branch: Optional[str] = None,
        workflow_name: Optional[str] = None,
        job_name: Optional[str] = None,
    ) -> int:
        """
        Find and download APK artifacts from the most recent successful job.

        Returns:
            Number of APKs downloaded
        """
        print(f"Searching for APK artifacts in {org}/{repo}")
        if branch:
            print(f"  Branch: {branch}")
        if workflow_name:
            print(f"  Workflow filter: {workflow_name}")
        if job_name:
            print(f"  Job filter: {job_name}")

        pipelines = self.get_recent_pipelines(org, repo, branch)
        print(f"\nFound {len(pipelines)} recent pipelines to check")

        downloaded_count = 0

        for pipeline in pipelines:
            pipeline_id = pipeline["id"]
            pipeline_number = pipeline["number"]
            pipeline_state = pipeline.get("state", "unknown")

            print(f"\nChecking pipeline #{pipeline_number} (state: {pipeline_state})")

            try:
                workflows = self.get_pipeline_workflows(pipeline_id)

                for workflow in workflows:
                    workflow_id = workflow["id"]
                    workflow_name_actual = workflow["name"]
                    workflow_status = workflow.get("status", "unknown")

                    if workflow_name and workflow_name not in workflow_name_actual:
                        continue

                    if workflow_status != "success":
                        print(
                            f"  Skipping workflow '{workflow_name_actual}' (status: {workflow_status})"
                        )
                        continue

                    print(f"  Checking workflow: {workflow_name_actual}")

                    jobs = self.get_workflow_jobs(workflow_id)

                    for job in jobs:
                        job_number = job["job_number"]
                        job_name_actual = job["name"]
                        job_status = job.get("status", "unknown")

                        # Filter by job name if specified
                        if job_name and job_name not in job_name_actual:
                            continue

                        if job_status != "success":
                            continue

                        print(f"    Checking job: {job_name_actual} (#{job_number})")

                        artifacts = self.get_job_artifacts(job_number, org, repo)

                        apk_artifacts = [
                            a for a in artifacts if a.get("path", "").endswith(".apk")
                        ]

                        if apk_artifacts:
                            print(f"    ✓ Found {len(apk_artifacts)} APK artifact(s)!")

                            for artifact in apk_artifacts:
                                artifact_path = artifact["path"]
                                artifact_url = artifact["url"]
                                filename = Path(artifact_path).name
                                output_path = output_dir / filename

                                print(f"Downloading: {filename}")
                                print(f"From: {artifact_url}")
                                print(f"To: {output_path}")

                                try:
                                    self.download_artifact(artifact_url, output_path)
                                    print("✓ Downloaded successfully")
                                    downloaded_count += 1
                                except Exception as e:
                                    print(f"        ✗ Download failed: {e}")

                            # If we downloaded APKs, we're done
                            if downloaded_count > 0:
                                print(f"\n{'=' * 80}")
                                print(
                                    f"Successfully downloaded {downloaded_count} APK(s) from:"
                                )
                                print(f"Pipeline #{pipeline_number}")
                                print(f"Workflow: {workflow_name_actual}")
                                print(f"Job: {job_name_actual}")
                                print(f"Saved to: {output_dir.resolve()}")
                                print(f"{'=' * 80}")
                                return downloaded_count

            except Exception as e:
                print(f"  Error checking pipeline #{pipeline_number}: {e}")
                continue

        if downloaded_count == 0:
            print("\n✗ No APK artifacts found in recent successful jobs")
            return 0

        return downloaded_count


def main():
    parser = argparse.ArgumentParser(
        description="Automatically find and download APK artifacts from CircleCI"
    )
    parser.add_argument(
        "--org", default="mozilla", help="GitHub organization name (default: mozilla)"
    )
    parser.add_argument(
        "--repo",
        default="experimenter",
        help="GitHub repository name (default: experimenter)",
    )
    parser.add_argument("--branch", default="main", help="Branch name (default: main)")
    parser.add_argument(
        "--workflow-name", help="Workflow name filter (optional, matches substring)"
    )
    parser.add_argument(
        "--job-name", help="Job name filter (optional, matches substring)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path.cwd(),
        help="Directory to save downloaded APKs (default: current directory)",
    )
    parser.add_argument(
        "--token", help="CircleCI API token (or set CIRCLECI_TOKEN env var)"
    )

    args = parser.parse_args()

    fetcher = CircleCIArtifactFetcher(token=args.token)

    downloaded = fetcher.find_and_download_apks(
        org=args.org,
        repo=args.repo,
        output_dir=args.output_dir,
        branch=args.branch,
        workflow_name=args.workflow_name,
        job_name=args.job_name,
    )

    if downloaded == 0:
        print("\nFailed to download any APK artifacts")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
