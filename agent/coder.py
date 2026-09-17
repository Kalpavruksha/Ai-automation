"""
Coder Agent — Generates executable code prototypes.
"""

from loguru import logger
from agent.llm import GeminiClient
from agent.models import Plan


class PrototypeGenerator:
    """Agent responsible for generating code prototypes (HTML/CSS) from a plan."""

    def __init__(self, llm: GeminiClient):
        self.llm = llm

    def generate_prototype(self, original_request: str, plan: Plan) -> str:
        """
        Generates a functional HTML/Tailwind CSS prototype landing page
        based on the user's original request and the generated plan.
        """
        system_prompt = (
            "You are an expert Frontend Web Developer. Your job is to create a beautiful, "
            "modern, and responsive single-file HTML landing page prototype based on the user's business idea.\n"
            "Use Tailwind CSS via CDN (<script src=\"https://cdn.tailwindcss.com\"></script>).\n"
            "Include a hero section, features section, and a sleek modern design.\n"
            "RETURN ONLY VALID HTML CODE. Do not include markdown fences like ```html."
        )

        prompt = f"""
        Original Request: {original_request}
        Document Title: {plan.document_title}
        Summary: {plan.summary}

        Please write the HTML code for this prototype.
        """

        logger.info("Generating code prototype using primary model...")
        
        try:
            # We use the primary model because writing code is a complex reasoning task
            raw_html = self.llm.generate(
                prompt,
                system_instruction=system_prompt,
                model=self.llm.primary_model
            )
            
            # Clean up markdown if the LLM still wrapped it
            cleaned_html = raw_html.strip()
            if cleaned_html.startswith("```html"):
                cleaned_html = cleaned_html[7:]
            if cleaned_html.startswith("```"):
                cleaned_html = cleaned_html[3:]
            if cleaned_html.endswith("```"):
                cleaned_html = cleaned_html[:-3]
                
            return cleaned_html.strip()
            
        except Exception as e:
            logger.error(f"Prototype generation failed: {e}")
            return f"<!-- Prototype generation failed: {e} -->"
