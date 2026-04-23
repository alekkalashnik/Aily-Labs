# Test Strategy — Grafana Synthetic Monitoring Dashboard

**Application under test:** [Grafana Synthetic Monitoring App](https://play.grafana.org/a/grafana-synthetic-monitoring-app/home)
**Environment:** `play.grafana.org` — anonymous viewer, shared public demo

---

## Scope and Objectives

The Grafana Synthetic Monitoring plugin gives teams an external-probe view of
their services: Checks (the endpoints being probed), Probes (the locations
doing the probing), latency and uptime dashboards, and alerting rules. This
strategy covers the UI of that plugin on the shared public demo, focusing on
what a read-only anonymous viewer can observe and interact with.

**What we cover:**

- Core pages: Home landing, Checks list, Check detail, Probes list
- Interactive controls: search, type filter, pagination, time-range picker, refresh
- Dynamic data rendering — cards, stat panels, and metric values
- Client-side routing — deep links, browser back/forward
- Cross-view data consistency (see [Data Validation Approach](./data_validation_approach.md))
- Key accessibility landmarks and responsive layout at desktop widths

**What we do not cover:**

- Write operations (create / edit / delete Checks) — the anonymous demo is read-only
- Authentication and authorisation flows
- Alert notification delivery — requires external integrations outside this demo
- Backend data validation via direct API calls — no credentials are available on `play.grafana.org`
- Load, stress, or performance benchmarking

---

## Risks and Mitigations

**Shared, uncontrolled environment.** Data, layout, and feature flags on `play.grafana.org`
can change without notice. We address this by writing structural and enum-based assertions
rather than asserting exact values — if the number of checks changes overnight, our tests
don't care, but if a card stops rendering a Type badge entirely, they will catch it.

**Constantly refreshing metrics.** Latency numbers, uptime percentages, and probe heartbeats
update every few seconds. Assertions against specific numbers are guaranteed to be flaky.
We instead assert against regex patterns and invariant relationships (filtered count ≤ total
count, sum of parts equals total, etc.).

**SPA loading behaviour.** Grafana renders entirely on the client — the initial HTML response
is nearly empty. We wait on meaningful app-shell landmarks (the nav toolbar, the page breadcrumb)
rather than relying on `networkidle` or arbitrary timeouts.

**No control over seed data.** We cannot create deterministic test data, so we choose
assertions that are robust against any valid, non-empty dataset. A test that requires exactly
17 checks in a specific order would be brittle; one that requires at least 1 check with a
valid Type badge is reliable.

---

## Approach

We prioritise tests by risk. Smoke tests (P0) confirm the app is reachable and the core views
render without errors — these run on every commit and must pass before anything else matters.
Primary journey tests (P1) cover the key user interactions: browsing checks, filtering, drilling
into a detail view, and reviewing probes. Edge cases and cross-cutting concerns (P2) round out
the suite once the critical paths are stable.

For data assertions, we follow one rule consistently: **assert the shape of data, not its
current value**. A value that is guaranteed to change is a guaranteed flake. The Type field
on a check card should always be one of a known set of strings — that relationship holds
regardless of demo state. We assert that, not "the third card says HTTP".

On the automation side, we use Playwright's built-in auto-retry assertions everywhere
(`expect(locator).to_be_visible()`, `to_have_count()`, `to_have_text()`). Explicit sleeps
and `wait_for_timeout` are banned — if an assertion needs a sleep to pass, it means we are
waiting on the wrong signal.

Every test navigates independently from scratch. There is no shared UI state between tests,
which eliminates a whole class of ordering-dependent failures on a shared demo environment.

---

## Tooling

| Concern            | Choice                                                           |
|--------------------|------------------------------------------------------------------|
| Language           | Python 3.12                                                      |
| Test runner        | Pytest 8.x                                                       |
| Browser automation | Playwright 1.58 (sync API) + pytest-playwright                   |
| Base URL           | pytest-base-url (`base_url` in `pytest.ini`)                     |
| Test pattern       | Page Object Model with BDD (Gherkin `.feature` files via pytest-bdd) |
| Reporting          | Allure (allure-pytest) — local and CI                            |
| Browser            | Chromium                                                         |
| Viewport           | 1440 × 900                                                       |

**Getting started:**

```bash
pip install -r requirements.txt
playwright install chromium
pytest --headed -ra
```

### How the test suite is structured

Scenarios are written as Gherkin `.feature` files under `features/`. Step definitions live
under `tests/steps/`, one module per page, each delegating directly to a POM method with no
logic in the step itself. A single `tests/test_features.py` collects every scenario in
`features/` via `pytest_bdd.scenarios()` — adding a new `.feature` file is enough to have
it picked up automatically, no new Python wrapper needed.

Feature tags (`@smoke`, `@P0`, `@critical`, `@navigation`, etc.) are registered as pytest
markers in `pytest.ini`, so you can run any subset with `-m`. Every POM action method is
wrapped with `@allure.step`, giving the Allure report a readable step-by-step trace rather
than a single opaque pass/fail per scenario.

### Artifacts produced on every run

These are configured in `pytest.ini` — nothing extra needs to be passed on the command line.

| Output                | Path                                           | When           |
|-----------------------|------------------------------------------------|----------------|
| Allure raw results    | `allure-results/`                              | Always         |
| Playwright video      | `test-results/*/video.webm`                    | On failure     |
| Playwright trace      | `test-results/*/trace.zip`                     | On failure     |

View the report locally:

```bash
# Quick live view (requires allure CLI):
allure serve allure-results

# Or generate a static site:
allure generate allure-results --clean -o allure-report
```

### CI pipeline

The workflow in `.github/workflows/tests.yml` runs on every push and pull request. It installs
Python 3.12, pip-cached dependencies, and Chromium headlessly. After the test run, it generates
a static Allure report and deploys it to GitHub Pages, carrying forward the trend history from
the previous run so the charts span multiple builds. Raw Allure results are also uploaded as a
workflow artifact (retained 30 days), and Playwright failure artifacts (video, trace) are
uploaded when the job fails.

---

## Test Scenario Catalogue

**Priority:** P0 blocker · P1 primary user journey · P2 edge case
**Type:** F functional · D data / invariant · X cross-cutting · N negative
**Status:** ✅ automated · ⚪ planned

### Smoke (P0)

| ID    | Scenario                                                              | Priority | Type | Status |
|-------|-----------------------------------------------------------------------|----------|------|--------|
| SM-01 | App home loads and the Synthetic Monitoring navigation is visible     | P0       | F    | ✅     |
| SM-02 | SM sub-nav shows Checks, Probes, Alerts (Legacy), and Config entries  | P0       | F    | ✅     |
| SM-03 | No JavaScript error-level console messages on home page load          | P0       | X    | ✅     |
| SM-04 | Page title tag contains "Grafana"                                     | P0       | F    | ✅     |

### Checks list (P0 / P1)

The Synthetic Monitoring plugin renders each check as a card
(`data-testid="check-card"`) rather than a table row, so "row count" below means card count.

| ID    | Scenario                                                                                                             | Priority | Type | Status |
|-------|----------------------------------------------------------------------------------------------------------------------|----------|------|--------|
| CL-01 | Checks page renders at least one check card                                                                          | P0       | F    | ✅     |
| CL-02 | Every card has a non-empty name and a Type badge in the documented enum                                              | P0       | D    | ✅     |
| CL-03 | Free-text search narrows the card set — every remaining card contains the term, count ≤ initial                      | P0       | D    | ✅     |
| CL-04 | Clearing the search box restores the original card count                                                             | P0       | D    | ✅     |
| CL-05 | Type filter under "Additional filters" narrows cards and every remaining card's Type matches the selection           | P1       | D    | ⚪     |
| CL-06 | A search term with zero matches shows an empty state, not an error                                                   | P1       | F    | ⚪     |
| CL-07 | Pagination navigates to the next page without losing active filters                                                  | P2       | F    | ⚪     |

### Check detail (P1)

Panels verified on `/checks/{id}/dashboard`: Uptime, Reachability, Average latency,
Frequency, Error rate by probe, and Duration by probe.

| ID    | Scenario                                                                                              | Priority | Type | Status |
|-------|-------------------------------------------------------------------------------------------------------|----------|------|--------|
| CD-01 | Detail page heading matches the check name selected from the list                                     | P1       | F    | ⚪     |
| CD-02 | Uptime and Reachability show values matching `^\d+(\.\d+)?%$`; latency matches `^\d+(\.\d+)?ms$`     | P1       | D    | ⚪     |
| CD-03 | Changing the time-range picker re-queries panels; the same panels remain visible after the change     | P1       | F    | ⚪     |
| CD-04 | Manual refresh triggers a new network request to the backend                                          | P1       | D    | ⚪     |

### Probes (P1)

| ID    | Scenario                                                                                     | Priority | Type | Status |
|-------|----------------------------------------------------------------------------------------------|----------|------|--------|
| PR-01 | Probes page renders entries under "Public Probes", each with a name and per-probe stats      | P1       | F    | ⚪     |
| PR-02 | Each probe shows check-runs/min and failed-runs/min values matching `^\d+(\.\d+)?$`          | P1       | D    | ⚪     |

### Cross-cutting (P2)

| ID    | Scenario                                                                        | Priority | Type | Status |
|-------|---------------------------------------------------------------------------------|----------|------|--------|
| CC-01 | Deep link `/checks?type=http` loads with the HTTP filter pre-applied            | P2       | F    | ⚪     |
| CC-02 | Browser back/forward preserves applied filters                                  | P2       | F    | ⚪     |
| CC-03 | Layout remains usable at 1280, 1024, and 768 px widths                          | P2       | X    | ⚪     |
| CC-04 | Page has a `<main>` landmark and a single `h1`                                  | P2       | X    | ⚪     |

### Negative (P2)

| ID    | Scenario                                                                                   | Priority | Type | Status |
|-------|--------------------------------------------------------------------------------------------|----------|------|--------|
| NG-01 | A nonsense search term yields an empty state without breaking the UI                       | P2       | N    | ⚪     |
| NG-02 | A time range before any data shows a "no data" panel state without JavaScript errors       | P2       | N    | ⚪     |
| NG-03 | A filter combination that yields zero results handles gracefully                           | P2       | N    | ⚪     |

---

## Entry and Exit Criteria

The test run should only begin once the demo URL is reachable from the runner, anonymous
read access to the Synthetic Monitoring plugin is confirmed, and the local environment
(Python 3.12 venv + Playwright Chromium) is installed.

We consider a cycle complete when all P0 scenarios pass, there are no new flakes across
three consecutive runs on CI, and there are no unresolved blocker defects.

---

## What is automated and why

The four scenarios in this repo cover the checks list, free-text search, SM navigation,
and the home page smoke check. They were chosen because they exercise dynamic content,
interactive controls, and data-driven assertions simultaneously, and because they are
stable on a shared read-only demo — no seed data required, no write operations, no
authentication.

The remaining scenarios in the catalogue above represent the natural backlog. Most are
deferred because they require either writable test data (which the anonymous demo does
not support), API-level ground truth (no credentials available), or because the shared
environment introduces too much variability to make them reliable without quarantining.
Once access to a dedicated environment or API credentials is available, the P1 scenarios
in particular are straightforward to automate against the existing POM structure.
