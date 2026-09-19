"""Celery tasks for automatic candidate discovery (§19, §20, §57)."""

from datetime import datetime, timezone
import logging

from ..agents.graph import run_discovery
from ..extensions import db
from ..models import MatchRun, RoleCandidate
from . import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="discovery.run")
def run_discovery_task(role_id: str, run_id: str = None) -> dict:
    logger.info("Candidate discovery running for role %s (run %s)", role_id, run_id)
    from .. import create_app
    app = create_app()

    with app.app_context():
        def update_progress(stage: str):
            if not run_id:
                return
            try:
                run = MatchRun.query.filter_by(id=run_id).first()
                if run:
                    run.current_stage = stage
                    if stage == "Analyzing employee profiles":
                        run.progress = 20
                    elif stage == "Finding transferable skills":
                        run.progress = 40
                    elif stage == "Scoring candidates":
                        run.progress = 65
                    elif stage == "Generating explanations":
                        run.progress = 85
                    elif stage == "Completed":
                        run.progress = 100
                        run.status = "completed"
                        run.completed_at = datetime.now(timezone.utc)
                        run.candidates_count = RoleCandidate.query.filter_by(role_id=role_id).count()
                    db.session.commit()
            except Exception as e:
                logger.warning("Error updating progress: %s", e)

        try:
            update_progress("Analyzing employee profiles")
            result = run_discovery(role_id, on_progress=update_progress)
            update_progress("Completed")
            logger.info("Candidate discovery completed for role %s", role_id)
            return {"status": "completed", "role_id": role_id}
        except Exception as exc:
            logger.error("Discovery failed: %s", exc, exc_info=True)
            if run_id:
                try:
                    run = MatchRun.query.filter_by(id=run_id).first()
                    if run:
                        run.status = "failed"
                        run.current_stage = f"Error: {str(exc)[:100]}"
                        db.session.commit()
                except Exception:
                    pass
            return {"status": "failed", "error": str(exc)}
