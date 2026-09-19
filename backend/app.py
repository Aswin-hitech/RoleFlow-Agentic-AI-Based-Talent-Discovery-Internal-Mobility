"""RoleFlow — Primary Backend Executable Entry Point.

app.py is our main source for the RoleFlow backend.

Run API:
    python app.py
"""

import os
from core import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=app.config.get("DEBUG", True))
