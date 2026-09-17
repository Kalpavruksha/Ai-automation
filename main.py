"""
Autonomous AI Agent — FastAPI Application

POST /agent  → Accepts a natural language request, autonomously plans,
               executes, reflects, and generates a polished Word document.
GET  /documents/{filename} → Download a generated document.
GET  /health → Health check.
"""

from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from loguru import logger

from agent.document import DocumentGenerator
from agent.executor import TaskExecutor
from agent.llm import GeminiClient
from agent.models import AgentRequest, AgentResponse, TaskStatus
from agent.planner import AgentPlanner
from agent.reflector import Reflector
from agent.coder import PrototypeGenerator

# ──────────────────────────────────────────────
# Logging Configuration
# ──────────────────────────────────────────────

logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | <cyan>{message}</cyan>",
    level="INFO",
    colorize=True,
)

# In-memory log storage for real-time UI updates
RECENT_LOGS = ["System initialized. Waiting for request..."]

def ui_log_sink(message):
    msg = message.record["message"]
    # Filter out Uvicorn access logs so the UI only sees agent steps
    if "HTTP/1.1" not in msg and "GET /logs" not in msg:
        RECENT_LOGS.append(msg)
        if len(RECENT_LOGS) > 20:
            RECENT_LOGS.pop(0)

logger.add(ui_log_sink, level="INFO")

logger.add(
    "logs/agent_{time:YYYY-MM-DD}.log",
    rotation="10 MB",
    retention="7 days",
    level="DEBUG",
)


# ──────────────────────────────────────────────
# Application Lifespan — initialize shared resources
# ──────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize LLM client and agent components on startup."""
    logger.info("🚀 Starting Autonomous AI Agent...")
    try:
        app.state.llm = GeminiClient()
        app.state.planner = AgentPlanner(app.state.llm)
        app.state.executor = TaskExecutor(app.state.llm)
        app.state.reflector = Reflector(app.state.llm)
        app.state.coder = PrototypeGenerator(app.state.llm)
        app.state.doc_generator = DocumentGenerator()
        logger.info("✅ All agent components initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize agent: {e}")
        raise
    yield
    logger.info("👋 Shutting down Autonomous AI Agent")


# ──────────────────────────────────────────────
# FastAPI App
# ──────────────────────────────────────────────

app = FastAPI(
    title="Autonomous AI Agent",
    description=(
        "An autonomous agent that accepts natural language requests, "
        "generates execution plans, and produces polished Word documents."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────

@app.get("/")
def serve_frontend():
    """Serve the modern web UI."""
    return FileResponse("static/index.html")

@app.get("/logs")
def get_logs():
    """Returns the latest system logs for UI streaming."""
    return {"logs": RECENT_LOGS}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/agent", response_model=AgentResponse)
def run_agent(request: AgentRequest):
    """
    Main agent endpoint. Accepts a natural language request and returns
    a structured response with the generated Word document.

    Pipeline: Validate → Plan → Execute → Reflect → (Revise?) → Generate Document
    """
    logger.info(f"📨 New request received: '{request.request[:80]}...'")

    try:
        # ── Phase 1: PLAN ──
        logger.info("=" * 60)
        logger.info("PHASE 1: PLANNING")
        logger.info("=" * 60)
        plan = app.state.planner.create_plan(request.request)

        # ── Phase 2: EXECUTE ──
        logger.info("=" * 60)
        logger.info("PHASE 2: EXECUTION")
        logger.info("=" * 60)
        execution_result = app.state.executor.execute(plan)

        # ── Phase 3: REFLECT ──
        logger.info("=" * 60)
        logger.info("PHASE 3: REFLECTION (Self-Check)")
        logger.info("=" * 60)
        reflection = app.state.reflector.reflect(
            request.request, plan, execution_result
        )

        # ── Phase 3b: REVISE (if reflection fails) ──
        if not reflection.passed:
            logger.info("=" * 60)
            logger.info("PHASE 3b: REVISION (Addressing feedback)")
            logger.info("=" * 60)
            execution_result.execution_log.append(
                f"⚠️  Reflection score: {reflection.overall_score}/10 — Triggering revision..."
            )

            # Revise sections that need improvement
            revised_sections = []
            for section in execution_result.sections:
                revised = app.state.executor.revise_section(
                    plan, section, reflection.feedback
                )
                revised_sections.append(revised)

            execution_result.sections = revised_sections
            execution_result.execution_log.append("🔄 Revision complete")

            # Mark tasks as revised
            for task in plan.tasks:
                if task.status == TaskStatus.COMPLETED:
                    task.status = TaskStatus.REVISED

            # Re-reflect after revision
            reflection = app.state.reflector.reflect(
                request.request, plan, execution_result
            )
            execution_result.execution_log.append(
                f"🔍 Post-revision score: {reflection.overall_score}/10"
            )

        # ── Phase 4: PROTOTYPE GENERATION (The Wow Factor) ──
        logger.info("=" * 60)
        logger.info("PHASE 4: PROTOTYPE GENERATION")
        logger.info("=" * 60)
        prototype_html = app.state.coder.generate_prototype(request.request, plan)

        # ── Phase 5: GENERATE DOCUMENT ──
        logger.info("=" * 60)
        logger.info("PHASE 5: DOCUMENT GENERATION")
        logger.info("=" * 60)
        filename = app.state.doc_generator.generate(plan, execution_result, reflection)

        # Build response
        response = AgentResponse(
            status="success",
            original_request=request.request,
            plan=plan,
            execution_log=execution_result.execution_log,
            reflection=reflection,
            prototype_html=prototype_html,
            document_filename=filename,
            document_download_url=f"/documents/{filename}",
        )

        logger.info(f"🎉 Agent completed successfully! Document: {filename}")
        return response

    except Exception as e:
        logger.error(f"❌ Agent pipeline failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Agent execution failed",
                "message": str(e),
                "suggestion": "Check server logs for details.",
            },
        )


@app.get("/documents/{filename}")
def download_document(filename: str):
    """Download a generated Word document."""
    filepath = os.path.join(
        os.path.dirname(__file__), "output", filename
    )
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Document not found")

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@app.exception_handler(422)
async def validation_exception_handler(request, exc):
    """Custom handler for validation errors (e.g., request too short)."""
    return JSONResponse(
        status_code=422,
        content={
            "error": "Invalid request",
            "detail": str(exc),
            "suggestion": (
                "Please provide a detailed natural language request "
                "(10-5000 characters) describing the document you need."
            ),
        },
    )


# ──────────────────────────────────────────────
# Entrypoint
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    import os

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
