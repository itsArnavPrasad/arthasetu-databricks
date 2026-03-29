"""
Root coordinator for the KrishiRin Pre-Call Analysis Pipeline.

This pipeline analyzes the farmer's risk profile, creditworthiness, and
agricultural situation BEFORE the advisory call. It does NOT recommend
loan products or schemes — that happens during/after the call.

Flow (4 stages):
  Stage 1: data_loader → farmer_context
  Stage 2: Parallel(score_explainer, risk_flag_detector, market_research)
  Stage 3: gap_analyzer → gap_analysis
  Stage 4: precall_synthesis → precall_analysis (final report + clarification questions)
"""

import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
precall_dir = os.path.dirname(current_dir)
krishirin_dir = os.path.dirname(precall_dir)
project_dir = os.path.dirname(krishirin_dir)
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from google.adk.agents import SequentialAgent, ParallelAgent

from krishirin_agents.precall.data_loader.agent import data_loader_agent
from krishirin_agents.precall.score_explainer.agent import score_explainer_agent
from krishirin_agents.precall.risk_flag_detector.agent import risk_flag_detector_agent
from krishirin_agents.precall.market_research.agent import market_research_agent
from krishirin_agents.precall.gap_analyzer.agent import gap_analyzer_agent
from krishirin_agents.precall.precall_synthesis.agent import precall_synthesis_agent

# Stage 2: 3 analysis agents in parallel (all only need farmer_context)
parallel_analysis = ParallelAgent(
    name="parallel_analysis",
    sub_agents=[
        score_explainer_agent,      # ML scoring via Databricks endpoints
        risk_flag_detector_agent,   # Risk flag detection
        market_research_agent,      # Crop price + yield predictions
    ],
    description="Runs 3 analysis agents in parallel: ML credit scoring, risk detection, crop market research.",
)

precall_analysis_pipeline = SequentialAgent(
    name="precall_analysis_pipeline",
    description=(
        "KrishiRin Pre-Call Analysis: 4-stage pipeline. "
        "Loads data → runs ML scoring + risk analysis + market research in parallel → "
        "gap analysis → final synthesis with clarification questions for the voice call."
    ),
    sub_agents=[
        data_loader_agent,           # Stage 1: load farmer data from OCR + external sources
        parallel_analysis,           # Stage 2: ML scoring + risk + market (parallel)
        gap_analyzer_agent,          # Stage 3: identify application gaps & actionable insights
        precall_synthesis_agent,     # Stage 4: final report + questions for voice agent
    ],
)

root_agent = precall_analysis_pipeline
