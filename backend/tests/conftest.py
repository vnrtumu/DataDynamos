"""Test fixtures. Redirects storage + DB to a throwaway temp dir before app import."""

import os
import tempfile
from pathlib import Path

# Must run before any `app.*` import so app.config.settings picks up the temp dir.
_TMP_DATA = tempfile.mkdtemp(prefix="doc-approval-tests-")
os.environ["DATA_DIR"] = _TMP_DATA

BACKEND_ROOT = Path(__file__).resolve().parent.parent
SAMPLES = BACKEND_ROOT / "samples"
