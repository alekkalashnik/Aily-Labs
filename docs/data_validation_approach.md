# Data Validation Approach — Without Direct API Access

**Companion document to:** [Test Strategy](./test_strategy.md)
**Target:** Grafana Synthetic Monitoring App Demo (`play.grafana.org`, anonymous viewer)

---

## The challenge

The Grafana Synthetic Monitoring dashboard displays values that change every few seconds:
latency readings, uptime percentages, "checks up" counters, and probe heartbeats. We have
no API credentials, no database access, and no ability to seed deterministic test data.

Asserting that latency equals 42 ms or that the checks list contains 17 rows will produce
a failing test on the very next run. The question this document answers is: **how do we
still get high-confidence data validation from a UI test against a live, shared demo?**

---

## Guiding principle: assert invariants, not values

An invariant is a relationship that must hold regardless of the specific numbers shown.
"Every card after filtering by HTTP must have Type = HTTP" is an invariant — it is true
whether there are 2 HTTP checks or 200. "The checks list has 17 rows" is not — it is
only true at a specific moment in time.

Invariants are robust to dynamic data and still catch real regressions. A bug that swaps
the Type and Name fields, renders `NaN` instead of a percentage, or silently drops half
the rows will break an invariant. A bug that changes a latency value from 41 ms to 43 ms
will not, and that is correct — that is not a regression.

---

## Validation techniques

The following techniques are used individually or in combination depending on the scenario.

### Structural / schema assertions

Every rendered value must conform to a declared shape. We don't care what the uptime
percentage is today, but we care that it looks like a percentage. A bug that replaces
a formatted number with a raw object reference, a NaN, or an empty string is caught
immediately by a regex check.

| Field       | Expected shape                                                                           |
|-------------|------------------------------------------------------------------------------------------|
| Check Type  | One of: `HTTP`, `PING`, `DNS`, `TCP`, `TRACEROUTE`, `MULTIHTTP`, `SCRIPTED`, `BROWSER`  |
| Latency     | Matches `^\d+(\.\d+)?\s?ms$`                                                             |
| Uptime      | Matches `^\d+(\.\d+)?%$` and the numeric value falls in `[0, 100]`                       |
| Frequency   | Matches `^\d+\s?(s|m|h)$`                                                                |
| Probe state | One of: `Online`, `Offline`                                                              |

In practice, we implement this as enum membership checks (`type in KNOWN_CHECK_TYPES`)
or Playwright's built-in text matchers (`expect(locator).to_have_text(re.compile(...))`).

### Filter self-consistency

When a filter is applied, every visible result must satisfy the filter condition — no
exceptions, no partial matches. This catches both backend bugs (the API returning the
wrong results) and frontend bugs (the UI rendering unfiltered data after a filter was set).

The search scenario already implements this: after typing a search term, we assert that
every visible card's text contains that term. The planned type-filter scenario (CL-05)
will do the same: after selecting "HTTP", every visible card must show Type = HTTP.

We also assert that the filtered count is less than or equal to the original count.
Filtering should narrow the set, never expand it.

### Cross-view consistency

Numbers that appear in multiple places should agree. The home page might show "N checks"
in a summary tile; the Checks list should show N cards when unfiltered. A discrepancy
points to either a caching issue, a rendering bug, or a stale aggregate.

Other examples of cross-view checks we plan to implement:

- Probes summary count on Home → total probe count on the Probes page
- Check name in the Checks list → heading on the Check detail page
- "Last run" timestamp on the list view → "last success" on the detail view for the same check

### Aggregation invariants

Where the UI shows a total alongside a breakdown, the breakdown should sum to the total.
If the Overview chart shows 5 HTTP checks, 3 DNS checks, and 2 PING checks, the total
check count should be 10. When it is not, something is wrong — either the aggregation
query is incorrect or the rendering is truncating results.

The implementation is straightforward: parse each numeric value from the DOM, then assert
`sum(per_type_counts) == total_count`.

### Ordering invariants

When the user sorts a column, the rendered order must be monotone. If sorted ascending by
name, `rows == sorted(rows)`. If sorted descending by last run, timestamps must be
non-increasing. The current Checks view uses cards rather than a sortable table, so this
technique applies to any future tabular view that exposes sort controls.

### Time-range monotonicity

A narrower time range must produce a sample count less than or equal to a wider range
that contains it. If we see 50 data points over the last 6 hours, we should not see 70
data points over the last 15 minutes — that would mean data is appearing from outside
the requested window.

This is one of the more interesting invariants because it gives us a meaningful signal
about query correctness without knowing any specific expected values.

