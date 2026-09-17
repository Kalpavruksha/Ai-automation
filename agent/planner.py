"""
Planner Agent — Analyzes requests and generates structured execution plans.

Takes a natural language request and uses the LLM to:
1. Determine the document type
2. Make assumptions for missing/ambiguous information
3. Break the work into ordered tasks
4. Return a structured Plan object
"""

from __future__ import annotations

from loguru import logger

from agent.llm import GeminiClient
from agent.models import DocumentType, Plan, TaskItem
from agent.prompts import PLANNING_PROMPT_TEMPLATE, PLANNING_SYSTEM_PROMPT


class AgentPlanner:
    """Generates a structured execution plan from a user request."""

    def __init__(self, llm: GeminiClient) -> None:
        self.llm = llm

    def create_plan(self, request: str) -> Plan:
        """Analyze the request and return a structured Plan."""
        logger.info("Planning: Analyzing request and generating execution plan...")

        prompt = PLANNING_PROMPT_TEMPLATE.format(request=request)
        raw = self.llm.generate_json(prompt, system_instruction=PLANNING_SYSTEM_PROMPT)

        # Validate document_type against our enum
        doc_type = raw.get("document_type", "general")
        try:
            doc_type_enum = DocumentType(doc_type)
        except ValueError:
            logger.warning(f"Unknown document type '{doc_type}', defaulting to 'general'")
            doc_type_enum = DocumentType.GENERAL

        tasks = [
            TaskItem(
                step_number=t.get("step_number", i + 1),
                title=t["title"],
                description=t["description"],
                expected_output=t.get("expected_output", ""),
            )
            for i, t in enumerate(raw.get("tasks", []))
        ]

        plan = Plan(
            document_type=doc_type_enum,
            document_title=raw.get("document_title", "Untitled Document"),
            summary=raw.get("summary", ""),
            assumptions=raw.get("assumptions", []),
            tasks=tasks,
        )

        logger.info(
            f"Plan created: '{plan.document_title}' "
            f"({plan.document_type.value}) with {len(plan.tasks)} tasks"
        )
        for task in plan.tasks:
            logger.info(f"   Step {task.step_number}: {task.title}")

        return plan
