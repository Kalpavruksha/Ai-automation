"""
Pydantic models for the autonomous agent pipeline.

Defines structured data models for requests, plans, execution results,
reflection outcomes, and the final API response.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────

class DocumentType(str, Enum):
    """Supported document types the agent can produce."""
    PROPOSAL = "proposal"
    MEETING_MINUTES = "meeting_minutes"
    PROJECT_PLAN = "project_plan"
    BUSINESS_REPORT = "business_report"
    TECHNICAL_DESIGN = "technical_design"
    SOP = "sop"
    PRODUCT_SPEC = "product_spec"
    GENERAL = "general"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REVISED = "revised"


# ──────────────────────────────────────────────
# Request
# ──────────────────────────────────────────────

class AgentRequest(BaseModel):
    """Incoming request to the agent."""
    request: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Natural language request describing the document to generate.",
    )


# ──────────────────────────────────────────────
# Planning
# ──────────────────────────────────────────────

class TaskItem(BaseModel):
    """A single task in the execution plan."""
    step_number: int
    title: str
    description: str
    expected_output: str
    status: TaskStatus = TaskStatus.PENDING


class Plan(BaseModel):
    """Agent-generated execution plan."""
    document_type: DocumentType
    document_title: str
    summary: str = Field(description="Brief summary of what the agent understood from the request.")
    assumptions: list[str] = Field(
        default_factory=list,
        description="Assumptions the agent made when information was missing or ambiguous.",
    )
    tasks: list[TaskItem]
    created_at: datetime = Field(default_factory=datetime.now)


# ──────────────────────────────────────────────
# Execution
# ──────────────────────────────────────────────

class SectionContent(BaseModel):
    """Content produced for a single document section."""
    heading: str
    body: str
    bullet_points: list[str] = Field(default_factory=list)
    table_data: Optional[list[dict]] = Field(
        default=None,
        description="Optional tabular data as list of row-dicts.",
    )


class ExecutionResult(BaseModel):
    """Result of executing all planned tasks."""
    sections: list[SectionContent]
    execution_log: list[str] = Field(default_factory=list)


# ──────────────────────────────────────────────
# Reflection
# ──────────────────────────────────────────────

class ReflectionResult(BaseModel):
    """Outcome of the agent's self-check."""
    passed: bool
    overall_score: int = Field(ge=1, le=10, description="Quality score 1-10")
    feedback: str
    missing_sections: list[str] = Field(default_factory=list)
    improvement_suggestions: list[str] = Field(default_factory=list)


# ──────────────────────────────────────────────
# API Response
# ──────────────────────────────────────────────

class AgentResponse(BaseModel):
    """Final response returned by the POST /agent endpoint."""
    status: str = "success"
    original_request: str
    plan: Plan
    execution_log: list[str]
    reflection: ReflectionResult
    prototype_html: Optional[str] = Field(default=None, description="Generated HTML prototype")
    document_filename: str
    document_download_url: str
    completed_at: datetime = Field(default_factory=datetime.now)
