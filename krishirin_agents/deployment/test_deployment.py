"""Test a deployed KrishiRin agent on Vertex AI Agent Engine.

Usage:
    python test_deployment.py --resource_id=<RESOURCE_ID>
    python test_deployment.py --resource_id=<RESOURCE_ID> --message "Run analysis for farmer FARMER_002"
"""

import argparse
import json
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from dotenv import load_dotenv

load_dotenv(os.path.join(project_root, ".env"))


def test_agent(resource_id: str, message: str):
    """Query a deployed agent and print the response."""
    import vertexai
    from vertexai import agent_engines

    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    bucket = os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET")

    vertexai.init(
        project=project_id,
        location=location,
        staging_bucket=f"gs://{bucket}",
    )

    print(f"Getting agent: {resource_id}")
    remote_agent = agent_engines.get(resource_id)
    print(f"Agent: {remote_agent.display_name}")

    print(f"\nSending message: {message}")
    print("-" * 60)

    response = remote_agent.query(input=message)

    if isinstance(response, dict):
        print(json.dumps(response, indent=2, default=str))
    else:
        print(response)

    print("-" * 60)
    print("Test complete.")


def main():
    parser = argparse.ArgumentParser(description="Test deployed KrishiRin agent")
    parser.add_argument("--resource_id", required=True, help="Agent Engine resource ID")
    parser.add_argument(
        "--message",
        default="Run analysis for farmer FARMER_001",
        help="Message to send to the agent",
    )
    args = parser.parse_args()
    test_agent(args.resource_id, args.message)


if __name__ == "__main__":
    main()
