"""Vercel entry point for the CardWise FastAPI application."""
import os
import sys
from pathlib import Path

# Make the existing backend package importable when the project is deployed
# from the repository root.
BACKEND_DIR = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# Never expose CardWise using the committed development signing key.
if not os.environ.get("SECRET_KEY"):
    raise RuntimeError(
        "CardWise is not configured: set a strong SECRET_KEY in Vercel "
        "Project Settings > Environment Variables before deploying."
    )

# This fallback allows a temporary preview if a DATABASE_URL has not yet
# been supplied. /tmp storage is ephemeral; configure managed PostgreSQL
# before using CardWise with any real account or financial data.
os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/cardwise-preview.db")

from app.main import app  # noqa: E402
