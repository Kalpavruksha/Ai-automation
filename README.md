# 🤖 Autonomous AI Agent — Document Generator

An autonomous AI agent built with **FastAPI** and **Google Gemini** that accepts natural language requests, autonomously plans and executes tasks, and produces polished Microsoft Word (.docx) documents.

## 🏗️ Architecture

```
User Request (JSON)
       │
       ▼
┌──────────────┐
│  POST /agent │  ◄── FastAPI Endpoint
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   PLANNER    │  ◄── Analyzes request, determines doc type,
│  (Gemini)    │      makes assumptions, creates task list
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   EXECUTOR   │  ◄── Generates content for each section
│  (Gemini)    │      via structured LLM calls
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  REFLECTOR   │  ◄── Self-check: reviews quality, completeness,
│  (Gemini)    │      tone, structure (scores 1-10)
└──────┬───────┘
       │
  ┌────┴────┐
  │ Pass?   │
  ├── Yes ──┤
  │         ▼
  │   ┌──────────┐
  │   │ DOCUMENT │  ◄── python-docx: title page, styled
  │   │GENERATOR │      sections, tables, bullets, footer
  │   └────┬─────┘
  │        │
  ├── No ──┤
  │        ▼
  │  ┌───────────┐
  │  │  REVISION │  ◄── Targeted rewrite using reflection
  │  │ (Gemini)  │      feedback, then re-reflect
  │  └─────┬─────┘
  │        │
  │        ▼
  │   ┌──────────┐
  │   │ DOCUMENT │
  │   │GENERATOR │
  │   └────┬─────┘
  │        │
  └────────┘
       │
       ▼
  JSON Response + .docx Download URL
```

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| API | FastAPI + Uvicorn |
| LLM | Google Gemini 2.0 Flash (via `google-genai`) |
| Document Generation | python-docx |
| Data Validation | Pydantic v2 |
| Logging | Loguru |
| Config | python-dotenv |

## ⚡ Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

Edit `.env` and replace the placeholder:

```
GEMINI_API_KEY=your-actual-gemini-api-key
```

### 3. Run the Server

```bash
python main.py
# or
uvicorn main:app --reload --port 8000
```

### 4. Test It

```bash
# Standard business request
curl -X POST http://localhost:8000/agent \
  -H "Content-Type: application/json" \
  -d '{"request": "Create a project proposal for developing a mobile app for a local restaurant chain that wants to offer online ordering and loyalty rewards."}'

# Complex/ambiguous request
curl -X POST http://localhost:8000/agent \
  -H "Content-Type: application/json" \
  -d '{"request": "Our team is struggling with productivity and we had some kind of meeting about it last week. Can you put together something that captures what we discussed and what we should do next? I think we talked about maybe using new tools or restructuring the workflow. Not sure about the details."}'
```

### 5. Download the Document

Use the `document_download_url` from the response:

```bash
curl -O http://localhost:8000/documents/<filename>.docx
```

Or open `http://localhost:8000/docs` for the interactive Swagger UI.

---

## 🔧 Engineering Improvement: Multi-Step Planning with Reflection/Self-Check

### What
After the executor generates all document sections, the **Reflector** agent reviews the complete output against the original request and execution plan. It evaluates:
- **Completeness** — Are all planned sections present and thorough?
- **Accuracy** — Is content realistic and internally consistent?
- **Tone** — Does the style match the document type?
- **Structure** — Are sections logically ordered?
- **Depth** — Is there enough detail to be useful?

If the score is below 7/10, the agent **automatically revises** all sections using the reflection feedback, then re-evaluates.

### Why I Chose This
For a document generation agent, **output quality is the most critical factor**. A plan-execute pipeline alone often produces content that's technically complete but lacks coherence, misses nuances from the original request, or has inconsistent tone. The reflection step catches these issues automatically — mimicking how a human writer would draft, review, and revise.

