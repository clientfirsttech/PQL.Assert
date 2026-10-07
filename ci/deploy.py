"""Publish the staged test models and reports to the CI workspace with fabric-cicd.

Run `python ci/build_stage.py stage` first. Reads PQL_TENANT_ID, PQL_CLIENT_ID,
PQL_CLIENT_SECRET and PQL_WORKSPACE_ID from the environment.

Items are updated in place and never unpublished, so the one-time SharePoint
connection binding on TestingModel survives every deploy (see docs/ci-setup.md).
"""

import argparse
import os
import sys
from pathlib import Path

from azure.identity import ClientSecretCredential
from fabric_cicd import FabricWorkspace, publish_all_items

REPO = Path(__file__).resolve().parent.parent
REQUIRED_ENV = ("PQL_TENANT_ID", "PQL_CLIENT_ID", "PQL_CLIENT_SECRET", "PQL_WORKSPACE_ID")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stage", default="_stage", help="folder produced by build_stage.py stage")
    args = parser.parse_args()

    missing = [name for name in REQUIRED_ENV if not os.environ.get(name)]
    if missing:
        print(f"Missing environment variables: {', '.join(missing)}", file=sys.stderr)
        return 1

    stage = (REPO / args.stage).resolve()
    if not any(stage.glob("*.SemanticModel")):
        print(f"No staged semantic models in {stage}. Run: python ci/build_stage.py stage", file=sys.stderr)
        return 1

    credential = ClientSecretCredential(
        tenant_id=os.environ["PQL_TENANT_ID"],
        client_id=os.environ["PQL_CLIENT_ID"],
        client_secret=os.environ["PQL_CLIENT_SECRET"],
    )
    workspace = FabricWorkspace(
        workspace_id=os.environ["PQL_WORKSPACE_ID"],
        repository_directory=str(stage),
        item_type_in_scope=["SemanticModel", "Report"],
        token_credential=credential,
    )
    publish_all_items(workspace)
    return 0


if __name__ == "__main__":
    sys.exit(main())
