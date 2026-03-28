"""Test runner path bootstrap for direct `python tests/...` execution.

Pytest already adds the repository root via `pytest.ini`, but editor helpers like
VS Code Code Runner may execute a test file directly from the `tests` directory.
In that mode, Python cannot resolve the top-level `app` package unless we add the
repository root to `sys.path`.
"""
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
root_str = str(ROOT)
if root_str not in sys.path:
    sys.path.insert(0, root_str)
