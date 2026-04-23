"""BDD fixtures + step-module registration.

Step definitions live under [`tests/steps/`](steps/) — one module per
page. Each is declared as a pytest plugin via `pytest_plugins` so its
@given/@when/@then registrations (which are pytest fixtures under the
hood) become visible to scenarios in this directory.

Add a new page by creating `tests/steps/<page>_steps.py` and appending
its dotted path to the list below.
"""

from __future__ import annotations

import pytest

pytest_plugins = [
    "tests.steps.home_steps",
    "tests.steps.checks_steps",
]


@pytest.fixture
def search_state() -> dict[str, object]:
    """Scratch-pad shared across When/Then steps within one scenario."""
    return {}
