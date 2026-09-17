"""
Task Executor — Executes each planned task by generating content via the LLM.

Iterates through the plan's task list, calls the LLM with task-specific
context, and accumulates section content for the document.
"""

from __future__ import annotations

from loguru import logger

from agent.llm import GeminiClient
from agent.models import (
    ExecutionResult,
    Plan,
    SectionContent,
    TaskStatus,
)
from agent.prompts import (
    EXECUTION_PROMPT_TEMPLATE,
    EXECUTION_SYSTEM_PROMPT,
    REVISION_PROMPT_TEMPLATE,
)


class TaskExecutor:
    """Executes plan tasks sequentially, generating content for each section."""

    def __init__(self, llm: GeminiClient) -> None:
        self.llm = llm

    def execute(self, plan: Plan) -> ExecutionResult:
        """Execute all tasks in the plan and return section content."""
        logger.info(f"Executor: Starting execution of {len(plan.tasks)} tasks...")

        sections: list[SectionContent] = []
        execution_log: list[str] = []

        system_prompt = EXECUTION_SYSTEM_PROMPT.format(
            doc_type=plan.document_type.value,
            doc_title=plan.document_title,
            summary=plan.summary,
            assumptions="; ".join(plan.assumptions) if plan.assumptions else "None",
        )

        for task in plan.tasks:
            task.status = TaskStatus.IN_PROGRESS
            log_msg = f"Step {task.step_number}: Generating '{task.title}'..."
            logger.info(f"   {log_msg}")
            execution_log.append(log_msg)

            try:
                prompt = EXECUTION_PROMPT_TEMPLATE.format(
                    title=task.title,
                    description=task.description,
                    expected_output=task.expected_output,
                )

                raw = self.llm.generate_json(
                    prompt, 
                    system_instruction=system_prompt,
                    model=self.llm.light_model
                )

                section = SectionContent(
                    heading=raw.get("heading", task.title),
                    body=raw.get("body", ""),
                    bullet_points=raw.get("bullet_points", []),
                    table_data=raw.get("table_data"),
                )
                sections.append(section)

                task.status = TaskStatus.COMPLETED
                execution_log.append(
                    f"Step {task.step_number}: Completed '{task.title}'"
                )

            except Exception as e:
                task.status = TaskStatus.FAILED
                error_msg = (
                    f"Step {task.step_number}: Failed '{task.title}': {e}"
                )
                logger.error(error_msg)
                execution_log.append(error_msg)
                # Add a fallback section so the document isn't missing content
                sections.append(
                    SectionContent(
                        heading=task.title,
                        body=f"[Content generation failed for this section: {e}]",
                    )
                )

        logger.info(f"Execution complete: {len(sections)} sections generated")
        return ExecutionResult(sections=sections, execution_log=execution_log)

    def revise_section(
        self,
        plan: Plan,
        section: SectionContent,
        feedback: str,
    ) -> SectionContent:
        """Revise a specific section based on reflection feedback."""
        logger.info(f"Revising section: '{section.heading}'")

        system_prompt = EXECUTION_SYSTEM_PROMPT.format(
            doc_type=plan.document_type.value,
            doc_title=plan.document_title,
            summary=plan.summary,
            assumptions="; ".join(plan.assumptions) if plan.assumptions else "None",
        )

        prompt = REVISION_PROMPT_TEMPLATE.format(
            title=section.heading,
            current_content=section.body,
            feedback=feedback,
        )

        try:
            raw = self.llm.generate_json(
                prompt, 
                system_instruction=system_prompt,
                model=self.llm.light_model
            )
            return SectionContent(
                heading=raw.get("heading", section.heading),
                body=raw.get("body", section.body),
                bullet_points=raw.get("bullet_points", section.bullet_points),
                table_data=raw.get("table_data", section.table_data),
            )
        except Exception as e:
            logger.error(f"Revision failed for '{section.heading}': {e}")
            return section  # Return original on failure
