"""Refresh semantic models in the CI workspace and wait for them to finish.

Reads PQL_TENANT_ID, PQL_CLIENT_ID, PQL_CLIENT_SECRET and PQL_WORKSPACE_ID
from the environment.

Before refreshing, each model's connections are checked: any SharePoint
source must be bound to a shareable cloud connection. That binding is set
once by hand (docs/ci-setup.md, step 6.1), and this check turns a lost
binding into a clear message instead of a vague credentials error.
"""

import argparse
import os
import sys
import time

import requests
from azure.identity import ClientSecretCredential

PBI_API = "https://api.powerbi.com/v1.0/myorg"
FABRIC_API = "https://api.fabric.microsoft.com/v1"
PBI_SCOPE = "https://analysis.windows.net/powerbi/api/.default"
FABRIC_SCOPE = "https://api.fabric.microsoft.com/.default"
REQUIRED_ENV = ("PQL_TENANT_ID", "PQL_CLIENT_ID", "PQL_CLIENT_SECRET", "PQL_WORKSPACE_ID")
DONE = {"Completed", "Failed", "Cancelled", "Disabled"}


class Api:
    def __init__(self, credential):
        self.credential = credential

    def _headers(self, scope):
        return {"Authorization": f"Bearer {self.credential.get_token(scope).token}"}

    def get(self, url, scope=PBI_SCOPE):
        resp = requests.get(url, headers=self._headers(scope), timeout=60)
        resp.raise_for_status()
        return resp.json()

    def post(self, url, body, scope=PBI_SCOPE):
        return requests.post(url, json=body, headers=self._headers(scope), timeout=60)


def find_datasets(api, workspace_id, names):
    datasets = api.get(f"{PBI_API}/groups/{workspace_id}/datasets")["value"]
    by_name = {d["name"]: d["id"] for d in datasets}
    missing = [n for n in names if n not in by_name]
    if missing:
        raise SystemExit(f"Semantic model(s) not found in the CI workspace: {', '.join(missing)}. "
                         "Did the deploy step run?")
    return {n: by_name[n] for n in names}


def check_bindings(api, workspace_id, name, dataset_id):
    """Fail if a SharePoint source isn't bound to a shareable cloud connection."""
    url = f"{FABRIC_API}/workspaces/{workspace_id}/items/{dataset_id}/connections"
    connections = api.get(url, scope=FABRIC_SCOPE).get("value", [])
    unbound = []
    for conn in connections:
        details = conn.get("connectionDetails") or {}
        path = f"{details.get('type', '')} {details.get('path', '')}".lower()
        if "sharepoint" in path and conn.get("connectivityType") != "ShareableCloud":
            unbound.append(details.get("path") or details.get("type"))
    if unbound:
        raise SystemExit(
            f"{name}: SharePoint source(s) not bound to a shareable cloud connection: "
            f"{', '.join(unbound)}.\nRe-bind the connection: see docs/ci-setup.md, step 6.1.")
    print(f"{name}: connection binding OK ({len(connections)} connection(s))")


def start_refresh(api, workspace_id, name, dataset_id):
    body = {"type": "full", "commitMode": "transactional", "applyRefreshPolicy": True, "retryCount": 1}
    resp = api.post(f"{PBI_API}/groups/{workspace_id}/datasets/{dataset_id}/refreshes", body)
    if resp.status_code != 202:
        raise SystemExit(f"{name}: refresh request failed ({resp.status_code}): {resp.text}")
    location = resp.headers.get("Location")
    if not location:
        raise SystemExit(f"{name}: refresh accepted but no Location header was returned")
    print(f"{name}: refresh started")
    return location


def wait(api, locations, timeout_s):
    deadline, delay = time.monotonic() + timeout_s, 10
    pending, failed = dict(locations), []
    while pending:
        if time.monotonic() > deadline:
            raise SystemExit(f"Timed out after {timeout_s}s waiting for: {', '.join(pending)}")
        time.sleep(delay)
        delay = min(delay * 2, 60)
        for name, url in list(pending.items()):
            state = api.get(url)
            status = state.get("status")
            if status not in DONE:
                continue
            del pending[name]
            if status == "Completed":
                print(f"{name}: refresh completed")
            else:
                print(f"{name}: refresh {status}")
                for msg in state.get("messages", []):
                    print(f"  {msg.get('type', '')}: {msg.get('message', msg)}")
                failed.append(name)
    return failed


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("models", nargs="+", help="semantic model names, e.g. TestingModel RLS_Model")
    parser.add_argument("--timeout", type=int, default=1200, help="seconds to wait for all refreshes")
    parser.add_argument("--skip-binding-check", action="store_true")
    args = parser.parse_args()

    missing = [name for name in REQUIRED_ENV if not os.environ.get(name)]
    if missing:
        print(f"Missing environment variables: {', '.join(missing)}", file=sys.stderr)
        return 1

    workspace_id = os.environ["PQL_WORKSPACE_ID"]
    api = Api(ClientSecretCredential(os.environ["PQL_TENANT_ID"], os.environ["PQL_CLIENT_ID"],
                                     os.environ["PQL_CLIENT_SECRET"]))
    datasets = find_datasets(api, workspace_id, args.models)
    if not args.skip_binding_check:
        for name, dataset_id in datasets.items():
            check_bindings(api, workspace_id, name, dataset_id)
    locations = {n: start_refresh(api, workspace_id, n, d) for n, d in datasets.items()}
    failed = wait(api, locations, args.timeout)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
