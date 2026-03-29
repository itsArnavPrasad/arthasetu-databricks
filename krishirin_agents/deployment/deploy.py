"""Deploy KrishiRin ADK agents to Vertex AI Agent Engine.

Usage:
    python deploy.py --create --pipeline precall
    python deploy.py --create --pipeline oncall
    python deploy.py --create --pipeline both
    python deploy.py --list
    python deploy.py --delete --resource_id=<ID>

Requires:
    - gcloud auth login && gcloud auth application-default login
    - GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION, GOOGLE_CLOUD_STORAGE_BUCKET in .env
"""

import argparse
import os
import sys

# Add project root so krishirin_agents is importable
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from dotenv import load_dotenv

load_dotenv(os.path.join(project_root, ".env"))

REQUIREMENTS = [
    "google-adk>=1.0.0",
    "python-dotenv>=1.0.0",
    "pydantic>=2.0.0",
    "requests>=2.31.0",
    "google-cloud-aiplatform[agent_engines]>=1.91.0",
    "google-genai>=1.5.0",
]


def init_vertexai():
    """Initialize Vertex AI with project config from .env."""
    import vertexai

    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    bucket = os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET")

    if not project_id:
        print("ERROR: GOOGLE_CLOUD_PROJECT not set in .env")
        sys.exit(1)
    if not bucket:
        print("ERROR: GOOGLE_CLOUD_STORAGE_BUCKET not set in .env")
        sys.exit(1)

    print(f"Project:  {project_id}")
    print(f"Location: {location}")
    print(f"Bucket:   gs://{bucket}")

    vertexai.init(
        project=project_id,
        location=location,
        staging_bucket=f"gs://{bucket}",
    )


def deploy_precall():
    """Deploy precall analysis pipeline to Agent Engine."""
    from vertexai import agent_engines
    from vertexai.preview.reasoning_engines import AdkApp
    from krishirin_agents.precall.coordinator.agent import root_agent

    print("\nDeploying Precall Pipeline...")
    adk_app = AdkApp(agent=root_agent, enable_tracing=True)

    remote_agent = agent_engines.create(
        adk_app,
        display_name="KrishiRin Precall Analysis",
        requirements=REQUIREMENTS,
        extra_packages=[
            os.path.join(project_root, "krishirin_agents"),
        ],
    )
    print(f"Precall deployed: {remote_agent.resource_name}")
    return remote_agent


def deploy_oncall():
    """Deploy oncall advisory pipeline to Agent Engine."""
    from vertexai import agent_engines
    from vertexai.preview.reasoning_engines import AdkApp
    from krishirin_agents.oncall.coordinator.agent import root_agent

    print("\nDeploying Oncall Pipeline...")
    adk_app = AdkApp(agent=root_agent, enable_tracing=True)

    remote_agent = agent_engines.create(
        adk_app,
        display_name="KrishiRin Oncall Advisory",
        requirements=REQUIREMENTS,
        extra_packages=[
            os.path.join(project_root, "krishirin_agents"),
        ],
    )
    print(f"Oncall deployed: {remote_agent.resource_name}")
    return remote_agent


def list_agents():
    """List all deployed agents on Agent Engine."""
    from vertexai import agent_engines

    remote_agents = agent_engines.list()
    if not remote_agents:
        print("No agents deployed.")
        return

    for agent in remote_agents:
        print(f"\n{agent.name} (\"{agent.display_name}\")")
        print(f"  Created: {agent.create_time}")
        print(f"  Updated: {agent.update_time}")


def delete_agent(resource_id: str):
    """Delete a deployed agent by resource ID."""
    from vertexai import agent_engines

    remote_agent = agent_engines.get(resource_id)
    remote_agent.delete(force=True)
    print(f"Deleted: {resource_id}")


def main():
    parser = argparse.ArgumentParser(description="Deploy KrishiRin agents to Agent Engine")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--create", action="store_true", help="Deploy agent(s)")
    group.add_argument("--list", action="store_true", help="List deployed agents")
    group.add_argument("--delete", action="store_true", help="Delete a deployed agent")

    parser.add_argument(
        "--pipeline",
        choices=["precall", "oncall", "both"],
        default="both",
        help="Which pipeline to deploy (default: both)",
    )
    parser.add_argument("--resource_id", help="Resource ID for delete operation")

    args = parser.parse_args()

    init_vertexai()

    if args.list:
        list_agents()
    elif args.delete:
        if not args.resource_id:
            print("ERROR: --resource_id required for --delete")
            sys.exit(1)
        delete_agent(args.resource_id)
    elif args.create:
        if args.pipeline in ("precall", "both"):
            deploy_precall()
        if args.pipeline in ("oncall", "both"):
            deploy_oncall()
        print("\nDeployment complete.")


if __name__ == "__main__":
    main()
