"""Single pytest entry point — loads every Gherkin scenario under features/.

pytest-bdd's `scenarios()` recursively discovers .feature files and
generates a pytest test per Scenario. Steps resolve via the modules in
[`tests/steps/`](steps/), registered in
[`tests/conftest.py`](conftest.py).
"""

from pytest_bdd import scenarios

scenarios("../features/")