### Refresh idempotence

Applying the same filter and time range twice in quick succession should produce
structurally identical results. Metric values may drift slightly between queries
(one probe cycle's worth of data), so we apply a tolerance of 5% for numeric
comparisons rather than requiring exact equality.

This catches bugs where a second render reads from a stale cache, applies a different
default, or re-initialises a filter state incorrectly.

### Deep-link and URL invariants

A URL like `/checks?type=http` should load with the HTTP filter already applied — the
query parameter should be reflected in the filter UI. We assert that the filter control's
selected value matches the query parameter, not that specific cards are present.

---

## Using the browser's own network traffic as a ground-truth channel

We have no API credentials — but the browser already calls the Grafana backend on every
page load, and Playwright lets us observe those calls without interfering with them.

```python
@pytest.fixture
def response_recorder(page: Page) -> list[ResponseRecord]:
    records: list[ResponseRecord] = []

    def on_response(resp: Response) -> None:
        if "/api/" in resp.url and resp.request.resource_type in {"xhr", "fetch"}:
            records.append(ResponseRecord(url=resp.url, status=resp.status, json=try_json(resp)))

    page.on("response", on_response)
    yield records
```

By hooking into the page's response events, each test run also gives us:

- **Status code sanity** — no 5xx responses on the critical path
- **Payload vs DOM consistency** — the `count` field in the JSON response matches the
  number of cards rendered on screen
- **Refresh verification** — a manual refresh actually triggers a new network request,
  not just a re-render from cached state
- **Navigation correctness** — the detail view request includes the check ID from the
  row the user clicked on the list page

This is not API testing — we never craft requests ourselves or call the backend directly.
We only observe the traffic the application was already going to make. The test remains
a faithful UI test, but with an additional signal channel that lets us catch a wider
class of data bugs.

---

## Visual regression testing — when and how

For UI elements that are stable across runs — the app logo, header layout, navigation
order, colour tokens — pixel-level screenshot comparison is a practical regression net.
Playwright's built-in `expect(page).to_have_screenshot()` handles this.

The critical rule: **mask every volatile region** before taking the baseline. Metric
panels, timestamps, sparklines, and any element driven by live data must be masked,
or the baseline will be stale after the first data refresh. We screenshot the chrome,
not the content.

We do not compare screenshots of live chart panels. The signal-to-noise ratio is too
low and the baseline maintenance cost is too high.

---

## Managing flakiness on a shared demo

The shared demo introduces a specific kind of noise that a private test environment does
not have. The table below describes the patterns we have seen and how we handle each one.

| Symptom                                           | Approach                                                                                   |
|---------------------------------------------------|--------------------------------------------------------------------------------------------|
| Auto-refreshing metric breaks an equality check   | Replace with regex, range check, or tolerance window — never `==` on a live metric        |
| A check is added or removed during the test run   | Read counts immediately before and after the action; never cache a count across steps      |
| SPA takes time to hydrate after navigation        | Wait on a semantic landmark with `expect(...).to_be_visible()` — never `wait_for_timeout`  |
| Backend latency spike causes a locator timeout    | Raise the global assertion timeout via `expect.set_options()` — do not add sleeps          |
| Demo dataset is temporarily missing a check type  | Use `pytest.skip` with an explanation rather than failing the run                          |
| A test is inherently unstable on the shared demo  | Mark with `@pytest.mark.quarantine` and exclude from required CI checks during investigation |

---

## What we deliberately avoid

- Asserting specific latency or uptime values — these change every few seconds
- Equality assertions against any counter that the app updates automatically
- Screenshot comparisons of live data panels
- Mocking the Grafana backend — we are testing a real deployed application, and a mock
  would only test our mock
- Re-implementing the Grafana API client inside the tests to fetch "authoritative" data —
  that requires credentials we don't have, and would effectively be rewriting the app

---

## How the implemented tests apply these techniques

The four automated scenarios use a combination of the approaches above without ever
asserting a literal value that depends on the current state of the demo.

| Scenario                   | Technique                                                                                     |
|----------------------------|-----------------------------------------------------------------------------------------------|
| Home smoke (SM-01 to SM-04)| Structural — page title is non-empty and contains "Grafana"; navigation landmark is visible; no error-level console messages |
| Checks list (CL-01, CL-02) | Structural — at least one card is present; every card has a non-empty name; every Type badge is in the documented enum |
| Search and filter (CL-03, CL-04) | Filter self-consistency — every visible card contains the search term after filtering; card count is restored after clearing |
