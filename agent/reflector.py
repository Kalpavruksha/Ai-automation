"""
Reflector — Self-check agent that reviews generated content for quality.

After execution, the reflector evaluates the output against the original
request and plan, checking for completeness, accuracy, tone, and structure.
If the quality is insufficient, it provides targeted feedback for revision.
"""

from __future__ import annotations

from loguru import logger

from agent.llm import GeminiClient
from agent.models import ExecutionResult, Plan, ReflectionResult
from agent.prompts import REFLECTION_PROMPT_TEMPLATE, REFLECTION_SYSTEM_PROMPT


class Reflector:
    """Reviews generated content and determines if revision is needed."""

    def __init__(self, llm: GeminiClient) -> None:
        self.llm = llm

    def reflect(
        self,
        request: str,
        plan: Plan,
        result: ExecutionResult,
    ) -> ReflectionResult:
        """Evaluate the execution result against the original request and plan."""
        logger.info("Reflector: Reviewing generated content for quality...")

        # Format generated content for the review prompt
        content_summary = self._format_content(result)
        planned_sections = ", ".join(t.title for t in plan.tasks)

        prompt = REFLECTION_PROMPT_TEMPLATE.format(
            request=request,
            doc_type=plan.document_type.value,
            doc_title=plan.document_title,
            planned_sections=planned_sections,
            assumptions="; ".join(plan.assumptions) if plan.assumptions else "None",
            generated_content=content_summary,
        )

        try:
            raw = self.llm.generate_json(
                prompt, 
                system_instruction=REFLECTION_SYSTEM_PROMPT,
                model=self.llm.light_model
            )

            reflection = ReflectionResult(
                passed=raw.get("passed", True),
                overall_score=max(1, min(10, raw.get("overall_score", 7))),
                feedback=raw.get("feedback", "No specific feedback."),
                missing_sections=raw.get("missing_sections", []),
                improvement_suggestions=raw.get("improvement_suggestions", []),
            )

            status = "PASSED" if reflection.passed else "NEEDS REVISION"
            logger.info(
                f"   {status} | Score: {reflection.overall_score}/10 | "
                f"{reflection.feedback[:100]}..."
            )

            if reflection.missing_sections:
                logger.info(f"   Missing sections: {reflection.missing_sections}")
            if reflection.improvement_suggestions:
                for s in reflection.improvement_suggestions:
                    logger.info(f"   Suggestion: {s}")

            return reflection

        except Exception as e:
            logger.error(f"Reflection failed: {e}")
            # Default to passing if reflection itself fails
            return ReflectionResult(
                passed=True,
                overall_score=6,
                feedback=(
                    f"Reflection could not be completed: {e}. "
                    "Proceeding with current content."
                ),
                missing_sections=[],
                improvement_suggestions=[],
            )

    @staticmethod
    def _format_content(result: ExecutionResult) -> str:
        """Format execution result sections into a readable string for the LLM."""
        parts: list[str] = []
        for i, section in enumerate(result.sections, 1):
            part = f"--- Section {i}: {section.heading} ---\n{section.body}"
            if section.bullet_points:
                bullets = "\n".join(f"  - {bp}" for bp in section.bullet_points)
                part += f"\nKey Points:\n{bullets}"
            if section.table_data:
                part += f"\n[Table with {len(section.table_data)} rows]"
            parts.append(part)
        return "\n\n".join(parts)
