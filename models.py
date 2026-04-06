from openenv.core.env_server.types import Action, Observation
from pydantic import Field
from typing import Dict, List, Optional

class ComplianceAction(Action):
    action_type: str = Field(
        ..., description="Type of action: extract_clauses, analyse_gap, or produce_checklist"
    )
    content: str = Field(
        ..., description="Content of the action"
    )


class ComplianceObservation(Observation):
    step: int = Field(default=0, description="Current step number")
    max_steps: int = Field(default=8, description="Maximum steps per episode")
    message: str = Field(default="", description="Message to the agent")
    regulation_document: Optional[str] = Field(default=None, description="The regulation text")
    company_profile: Optional[Dict] = Field(default=None, description="The company profile")
    episode_id: Optional[str] = Field(default=None, description="Current episode ID")
    difficulty: Optional[str] = Field(default=None, description="Episode difficulty: easy, medium, hard")

    extracted_clauses_so_far: Optional[List[str]] = Field(default=None, description="Clause IDs extracted so far")
    gaps_found_so_far: Optional[List[Dict]] = Field(default=None, description="Gap items recorded so far")
    partial_score: Optional[float] = Field(default=None, description="Running partial score so far")
    steps_remaining: Optional[int] = Field(default=None, description="Steps remaining in episode")