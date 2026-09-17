"""
Centralized Prompt Templates for the Autonomous Agent Pipeline.

All LLM prompts are organized here by pipeline phase:
- Planning prompts
- Execution prompts
- Reflection prompts
- Revision prompts

Keeps agent logic classes clean and focused on orchestration.
"""


# ══════════════════════════════════════════════
#  PHASE 1: PLANNING
# ══════════════════════════════════════════════

PLANNING_SYSTEM_PROMPT = """\
You are an expert autonomous planning agent. Your job is to analyze a user's \
natural language request and produce a detailed execution plan for generating \
a professional business document.

RULES:
- Determine the most appropriate document type from: proposal, meeting_minutes, \
project_plan, business_report, technical_design, sop, product_spec, general.
- If the request is ambiguous or missing information, make reasonable business \
assumptions and list them explicitly.
- Break the work into 4-8 concrete tasks. Each task should map to a document section.
- Tasks must be ordered logically (e.g., executive summary first, conclusion last).
- Provide a clear, professional document title.
"""

PLANNING_PROMPT_TEMPLATE = """\
Analyze the following user request and create a structured execution plan.

USER REQUEST:
\"\"\"
{request}
\"\"\"

Respond with a JSON object matching this EXACT schema:
{{
  "document_type": "<one of: proposal, meeting_minutes, project_plan, \
business_report, technical_design, sop, product_spec, general>",
  "document_title": "<Professional document title>",
  "summary": "<Brief summary of what you understood from the request>",
  "assumptions": ["<assumption 1>", "<assumption 2>", ...],
  "tasks": [
    {{
      "step_number": 1,
      "title": "<Section/task title>",
      "description": "<What this task should produce>",
      "expected_output": "<Description of expected content>"
    }}
  ]
}}

Return ONLY valid JSON. No markdown, no explanation.
"""


# ══════════════════════════════════════════════
#  PHASE 2: EXECUTION
# ══════════════════════════════════════════════

EXECUTION_SYSTEM_PROMPT = """\
You are an expert business document writer. You are generating content for a \
specific section of a {doc_type} titled "{doc_title}".

CONTEXT:
- Document Type: {doc_type}
- Document Title: {doc_title}
- Overall Summary: {summary}
- Assumptions Made: {assumptions}

RULES:
- Write professional, clear, and well-structured content.
- Use concrete details, numbers, and specifics — use realistic mock data where needed.
- Be thorough but concise.
- Match the tone and style expected for a {doc_type}.
"""

EXECUTION_PROMPT_TEMPLATE = """\
Generate content for the following document section:

SECTION: {title}
DESCRIPTION: {description}
EXPECTED OUTPUT: {expected_output}

Respond with a JSON object matching this EXACT schema:
{{
  "heading": "<Section heading>",
  "body": "<Main paragraph content for this section. \
Use \\n for line breaks between paragraphs.>",
  "bullet_points": ["<point 1>", "<point 2>", ...],
  "table_data": null
}}

NOTES:
- "body" should be 2-5 paragraphs of professional content.
- "bullet_points" should contain 3-8 key points if appropriate, or an empty list.
- "table_data" should be a list of row-objects if a table makes sense for this \
section (e.g., timeline, budget, comparison), or null otherwise.
  Example: [{{"item": "Phase 1", "duration": "2 weeks", "cost": "$5,000"}}]
- Return ONLY valid JSON.
"""


# ══════════════════════════════════════════════
#  PHASE 2b: REVISION
# ══════════════════════════════════════════════

REVISION_PROMPT_TEMPLATE = """\
The following section content was reviewed and needs improvement.

ORIGINAL SECTION: {title}
CURRENT CONTENT:
{current_content}

REVIEWER FEEDBACK:
{feedback}

Please rewrite this section addressing the feedback. Respond with the same JSON schema:
{{
  "heading": "<Section heading>",
  "body": "<Improved paragraph content>",
  "bullet_points": ["<point 1>", ...],
  "table_data": null
}}

Return ONLY valid JSON.
"""


# ══════════════════════════════════════════════
#  PHASE 3: REFLECTION
# ══════════════════════════════════════════════

REFLECTION_SYSTEM_PROMPT = """\
You are a strict quality-assurance reviewer for professional business documents. \
Your job is to evaluate whether the generated content fully addresses the original \
user request and execution plan. Be honest and specific in your feedback.
"""

REFLECTION_PROMPT_TEMPLATE = """\
Review the following document content against the original request and plan.

ORIGINAL USER REQUEST:
\"\"\"{request}\"\"\"

EXECUTION PLAN SUMMARY:
- Document Type: {doc_type}
- Document Title: {doc_title}
- Planned Sections: {planned_sections}
- Assumptions: {assumptions}

GENERATED CONTENT (section-by-section):
{generated_content}

EVALUATION CRITERIA:
1. COMPLETENESS: Does the document cover all planned sections and the user's intent?
2. ACCURACY: Is the content realistic, professional, and internally consistent?
3. TONE: Does the writing style match the document type?
4. STRUCTURE: Are sections logically ordered with clear headings?
5. DEPTH: Is there enough detail to be useful (not just filler)?

Respond with a JSON object matching this EXACT schema:
{{
  "passed": <true if overall quality >= 7/10, false otherwise>,
  "overall_score": <integer 1-10>,
  "feedback": "<Specific overall feedback>",
  "missing_sections": ["<section name>", ...],
  "improvement_suggestions": ["<suggestion 1>", "<suggestion 2>", ...]
}}

Return ONLY valid JSON.
"""
