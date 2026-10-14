"""Preview or apply the maintained public-repository controls through gh.

The default is an offline preview. --apply requires the intended repository to
already be public and the caller to have admin permission. This script never
changes visibility or publishes a package, image, or documentation site.
"""

import argparse
import json
from pathlib import Path
import subprocess
import sys


REPOSITORY = "ajavanma/PointCloud-Workflows"
BASE = f"repos/{REPOSITORY}"


def api(method, endpoint, payload=None):
    command = [
        "gh", "api", "--method", method, endpoint,
        "-H", "Accept: application/vnd.github+json",
        "-H", "X-GitHub-Api-Version: 2022-11-28",
    ]
    if payload is not None:
        command.extend(["--input", "-"])
    result = subprocess.run(
        command, input=None if payload is None else json.dumps(payload),
        text=True, capture_output=True, check=False,
    )
    if result.returncode:
        raise RuntimeError(f"{method} {endpoint}: {result.stderr.strip()}")
    return json.loads(result.stdout) if result.stdout.strip() else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Apply to the already-public repository.")
    arguments = parser.parse_args()
    protection = json.loads(Path(__file__).with_name("public-branch-protection.json").read_text())
    security = {"security_and_analysis": {
        "secret_scanning": {"status": "enabled"},
        "secret_scanning_push_protection": {"status": "enabled"},
    }}
    operations = [
        ("PUT", f"{BASE}/branches/main/protection", protection),
        ("PATCH", BASE, security),
        ("PUT", f"{BASE}/vulnerability-alerts", None),
        ("PUT", f"{BASE}/private-vulnerability-reporting", None),
        ("PUT", f"{BASE}/actions/permissions/fork-pr-contributor-approval", {"approval_policy": "all_external_contributors"}),
    ]
    if not arguments.apply:
        print(json.dumps({"repository": REPOSITORY, "mode": "preview", "operations": [
            {"method": method, "endpoint": endpoint, "payload": payload}
            for method, endpoint, payload in operations
        ]}, indent=2))
        return

    repository = api("GET", BASE)
    if repository.get("full_name") != REPOSITORY or repository.get("private") is not False:
        raise RuntimeError("Refusing changes: the intended repository must already be public.")
    if repository.get("default_branch") != "main" or not repository.get("permissions", {}).get("admin"):
        raise RuntimeError("Refusing changes: main must be the default branch and admin permission is required.")
    for method, endpoint, payload in operations:
        api(method, endpoint, payload)
        print(f"Applied {method} {endpoint}")

    observed = api("GET", f"{BASE}/branches/main/protection")
    for setting in ("enforce_admins", "required_linear_history", "required_conversation_resolution"):
        if observed.get(setting, {}).get("enabled") is not True:
            raise RuntimeError(f"Branch protection verification failed: {setting}")
    for setting in ("allow_force_pushes", "allow_deletions"):
        if observed.get(setting, {}).get("enabled") is not False:
            raise RuntimeError(f"Branch protection verification failed: {setting}")
    required_checks = {(item["context"], item["app_id"]) for item in protection["required_status_checks"]["checks"]}
    actual_checks = {(item["context"], item["app_id"]) for item in observed["required_status_checks"]["checks"]}
    if actual_checks != required_checks or observed["required_status_checks"].get("strict") is not True:
        raise RuntimeError("Branch protection verification failed: required status checks")
    reviews = observed.get("required_pull_request_reviews", {})
    if reviews.get("required_approving_review_count") != 0 or not reviews.get("dismiss_stale_reviews"):
        raise RuntimeError("Branch protection verification failed: solo-maintainer PR policy")
    observed_security = api("GET", BASE).get("security_and_analysis", {})
    for setting in security["security_and_analysis"]:
        if observed_security.get(setting, {}).get("status") != "enabled":
            raise RuntimeError(f"Security verification failed: {setting}")
    api("GET", f"{BASE}/vulnerability-alerts")
    if api("GET", f"{BASE}/private-vulnerability-reporting").get("enabled") is not True:
        raise RuntimeError("Private vulnerability reporting verification failed")
    if api("GET", f"{BASE}/actions/permissions/fork-pr-contributor-approval").get("approval_policy") != "all_external_contributors":
        raise RuntimeError("External contributor workflow approval verification failed")
    print("Verified branch protection, secret scanning, push protection, dependency alerts, private reporting, and contributor workflow approvals.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, KeyError) as error:
        print(f"public settings: {error}", file=sys.stderr)
        raise SystemExit(1)
