"""
Root coordinator for the KrishiRin On-Call Advisory Pipeline.

Pipeline (3 stages, 11 agents, 7 visible output_keys):
  Stage 1: call_analyzer → state["call_insights"]
  Stage 2: parallel_tracks
    Track A: Parallel(scheme_matcher, bank_product) → policy_optimizer → state["optimal_policy"]
    Track B: crop_planner → Parallel(input_cost, market_timing) → agri_synthesizer → state["agri_advisory"]
    Track C: risk_mitigator → state["risk_plan"]
  Stage 3: cashflow_mapper → state["cashflow_map"]
"""

import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
oncall_dir = os.path.dirname(current_dir)
krishirin_dir = os.path.dirname(oncall_dir)
project_dir = os.path.dirname(krishirin_dir)
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from google.adk.agents import SequentialAgent, ParallelAgent

from krishirin_agents.oncall.call_analyzer.agent import call_analyzer_agent
from krishirin_agents.oncall.loan_policy.agent import loan_policy_pipeline
from krishirin_agents.oncall.agri_advisory.agent import agri_advisory_pipeline
from krishirin_agents.oncall.risk_mitigator.agent import risk_mitigator_agent
from krishirin_agents.oncall.cashflow_mapper.agent import cashflow_mapper_agent

# --- Stage 2: Three parallel tracks ---
parallel_tracks = ParallelAgent(
    name="parallel_tracks",
    sub_agents=[
        loan_policy_pipeline,     # Track A: scheme matching → bank comparison → optimization
        agri_advisory_pipeline,   # Track B: crop plan → costs → market → synthesis
        risk_mitigator_agent,     # Track C: insurance, diversification, buffers
    ],
    description="Runs loan policy, agricultural advisory, and risk mitigation in parallel.",
)

# --- Root Pipeline (no postcall_synthesis — voice agent has results already) ---
postcall_advisory_pipeline = SequentialAgent(
    name="postcall_advisory_pipeline",
    description=(
        "KrishiRin On-Call Advisory: 3-stage pipeline. "
        "Analyzes call transcript → parallel tracks (policy + agri + risk) → cashflow map."
    ),
    sub_agents=[
        call_analyzer_agent,       # Stage 1: Analyze call transcript
        parallel_tracks,           # Stage 2: Policy + Agri + Risk (parallel)
        cashflow_mapper_agent,     # Stage 3: 12-month cashflow projection
    ],
)

root_agent = postcall_advisory_pipeline