### How It Improves the Agent
1. **Self-correcting** — Catches and fixes quality issues without human intervention
2. **Transparent** — Quality scores and feedback are included in the API response AND the generated document
3. **Bounded** — Maximum 1 revision cycle to prevent infinite loops while still improving output
4. **Graceful degradation** — If reflection itself fails, the agent proceeds with the original content rather than crashing

---

## 🧪 Two Test Inputs

### Test 1: Standard Business Request
```json
{
  "request": "Create a project proposal for developing a mobile app for a local restaurant chain that wants to offer online ordering and loyalty rewards."
}
```
**What the agent does:** Identifies this as a `proposal`, creates ~6 tasks (executive summary, objectives, scope, timeline, budget, next steps), generates professional content with realistic mock data, and produces a formatted proposal document.

### Test 2: Complex / Ambiguous Request
```json
{
  "request": "Our team is struggling with productivity and we had some kind of meeting about it last week. Can you put together something that captures what we discussed and what we should do next? I think we talked about maybe using new tools or restructuring the workflow. Not sure about the details."
}
```
**What the agent does:** Identifies this as `meeting_minutes`, makes explicit assumptions (meeting date, attendees, specific tools discussed), generates inferred discussion points and action items, and documents its assumptions prominently in the output. This demonstrates autonomous decision-making when information is incomplete.

---

## ⚖️ Engineering Tradeoff: Simplicity vs. Extensibility

### The Tradeoff
I chose a **simple sequential pipeline** (Plan → Execute → Reflect → Generate) over a more extensible architecture like LangGraph state machines or multi-agent orchestration.

### Why Simplicity Won
- **60-minute time constraint** — A sequential pipeline is faster to build, test, and debug
- **Single responsibility** — Each component has one clear job, making the code easy to understand
- **Predictable execution** — No complex state transitions, no agent-to-agent communication failures
- **Sufficient for the use case** — Document generation is inherently sequential (outline → write → review)

### What I'd Change With More Time
- **LangGraph** for stateful workflows with branching (e.g., research → draft → review → approve)
- **Tool calling** to fetch real data (project management APIs, calendar, existing docs)
- **Streaming responses** via WebSocket for real-time progress updates
- **Multi-agent architecture** — separate specialist agents for research, writing, formatting, and review
- **Conversation memory** — maintain context across requests for iterative document refinement

---

## 📁 Project Structure

```
├── main.py                 # FastAPI app with POST /agent endpoint
├── agent/
│   ├── __init__.py
│   ├── models.py           # Pydantic data models
│   ├── llm.py              # Gemini LLM client wrapper
│   ├── planner.py          # Request analysis & task planning
│   ├── executor.py         # Task execution & content generation
│   ├── reflector.py        # Quality review & self-check
│   └── document.py         # Word document generation
├── output/                 # Generated .docx files
├── logs/                   # Application logs
├── requirements.txt
├── .env                    # API key configuration
└── README.md
```

## 📝 API Reference

### `POST /agent`
**Request:**
```json
{
  "request": "Your natural language request (10-5000 chars)"
}
```

**Response:**
```json
{
  "status": "success",
  "original_request": "...",
  "plan": {
    "document_type": "proposal",
    "document_title": "...",
    "summary": "...",
    "assumptions": ["..."],
    "tasks": [{"step_number": 1, "title": "...", "description": "...", "status": "completed"}]
  },
  "execution_log": ["Step 1: Generating '...'", "Step 1: ✅ Completed '...'"],
  "reflection": {
    "passed": true,
    "overall_score": 8,
    "feedback": "...",
    "missing_sections": [],
    "improvement_suggestions": ["..."]
  },
  "document_filename": "Project_Proposal_20250917_120000.docx",
  "document_download_url": "/documents/Project_Proposal_20250917_120000.docx"
}
```

### `GET /documents/{filename}`
Downloads the generated `.docx` file.

### `GET /health`
Returns `{"status": "healthy", "timestamp": "..."}`.
https://ai-automation-bztm.onrender.com/
