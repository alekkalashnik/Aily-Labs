"""Root conftest — shared fixtures + reporting hooks.

- `browser_context_args` is extended so that `page.goto("/relative")`
  resolves against `pytest-base-url`, and the viewport is 1440x900.
- `console_errors` collects `error`-level console messages (minus a
  whitelist of environmental noise) so tests can assert on them.
- `home_page` / `checks_page` inject pre-constructed Page Objects.
- `pytest_runtest_makereport` hook attaches the current page screenshot,
  page HTML and console log to the Allure report when a test fails, so
  triage does not require rerunning.
"""

from __future__ import annotations

from collections.abc import Generator, Iterator

import allure
import pytest
from playwright.sync_api import ConsoleMessage, Page, expect

from pages import ChecksPage, HomePage


# Known-benign console messages to ignore when asserting SM-03. These
# are noise from the shared public demo environment — not regressions
# in the Synthetic Monitoring plugin.
_CONSOLE_ERROR_WHITELIST: tuple[str, ...] = (
    "favicon",
    "ResizeObserver loop",
    "Failed to preload plugin",
    "Failed to load resource: the server responded with a status of 403",
    "Error fetching Prometheus write target",
    "@grafana/faro-web-sdk",
    "faro-collector",
    "Access to fetch at 'https://faro-collector",
    "Failed to load resource: net::ERR_FAILED",
    "Failed to load resource: net::ERR_NAME_NOT_RESOLVED",
    "Intercom Messenger error",
)


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict, base_url: str) -> dict:
    return {
        **browser_context_args,
        "base_url": base_url,
        "viewport": {"width": 1440, "height": 900},
        "ignore_https_errors": True,
    }


@pytest.fixture
def console_errors(page: Page) -> Iterator[list[str]]:
    errors: list[str] = []

    def handler(msg: ConsoleMessage) -> None:
        if msg.type != "error":
            return
        text = msg.text
        if any(token in text for token in _CONSOLE_ERROR_WHITELIST):
            return
        errors.append(text)

    page.on("console", handler)
    yield errors


@pytest.fixture(scope="session", autouse=True)
def _configure_assertions() -> None:
    expect.set_options(timeout=15_000)


@pytest.fixture
def home_page(page: Page) -> HomePage:
    return HomePage(page)


@pytest.fixture
def checks_page(page: Page) -> ChecksPage:
    return ChecksPage(page)


# ---------------------------------------------------------------------------
# Reporting — attach Playwright artifacts to Allure on failure
# ---------------------------------------------------------------------------


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[None]) -> Generator[None, None, None]:
    outcome = yield
    report: pytest.TestReport = outcome.get_result()

    if report.when != "call" or report.passed:
        return

    page: Page | None = item.funcargs.get("page")  # type: ignore[assignment]
    if page is None or page.is_closed():
        return

    try:
        allure.attach(
            page.screenshot(full_page=True),
            name=f"failure_{item.name}.png",
            attachment_type=allure.attachment_type.PNG,
        )
    except Exception as exc:  # noqa: BLE001
        allure.attach(
            f"screenshot capture failed: {exc!r}",
            name="screenshot_error.txt",
            attachment_type=allure.attachment_type.TEXT,
        )

    try:
        allure.attach(
            page.content(),
            name=f"failure_{item.name}.html",
            attachment_type=allure.attachment_type.HTML,
        )
    except Exception as exc:  # noqa: BLE001
        allure.attach(
            f"HTML capture failed: {exc!r}",
            name="html_error.txt",
            attachment_type=allure.attachment_type.TEXT,
        )

    allure.attach(
        page.url,
        name="current_url.txt",
        attachment_type=allure.attachment_type.TEXT,
    )

    console_errs: list[str] | None = item.funcargs.get("console_errors")  # type: ignore[assignment]
    if console_errs:
        allure.attach(
            "\n".join(console_errs),
            name="console_errors_at_failure.txt",
            attachment_type=allure.attachment_type.TEXT,
        )
