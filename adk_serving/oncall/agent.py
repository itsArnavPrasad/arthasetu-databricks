"""Oncall advisory pipeline — entry point for adk api_server."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from krishirin_agents.oncall.coordinator.agent import root_agent
