from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from learning_ecosystem.database import create_database
from learning_ecosystem.enums import ArtifactType, NodeType, ScopeStatus, SessionStatus
from learning_ecosystem.errors import NotFoundError
from learning_ecosystem.repository import LearningEcosystemRepository
from learning_ecosystem.seed import (
    CURRICULUM_ID,
    LEARNER_ID,
    NEXT_RECOMMENDED_OBJECTIVE,
    seed_pd1_poc,
)
from learning_ecosystem.tutor import TutorRuntime

ROOT = Path(__file__).parent
templates = Jinja2Templates(directory=str(ROOT / "templates"))


def create_app(database: str = "learning_ecosystem.db") -> FastAPI:
    connection = create_database(database)
    repo = LearningEcosystemRepository(connection)
    try:
        repo.get_curriculum(CURRICULUM_ID)
    except NotFoundError:
        seed_pd1_poc(repo)
    tutor = TutorRuntime(repo)

    app = FastAPI(title="Learning Ecosystem")
    app.state.repo = repo
    app.state.tutor = tutor
    app.mount("/static", StaticFiles(directory=str(ROOT / "static")), name="static")

    @app.get("/")
    def landing(request: Request):
        return templates.TemplateResponse(request, "landing.html", {"title": "Start"})

    @app.get("/learn")
    def learner_home(request: Request):
        resume = repo.load_resume_state(LEARNER_ID)
        sessions = repo.list_sessions(LEARNER_ID)
        concept_names = {c.id: c.canonical_name for c in repo.list_concepts()}
        states = [
            {
                "name": concept_names.get(state.concept_id, state.concept_id),
                "status": state.status.value,
            }
            for state in resume.concept_states
        ]
        active = next((item for item in sessions if item.status is SessionStatus.ACTIVE), None)
        return templates.TemplateResponse(request, "learner_home.html", {
                "request": request,
                "title": "Learn",
                "resume": resume,
                "sessions": sessions,
                "states": states,
                "next_objective": NEXT_RECOMMENDED_OBJECTIVE,
                "active": active,
            },
        )

    @app.post("/learn/start")
    def start_learning():
        turn = tutor.start_session(LEARNER_ID)
        return RedirectResponse(f"/learn/session/{turn.session_id}", status_code=303)

    @app.get("/learn/session/{session_id}")
    def live_session(request: Request, session_id: str):
        session = repo.get_session(session_id)
        working = tutor.working_state(session_id)
        node = repo.get_node(working.objective_node_id) if working else None
        concept = repo.get_concept(working.concept_id) if working else None
        live = session.status is SessionStatus.ACTIVE and working is not None
        snapshot = None
        if not live:
            snapshot = repo.session_close_snapshot(session_id)
        return templates.TemplateResponse(request, "session.html", {
                "request": request,
                "title": "Session",
                "session": session,
                "working": working,
                "node": node,
                "concept": concept,
                "live": live,
                "snapshot": snapshot,
            },
        )

    @app.post("/learn/session/{session_id}/reply")
    def reply(session_id: str, answer: str = Form(""), action: str = Form("answer")):
        text = answer
        if action == "stuck":
            text = "I don't know. I'm stuck."
        elif action == "explain":
            text = "Please explain it to me."
        elif not text.strip():
            return RedirectResponse(f"/learn/session/{session_id}", status_code=303)
        tutor.respond(session_id, text)
        return RedirectResponse(f"/learn/session/{session_id}", status_code=303)

    @app.post("/learn/session/{session_id}/close")
    def close(session_id: str):
        working = tutor.working_state(session_id)
        node = repo.get_node(working.objective_node_id) if working else None
        tutor.close_session(
            session_id,
            summary=f"Closed live session on {node.title if node else 'current objective'}.",
            takeaways=["Session closed from the learner UI."],
        )
        return RedirectResponse(f"/learn/session/{session_id}", status_code=303)

    @app.get("/admin")
    def admin_home(request: Request):
        nodes = repo.list_nodes(CURRICULUM_ID)
        concepts = repo.list_concepts()
        in_scope = [node for node in nodes if node.scope_status is ScopeStatus.IN_SCOPE]
        out_scope = [node for node in nodes if node.scope_status is ScopeStatus.OUT_OF_SCOPE]
        return templates.TemplateResponse(request, "admin.html", {
                "request": request,
                "title": "Curriculum",
                "curriculum": repo.get_curriculum(CURRICULUM_ID),
                "in_scope": in_scope,
                "out_scope": out_scope,
                "concepts": concepts,
                "topics": [node for node in in_scope if node.node_type is NodeType.TOPIC],
            },
        )

    @app.get("/admin/concepts/{concept_id}")
    def admin_concept(request: Request, concept_id: str):
        concept = repo.get_concept(concept_id)
        artifacts = repo.list_artifacts_for_concept(concept_id)
        sources = repo.list_sources_for_concept(concept_id)
        return templates.TemplateResponse(request, "admin_concept.html", {
                "request": request,
                "title": concept.canonical_name,
                "concept": concept,
                "artifacts": artifacts,
                "sources": sources,
                "artifact_types": [item.value for item in ArtifactType],
            },
        )

    @app.post("/admin/concepts/{concept_id}/artifacts")
    def add_artifact(
        concept_id: str,
        artifact_type: str = Form(...),
        content: str = Form(...),
        source_title: str = Form(...),
        source_url: str = Form(""),
        source_authority: str = Form("Salesforce"),
    ):
        source = repo.create_source(
            title=source_title,
            url=source_url or None,
            authority=source_authority,
        )
        repo.add_knowledge_artifact(
            concept_id=concept_id,
            artifact_type=ArtifactType(artifact_type),
            content=content,
            source_id=source.id,
            authority_level="authoritative" if source_authority == "Salesforce" else "derived",
        )
        return RedirectResponse(f"/admin/concepts/{concept_id}", status_code=303)

    return app
