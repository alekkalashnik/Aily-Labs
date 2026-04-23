"""Base class for all Page Objects — holds the Playwright page and
exposes the Grafana app-shell readiness signal.

Each POM action method is wrapped with `allure.step` so the Allure
report renders a readable tree of per-step expectations and actions
rather than a single opaque assertion.
"""

from __future__ import annotations

import re
from typing import ClassVar

import allure
from playwright.sync_api import Locator, Page, expect


class BasePage:
    URL: ClassVar[str] = ""  # Must be overridden by every concrete subclass.

    def __init__(self, page: Page) -> None:
        self._page = page

    def open(self) -> None:
        assert self.URL, f"{type(self).__name__} must define a non-empty URL."
        with allure.step(f"Open {self.URL}"):
            self._page.goto(self.URL, wait_until="domcontentloaded")
            self._wait_until_app_shell_ready()

    def _wait_until_app_shell_ready(self) -> None:
        expect(self._nav_toolbar).to_be_visible()

    @property
    def _nav_toolbar(self) -> Locator:
        return self._page.get_by_test_id("data-testid Nav toolbar")

    @property
    def _mega_menu(self) -> Locator:
        return self._page.get_by_test_id("data-testid navigation mega-menu")

    @property
    def _synthetics_breadcrumb(self) -> Locator:
        return self._page.get_by_test_id("data-testid Synthetics breadcrumb")

    @allure.step("Grafana app shell (mega-menu present, Synthetics breadcrumb visible)")
    def expect_app_shell_visible(self) -> None:
        # The nav toolbar is already verified by open(); this step checks the
        # remaining shell elements that open() does not wait for.
        expect(self._mega_menu).to_be_attached()
        expect(self._synthetics_breadcrumb).to_be_visible()

    @allure.step("Page title contains {title!r}")
    def expect_title_mentions(self, title: str) -> None:
        expect(self._page).to_have_title(re.compile(re.escape(title), re.IGNORECASE))

    @allure.step("No unexpected console errors were recorded")
    def expect_no_console_errors(self, errors: list[str]) -> None:
        if errors:
            allure.attach(
                "\n".join(errors),
                name="console_errors.txt",
                attachment_type=allure.attachment_type.TEXT,
            )
        assert errors == [], f"Unexpected console errors: {errors}"
