"""RoleFlow — Single Backend Executable Entry Point.

Run API:
    python app.py

Run Celery worker:
    celery -A app.celery_app worker --loglevel=info
"""

import os
from core import create_app
from core.tasks import celery_app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=app.config.get("DEBUG", True))
