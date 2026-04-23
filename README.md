# Grafana Synthetic Monitoring — UI Test Suite

[![Synthetic Monitoring Tests](https://github.com/alekkalashnik/Aily-Labs/actions/workflows/tests.yml/badge.svg)](https://github.com/alekkalashnik/Aily-Labs/actions/workflows/tests.yml)

This repository contains end-to-end UI tests for the [Grafana Synthetic Monitoring plugin](https://play.grafana.org/a/grafana-synthetic-monitoring-app/home) running on the public `play.grafana.org` demo. The plugin gives teams an external-probe view of their services — Checks, Probes, latency dashboards, and alerting rules. The tests run against the anonymous read-only demo, so no credentials or test data setup is required.

The live Allure report is published to GitHub Pages after every push to `main`:
[alekkalashnik.github.io/Aily-Labs](https://alekkalashnik.github.io/Aily-Labs/)

---

## Technology stack

| Concern            | Choice                                                           |
|--------------------|------------------------------------------------------------------|
| Language           | Python 3.12                                                      |
| Test runner        | Pytest 8                                                         |
| Browser automation | Playwright 1.58 (sync API)                                       |
| BDD layer          | pytest-bdd (Gherkin `.feature` files)                            |
| Design pattern     | Page Object Model                                                |
| Reporting          | Allure (deployed to GitHub Pages)                                |
| Browser            | Chromium                                                         |

---

## Project structure

```
features/               # Gherkin scenarios — the human-readable spec
  home_smoke.feature
  checks_list.feature
  checks_search_and_filter.feature

pages/                  # Page Object Model — all page logic lives here
  base_page.py
  home_page.py
  checks_page.py

tests/
  steps/                # Step definitions — thin glue to POM methods
    home_steps.py
    checks_steps.py
  conftest.py           # Fixtures and step module registration
  test_features.py      # Single entry point that loads all feature files

docs/
  test_strategy.md            # Scope, scenario catalogue, approach, and tooling
  data_validation_approach.md # How to assert correctness without API access

.github/workflows/
  tests.yml             # CI: run tests and publish Allure report to GitHub Pages
```

---

## Local setup

**Prerequisites:** Python 3.12, Node.js (for the Allure CLI), Java 21 (for Allure report generation).

```bash
# Clone and enter the repo
git clone https://github.com/alekkalashnik/Aily-Labs.git
cd Aily-Labs

# Create a virtual environment and install Python dependencies
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install the Chromium browser
playwright install chromium

# Install the Allure CLI (one-time, macOS)
brew install openjdk@21
echo 'export PATH="/usr/local/opt/openjdk@21/bin:$PATH"' >> ~/.bash_profile
echo 'export JAVA_HOME="/usr/local/opt/openjdk@21"'      >> ~/.bash_profile
source ~/.bash_profile
npm install -g allure-commandline
```

---

## Running the tests

```bash
# Run the full suite headlessly
pytest -ra

# Run headed — useful when debugging or inspecting selector behaviour
pytest --headed -ra

# Run only P0 smoke scenarios
pytest -m smoke --headed

# Run only blocker-severity scenarios
pytest -m blocker --headed
```

---

## Viewing the Allure report

**Online** — the report is updated automatically after every push to `main`:
[alekkalashnik.github.io/Aily-Labs](https://alekkalashnik.github.io/Aily-Labs/)

**Locally** — after running the tests, launch an interactive report server:

```bash
allure serve allure-results
```

Or generate a static site to open in your browser:

```bash
allure generate allure-results --clean -o allure-report
open allure-report/index.html
```

---

## CI/CD

Every push to `main` and every pull request triggers the GitHub Actions workflow. It installs
Python 3.12, dependencies, and Chromium, then runs the full suite headlessly. After the run
it carries forward the Allure trend history from the previous deployment, publishes the updated
report to GitHub Pages, and uploads Playwright failure artifacts (video, trace) when the job fails.

See [`.github/workflows/tests.yml`](.github/workflows/tests.yml) for the full configuration.

---

## Further reading

- [Test Strategy](docs/test_strategy.md) — scope and objectives, risk mitigations, the full scenario catalogue, and entry/exit criteria
- [Data Validation Approach](docs/data_validation_approach.md) — how we achieve meaningful data assertions against a live demo without API access or seed data
